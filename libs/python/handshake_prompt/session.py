# encoding=utf-8
"""
Session — core network state for a single HPP handshake.

Transport concerns (sid, token, TTL, rate limit, WebSocket broadcast) live here.
Mode-specific data handling is delegated to mode handlers in modes/.
"""
import json
import re
import secrets
import time
from collections import deque
from datetime import datetime, timezone


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def _validate_type(value, ftype):
    """Default type validator used by form-fill mode."""
    if ftype in ('string', 'str'):
        return isinstance(value, str)
    if ftype in ('int', 'integer'):
        return isinstance(value, int) and not isinstance(value, bool)
    if ftype in ('float', 'number'):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if ftype in ('bool', 'boolean'):
        return isinstance(value, bool)
    if ftype == 'datetime':
        return isinstance(value, str) and bool(
            re.match(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}', value))
    if ftype.startswith('array'):
        return isinstance(value, list)
    return True


class Session:
    """
    A single handshake session.

    Core fields (all modes):
      sid, token, mode, meta, owner, ttl, changes, ws_clients

    Form-fill mode additionally uses:
      schema, values (with by/at provenance)
    """

    def __init__(self, sid, mode='default', schema=None, context=None,
                 ttl=1800, rate_limit_per_min=60,
                 owner=None, meta=None, validator=None):
        self.sid           = sid
        self.token         = secrets.token_urlsafe(24)
        self.mode          = mode
        self.schema        = schema or []
        self.owner         = owner
        self.meta          = dict(meta or {})
        self.ttl           = ttl
        self.created_at    = time.time()
        self.touched_at    = time.time()

        self._rate_limit = rate_limit_per_min
        self._rate_window = deque()
        self._validator = validator or _validate_type
        self._now_iso = _now_iso

        self.values = {}
        self.data = {}
        for key, val in (context or {}).items():
            by = 'user' if val not in (None, '', [], {}) else 'empty'
            self.values[key] = {'value': val, 'by': by, 'at': _now_iso()}
            self.data[key] = val

        self.changes = []
        self.ws_clients = set()

    # ── lifecycle ────────────────────────────────────────

    def touch(self):
        self.touched_at = time.time()

    def is_expired(self):
        return time.time() - self.touched_at > self.ttl

    def expires_in(self):
        return max(0, int(self.ttl - (time.time() - self.touched_at)))

    def extend(self, extra_seconds):
        self.ttl += extra_seconds
        self.touch()
        return self.expires_in()

    # ── rate limit ───────────────────────────────────────

    def check_rate_limit(self):
        now = time.time()
        while self._rate_window and self._rate_window[0] < now - 60:
            self._rate_window.popleft()
        if len(self._rate_window) >= self._rate_limit:
            return False
        self._rate_window.append(now)
        return True

    # ── form-fill helpers (used by FormFillHandler) ──────

    def set_value(self, key, value, source):
        current_by = self.values.get(key, {}).get('by', 'empty')
        if source == 'ai' and current_by in ('user', 'user_edit'):
            return False
        if source == 'user' and current_by == 'ai':
            source = 'user_edit'

        old = self.values.get(key, {}).get('value')
        now = _now_iso()
        self.values[key] = {'value': value, 'by': source, 'at': now}
        self.data[key] = value
        self.record_change(key, old, value, source)
        return True

    def validate_value(self, key, value):
        field_def = next((f for f in self.schema if f.get('key') == key), None)
        if not field_def:
            return True, None
        ftype = field_def.get('type', 'string')
        if not self._validator(value, ftype):
            return False, f'type mismatch, expected {ftype}'
        if ftype == 'enum':
            options = [o.get('value') for o in field_def.get('options', [])]
            if options and value not in options:
                return False, f'value not in allowed options {options}'
        return True, None

    def get_context(self):
        return {k: v.copy() for k, v in self.values.items()}

    def get_missing(self):
        return [
            f['key'] for f in self.schema
            if f.get('required')
            and self.values.get(f['key'], {}).get('value') in (None, '', [], {})
        ]

    def record_change(self, key, old, new, by):
        now = _now_iso()
        self.changes.append({'key': key, 'from': old, 'to': new, 'by': by, 'at': now})
        if len(self.changes) > 200:
            self.changes.pop(0)
        self.touch()

    def get_diff_since(self, since_iso):
        return [c for c in self.changes if c['at'] > since_iso]

    # ── WebSocket ────────────────────────────────────────

    def broadcast(self, msg):
        dead = set()
        payload = json.dumps(msg, ensure_ascii=False)
        sent = 0
        for ws in list(self.ws_clients):
            try:
                ws.send(payload)
                sent += 1
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead
        return sent

    # ── serialization ────────────────────────────────────

    def to_dict(self, include_token=False):
        out = {
            'sessionId': self.sid,
            'mode':      self.mode,
            'meta':      self.meta,
            'expiresIn': self.expires_in(),
        }
        if self.mode == 'form-fill':
            out.update({
                'schema':  self.schema,
                'context': self.get_context(),
                'missing': self.get_missing(),
            })
        else:
            out['data'] = dict(self.data)
        if include_token:
            out['token'] = self.token
        return out
