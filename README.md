# Handshake Prompt Protocol

> **One copy-paste. AI Agent gets access to your web service. No API key. No MCP. No setup.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt-blue)](https://pypi.org/project/handshake-prompt/)
[![npm](https://img.shields.io/badge/npm-@handshake--prompt/client-red)](https://www.npmjs.com/package/@handshake-prompt/client)

---

## TL;DR

```
┌──────────┐   ① Click button     ┌────────────┐
│   User   │ ────────────────────→│  Your Web  │
│ Browser  │   ② Copy prompt      │  Service   │
│          │ ←────────────────────│            │
└──────────┘                      └────────────┘
      │                                  ↑
      │ ③ Paste prompt to Agent          │
      ↓                                  │ ④ Agent uses
┌──────────┐                              │   credentials
│  Agent   │ ─────────────────────────────┘   embedded in prompt
└──────────┘
```

**The user does nothing technical.** Just clicks a button, pastes a prompt to their Agent, and tells it what to do.

---

## Why this exists

Modern web services want to let users delegate work to AI Agents, but every existing mechanism has friction:

| Approach | User Setup |
|----------|-----------|
| API Key  | Generate key, store securely, paste into Agent config |
| OAuth    | Click through 3-page consent flow, manage refresh tokens |
| MCP      | Install MCP server, configure transport, restart Agent |
| **Handshake Prompt** | **Copy & paste once** |

Handshake Prompt is for the **last mile** — a 30-minute, single-purpose grant that lets any Agent do one job on a user's behalf, then expires.

---

## Try the demo (30 seconds)

```bash
git clone https://github.com/CGandGameEngineLearner/handshake-prompt
cd handshake-prompt/examples/server-flask
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>, click "🤖 AI Fill", paste the prompt to your AI Agent, and tell it what to do.

---

## Install the SDKs

| Package | Role | Install |
|---------|------|---------|
| [`handshake-prompt`](libs/python)              | Server (Python / Flask) | `pip install handshake-prompt` |
| [`@handshake-prompt/client`](libs/js)          | Browser (any framework) | `npm i @handshake-prompt/client` |
| [`handshake-prompt-agent`](libs/agent-python)  | Agent-side client/CLI   | `pip install handshake-prompt-agent` |

### Server (Python, 3 lines)

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
HandshakeManager(app, sock)   # done.
```

### Browser (JS)

```ts
import { HandshakeClient } from '@handshake-prompt/client'

const hpp = new HandshakeClient()
await hpp.createSession({ mode: 'form-fill', schema: [...], context: {...} })
hpp.on('action', ({ key, value }) => fillField(key, value))
hpp.connect()
await hpp.copyPrompt()
```

### Agent (Python or CLI)

```bash
pip install handshake-prompt-agent

# Inside the Agent's skill:
handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>
handshake-prompt-agent action --sid <sid> --token <token> --base <url> \
    --data '{"name":"Alice"}'
```

---

## What's in this repo

```
handshake-prompt/
├── SPEC.md                     ← Protocol specification
├── docs/
│   ├── comparison.md           ← vs OAuth / API Key / MCP
│   └── threat-model.md         ← Security analysis
├── libs/
│   ├── python/                 ← handshake-prompt (server SDK)
│   ├── js/                     ← @handshake-prompt/client (browser SDK)
│   └── agent-python/           ← handshake-prompt-agent (Agent SDK)
└── examples/
    ├── server-flask/           ← Minimal end-to-end demo
    ├── client-vue/             ← Vue component example
    └── skill/                  ← Reference Agent skill files
```

---

## How it works (60-second tour)

### 1. Browser asks the server to start a session

```http
POST /handshake/session
{ "mode": "form-fill", "schema": [...], "context": {...} }
```

Server replies with `sessionId` + a **single-use `token`** (192-bit random,
30-minute TTL).

### 2. Browser builds and copies a handshake prompt

```
# Handshake Prompt - form-fill

## Credentials
- sessionId: 4f2a8c...
- token: AbC9X...               ← embedded credential
- baseUrl: https://my.app

## Usage
1. GET  https://my.app/handshake/context/4f2a8c   (header X-Handshake-Token)
2. POST https://my.app/handshake/action/4f2a8c    {"actions":[...]}

## Waiting for user's request...
```

User pastes this text into their AI Agent.

### 3. Agent uses credentials to call the server

- `GET  /handshake/context/<sid>` — fetch schema + current values
- `POST /handshake/action/<sid>`  — submit field values

Server validates the token (`hmac.compare_digest`) and rate-limits per session.

### 4. Server pushes actions to browser via WebSocket

The browser sees fields fill in real time. The user can edit any field
manually — and the server **refuses** any AI attempt to overwrite
user-written fields (`by=user` / `by=user_edit`).

---

## Comparison to existing approaches

See [docs/comparison.md](docs/comparison.md) for the full table. Highlights:

|                          | API Key | OAuth 2.0 | MCP | Handshake Prompt |
|--------------------------|:-------:|:---------:|:---:|:---:|
| User configures anything | ✅       | partial    | ✅   | **❌ Never** |
| Scoped to one task       | ❌       | ❌         | ❌   | **✅** |
| Auto-expires             | ❌       | ❌         | ❌   | **✅** |
| Works with any Agent     | ✅       | ✅         | only MCP-aware | **✅** |
| Real-time UX (user sees AI work) | ❌ | ❌    | ❌   | **✅** |
| Backend integration cost | medium  | high      | high | **3 lines** |

---

## Security

See [docs/threat-model.md](docs/threat-model.md). Defaults:

- **128-bit** session IDs, **192-bit** tokens, both `secrets`-generated
- Timing-safe token comparison (`secrets.compare_digest`)
- 30-minute TTL, configurable
- 60 req/min/session rate limit
- AI **cannot** overwrite fields previously written by the user
- WebSocket connections are token-authenticated at upgrade time

---

## Status

- [x] v0.1 spec frozen
- [x] Reference SDKs: Python server, JS browser, Python Agent + CLI
- [ ] Node.js server SDK
- [ ] Vue/React component packages
- [ ] Production deployment guide
- [ ] Conformance test suite

---

## License

MIT
