# handshake-prompt (Python Server SDK)

> Server-side SDK for the **Handshake Prompt Protocol (HPP)** — a lightweight
> way to grant any AI Agent access to your web service via a single
> copy-paste prompt. No API keys, no MCP servers, no env vars for end users.

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
hm   = HandshakeManager(app, sock)   # done! HPP endpoints are now mounted.

if __name__ == '__main__':
    app.run(port=5000)
```

That's it. Your service now exposes:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/handshake/session`        | POST | Browser creates a handshake session |
| `/handshake/context/<sid>`  | GET  | Agent reads current state (token-auth) |
| `/handshake/action/<sid>`   | POST | Agent submits actions (token-auth) |
| `/handshake/notify/<sid>`   | POST | Browser reports user edits |
| `/handshake/diff/<sid>`     | GET  | Agent fetches incremental changes |
| `/ws/handshake/<sid>`       | WS   | Real-time push channel (token-auth) |

## Build a handshake prompt

```python
prompt_text = hm.build_prompt(session, base_url='https://your-service.com')
# Display this text in the UI, let user copy-paste it to their Agent.
```

## Configure schema

Schemas describe what fields the Agent should fill. Sent by the browser
when creating a session:

```json
{
  "mode": "form-fill",
  "schema": [
    {"key": "name",  "label": "Name",  "type": "string", "required": true, "example": "Alice"},
    {"key": "age",   "label": "Age",   "type": "int",    "example": 30},
    {"key": "vip",   "label": "VIP",   "type": "bool"}
  ],
  "context": {}    // current state, used by browser to pre-populate
}
```

Supported types: `string` / `int` / `float` / `bool` / `datetime` /
`array<string>` / `enum`. Custom validators can be plugged in via
`HandshakeManager(validator=...)`.

## Hooks

Attach custom logic at key lifecycle points:

```python
@hm.on_create_session
def bind_owner(sess, request):
    """Bind a session to the current logged-in user"""
    from flask import session as flask_session
    sess.owner = flask_session.get('user_id')

@hm.on_action
def audit(sess, action, request):
    """Audit every action; return False to veto"""
    print(f'[AUDIT] sid={sess.sid} user={sess.owner} action={action}')

@hm.on_done
def notify_done(sess, applied, rejected, errors):
    """Called after each batch of actions"""
    pass
```

## Browser auth for `/notify`

By default `/notify/<sid>` accepts any request (it's only used by
browsers within the same origin). For stricter setups, supply a callable:

```python
def my_auth(request, sess):
    return flask_session.get('user_id') == sess.owner

hm = HandshakeManager(app, sock, require_browser_auth=my_auth)
```

## Security defaults

- **Token entropy**: 192 bits (`secrets.token_urlsafe(24)`)
- **Session ID entropy**: 128 bits (`secrets.token_hex(16)`)
- **Timing-safe comparison**: `secrets.compare_digest`
- **TTL**: 30 minutes default
- **Rate limit**: 60 requests / minute / session
- **User-data protection**: AI **cannot** overwrite fields marked
  `by=user` or `by=user_edit`
- **WebSocket auth**: connection-time token verification

See `SPEC.md` of the main repository for full protocol details.

## License

MIT
