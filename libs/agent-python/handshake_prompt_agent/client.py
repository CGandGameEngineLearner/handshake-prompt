# encoding=utf-8
"""
HandshakeAgent - Agent-side HTTP client for HPP.

No external dependencies - uses Python stdlib urllib only.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request


class HPPError(Exception):
    def __init__(self, msg, code=None, body=None):
        super().__init__(msg)
        self.code = code
        self.body = body


class HandshakeAgent:
    """
    Agent-side client for a single handshake session.

    >>> agent = HandshakeAgent(sid="...", token="...", base_url="http://localhost:5000")
    >>> ctx = agent.get_context()
    >>> agent.action({"name": "Alice"})
    """

    def __init__(self, sid, token, base_url, prefix='/handshake', timeout=15):
        self.sid     = sid
        self.token   = token
        self.base    = base_url.rstrip('/')
        self.prefix  = prefix.rstrip('/')
        self.timeout = timeout

    # ── HTTP helpers ───────────────────────────────────────

    def _headers(self):
        return {
            'Content-Type': 'application/json; charset=utf-8',
            'X-Handshake-Token': self.token,
        }

    def _get(self, path):
        url = f'{self.base}{path}'
        req = urllib.request.Request(url, headers=self._headers(), method='GET')
        return self._do(req)

    def _post(self, path, body):
        url = f'{self.base}{path}'
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=self._headers(), method='POST')
        return self._do(req)

    def _do(self, req):
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                text = r.read().decode('utf-8')
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')
            try:
                payload = json.loads(body)
            except Exception:
                payload = {'error': body}
            raise HPPError(payload.get('error', f'HTTP {e.code}'),
                           code=e.code, body=payload)
        except urllib.error.URLError as e:
            raise HPPError(f'connection error: {e.reason}')

    # ── HPP operations ─────────────────────────────────────

    def get_context(self):
        """
        Fetch schema + current values.

        Returns a dict with keys: sessionId, mode, schema, context, missing, expiresIn.
        """
        return self._get(f'{self.prefix}/context/{self.sid}')

    def get_diff(self, since=''):
        """
        Fetch changes since a given ISO timestamp.
        If since is empty, returns the last 50 changes.
        """
        path = f'{self.prefix}/diff/{self.sid}'
        if since:
            path += f'?since={urllib.parse.quote(since)}'
        return self._get(path)

    def action(self, values, stream=True, interval_ms=300):
        """
        Submit field values.

        Args:
            values:      dict {key: value, ...}
            stream:      if True, server pushes each field to browser with animation
            interval_ms: delay between pushes when stream=True

        Returns the response dict with: ok, applied, rejected, errors, missing, context.

        Note: AI cannot overwrite fields previously written by the user.
              Such fields appear in `rejected`.
        """
        actions = [{'type': 'set', 'key': k, 'value': v} for k, v in values.items()]
        return self._post(f'{self.prefix}/action/{self.sid}', {
            'actions':    actions,
            'stream':     stream,
            'intervalMs': interval_ms,
        })


# ── Prompt parser ────────────────────────────────────────────

_PROMPT_KEYS = ('sessionId', 'token', 'baseUrl')


def parse_prompt(prompt_text):
    """
    Parse a handshake prompt and extract credentials.

    Returns a dict {sessionId, token, baseUrl, ...}, or raises ValueError
    if required fields are missing.
    """
    result = {}
    # Match lines like "- key: value" or "key: value"
    for line in prompt_text.splitlines():
        m = re.match(r'^\s*-?\s*(\w+)\s*:\s*(.+?)\s*$', line)
        if m:
            key, val = m.group(1), m.group(2)
            # Only take the first non-empty occurrence
            if key in _PROMPT_KEYS and key not in result:
                result[key] = val
            elif key in ('mode', 'expiresIn', 'skill') and key not in result:
                result[key] = val

    missing = [k for k in _PROMPT_KEYS if k not in result]
    if missing:
        raise ValueError(f'missing fields in prompt: {missing}')

    return result
