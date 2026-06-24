# encoding=utf-8
"""
Session 对象 - 一个握手会话的完整状态
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
    """简易类型校验，可被 HandshakeManager(validator=...) 覆盖"""
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
    单个握手会话。

    存储：
      - sid / token       会话标识 + 一次性访问令牌
      - schema            字段定义 list[dict]
      - values            当前值 {key: {value, by, at}}
      - changes           变更历史 (最近 200)
      - ws_clients        订阅的 WebSocket 集合

    by 字段含义：
      - 'empty'      未填
      - 'user'       用户主动填写
      - 'ai'         Agent 填写
      - 'user_edit'  AI 填后被用户修改

    安全：
      - AI 不能覆盖 by=user 或 by=user_edit 的字段（在 set_value 中强制）
    """

    def __init__(self, sid, mode='default', schema=None, context=None,
                 ttl=1800, rate_limit_per_min=60,
                 owner=None, meta=None, validator=None):
        self.sid           = sid
        self.token         = secrets.token_urlsafe(24)     # 192 bit
        self.mode          = mode
        self.schema        = schema or []
        self.owner         = owner       # 任意类型，用于绑定创建者身份
        self.meta          = dict(meta or {})    # 任意业务元数据
        self.ttl           = ttl
        self.created_at    = time.time()
        self.touched_at    = time.time()

        self._rate_limit = rate_limit_per_min
        self._rate_window = deque()
        self._validator = validator or _validate_type

        # 字段值
        self.values = {}
        for key, val in (context or {}).items():
            by = 'user' if val not in (None, '', [], {}) else 'empty'
            self.values[key] = {'value': val, 'by': by, 'at': _now_iso()}

        # 变更历史
        self.changes = []

        # 订阅广播的 WebSocket
        self.ws_clients = set()

    # ── 生命周期 ─────────────────────────────────────────

    def touch(self):
        self.touched_at = time.time()

    def is_expired(self):
        return time.time() - self.touched_at > self.ttl

    def expires_in(self):
        return max(0, int(self.ttl - (time.time() - self.touched_at)))

    # ── 频率限制 ─────────────────────────────────────────

    def check_rate_limit(self):
        now = time.time()
        while self._rate_window and self._rate_window[0] < now - 60:
            self._rate_window.popleft()
        if len(self._rate_window) >= self._rate_limit:
            return False
        self._rate_window.append(now)
        return True

    # ── 数据 ────────────────────────────────────────────

    def set_value(self, key, value, source):
        """
        设置字段。source ∈ {'ai', 'user'}

        AI 试图覆盖 by=user / user_edit 时返回 False（不修改）。
        用户修改 AI 填的字段时，by 自动升级为 user_edit。
        """
        current_by = self.values.get(key, {}).get('by', 'empty')

        if source == 'ai' and current_by in ('user', 'user_edit'):
            return False

        if source == 'user' and current_by == 'ai':
            source = 'user_edit'

        old = self.values.get(key, {}).get('value')
        now = _now_iso()
        self.values[key] = {'value': value, 'by': source, 'at': now}
        self.changes.append({
            'key': key, 'from': old, 'to': value, 'by': source, 'at': now,
        })
        if len(self.changes) > 200:
            self.changes.pop(0)
        self.touch()
        return True

    def validate_value(self, key, value):
        """根据 schema 校验单个字段值，返回 (ok, msg)"""
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
        """完整上下文快照"""
        return {k: v.copy() for k, v in self.values.items()}

    def get_diff_since(self, since_iso):
        return [c for c in self.changes if c['at'] > since_iso]

    def get_missing(self):
        """必填且未填的字段 key 列表"""
        return [
            f['key'] for f in self.schema
            if f.get('required')
            and self.values.get(f['key'], {}).get('value') in (None, '', [], {})
        ]

    # ── WebSocket 广播 ──────────────────────────────────

    def broadcast(self, msg):
        dead = set()
        payload = json.dumps(msg, ensure_ascii=False)
        for ws in list(self.ws_clients):
            try:
                ws.send(payload)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead

    # ── 序列化 ──────────────────────────────────────────

    def to_dict(self, include_token=False):
        out = {
            'sessionId':  self.sid,
            'mode':       self.mode,
            'schema':     self.schema,
            'context':    self.get_context(),
            'missing':    self.get_missing(),
            'meta':       self.meta,
            'expiresIn':  self.expires_in(),
        }
        if include_token:
            out['token'] = self.token
        return out
