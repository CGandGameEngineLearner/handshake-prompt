# handshake-prompt (Python Server SDK)

> Core network component for the **Handshake Prompt Protocol (HPP)** —
> session pairing, token auth, HTTP + WebSocket transport.

## Architecture

```
┌─────────────────────────────────────────┐
│  Application (your service)           │
│  form-fill UI, device pairing, etc.     │
└──────────────────┬──────────────────────┘
                   │ hooks + mode handlers
┌──────────────────▼──────────────────────┐
│  handshake_prompt (this package)        │
│  ProtocolEngine · Session · SessionStore│
│  auth · Flask adapter (HandshakeManager)│
└──────────────────┬──────────────────────┘
                   │
         HTTP / WebSocket + X-Handshake-Token
```

**Core transport** (always included):
- Session creation with 128-bit sid + 192-bit token
- Token auth on all Agent endpoints
- Rate limiting, TTL, dynamic extension
- WebSocket real-time push

**Application plugins** (optional, in `handshake_prompt.modes`):
- `form-fill` — schema validation, field ownership, missing-field detection
- `default` — opaque key/value context for generic Agent interactions

Prompt text generation is **not** part of the core transport — use
`handshake_prompt.prompt.build_prompt()` if you want a default template.

## Install

```bash
pip install handshake-prompt
```

## Quick start (Flask)

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
hm   = HandshakeManager(app, sock)   # HPP endpoints mounted

if __name__ == '__main__':
    app.run(port=5000)
```

Endpoints (default prefix `/handshake`):

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/handshake/session`        | POST | Browser cookie (your app) | Create session |
| `/handshake/context/<sid>`  | GET  | X-Handshake-Token | Agent reads state |
| `/handshake/action/<sid>`   | POST | X-Handshake-Token | Agent submits actions |
| `/handshake/notify/<sid>`   | POST | Browser (optional) | User-side edits |
| `/handshake/diff/<sid>`     | GET  | X-Handshake-Token | Incremental changes |
| `/ws/handshake/<sid>`       | WS   | ?token= | Real-time push |

## Using without Flask

```python
from handshake_prompt import ProtocolEngine, SessionStore

store = SessionStore()
engine = ProtocolEngine(store=store, prefix='/api/pair')

payload, code = engine.create_session({'mode': 'device-pair', 'data': {}})
# Wire payload/code into your own framework adapter
```

## Form-fill mode (optional plugin)

```json
{
  "mode": "form-fill",
  "schema": [
    {"key": "name", "label": "Name", "type": "string", "required": true}
  ],
  "context": {}
}
```

## Custom mode handler

```python
from handshake_prompt.modes import DEFAULT_HANDLERS

class MyHandler:
    def setup_session(self, sess, body): ...
    def context_response(self, sess): ...
    def process_actions(self, sess, actions, stream, interval, cbs, broadcast): ...
    def process_notify(self, sess, key, value): ...
    def process_ws_message(self, sess, msg): ...

hm = HandshakeManager(app, sock, mode_handlers={
    **DEFAULT_HANDLERS,
    'my-mode': MyHandler(),
})
```

## Hooks

```python
@hm.on_create_session
def bind_owner(sess, request):
    sess.owner = flask_session.get('user_id')

@hm.on_action
def audit(sess, action, request):
    return True  # return False to veto

@hm.on_extend
def cap_extension(sess, extra_seconds, request):
    return min(extra_seconds, 1800)
```

## Security defaults

- Token: 192-bit entropy, timing-safe comparison
- Session ID: 128-bit entropy
- TTL: 30 min default, dynamically extendable
- Rate limit: 60 req/min/session
- WebSocket: token verified at connect time

See `SPEC.md` for full protocol details.

## License

MIT
