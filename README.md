# Handshake Prompt Protocol (HPP)

> **Zero configuration. One copy-paste. Your Agent operates any web service.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt-blue)](https://pypi.org/project/handshake-prompt/)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt--agent-blue)](https://pypi.org/project/handshake-prompt-agent/)
[![npm](https://img.shields.io/badge/npm-handshake--prompt--client-red)](https://www.npmjs.com/package/handshake-prompt-client)

---

## What is it?

**Handshake Prompt** is an open protocol that lets any AI Agent operate an existing web service on behalf of the user — with **zero setup required from the user**.

No API keys to generate. No tokens to configure. No MCP servers to install.

The user simply:

1. Opens the web service in their browser (already logged in)
2. Clicks **"AI Assistant"** and copies a **handshake prompt**
3. Pastes it to their Agent (Codemaker, Claude, Cursor, etc.)
4. Tells the Agent what they want done — in plain language
5. **Watches the Agent work in real time**, field by field, on the same page
6. Reviews and confirms before anything is saved

That's it. The entire authorization and session handoff happens inside the prompt text.

---

## Why it matters

### The problem with existing approaches

Connecting an AI Agent to a legacy web service today requires users to:

- **API Key**: generate a key, find the config file, paste it, restart the app — just to try once
- **OAuth**: click through a multi-step consent flow, manage refresh tokens, re-authorize after expiry
- **MCP Server**: install a binary, edit JSON config, manage a background daemon — per service, per Agent

This friction kills adoption. Most users never get through it.

### The Handshake Prompt solution

| | API Key | OAuth | MCP | **Handshake Prompt** |
|--|:-------:|:-----:|:---:|:--------------------:|
| User setup steps | 3–5 | 2–3 | 5–10 | **1** |
| Expires automatically | ❌ | ❌ | ❌ | **✅** |
| Scoped to single task | ❌ | ❌ | ❌ | **✅** |
| Works with any Agent | ✅ | ✅ | MCP-only | **✅** |
| User sees Agent work live | ❌ | ❌ | ❌ | **✅** |
| Backend integration cost | medium | heavy | heavy | **3 lines** |

---

## Use cases

Handshake Prompt is purpose-built for **AI-enabling legacy IT systems** that weren't designed with Agent access in mind.

### 📋 OA / Office Automation
> *"Submit this expense report for me. Dates from my calendar, amounts from the receipt photo."*

HR approval flows, leave requests, reimbursement forms — typically trapped in enterprise portals with no API. HPP adds Agent access without touching the core system.

### 🏦 Financial Systems
> *"Fill in the fund transfer form. Amount: last month's balance. Reference: invoice #2891."*

Trading platforms, internal accounting systems, fund allocation forms — Agent fills, human confirms, system saves. No AI ever touches the backend directly.

### 📊 ERP / CRM Data Entry
> *"Create a new customer record from this business card photo."*

Data entry at scale. The Agent reads unstructured input and maps it to structured form fields. User reviews each field before saving. Audit trail intact.

### 🏥 Medical / Legal Records
> *"Pre-fill the patient intake form from the referral letter."*

High-stakes workflows where a human must always confirm. HPP enforces this: the Agent fills, the user clicks Save.

### ⚙️ Any Form-Heavy Internal Tool

Configuration panels, provisioning wizards, batch data uploads — if it has fields, HPP can help an Agent fill them.

---

## How a handshake prompt looks

When the user clicks "AI Assistant", the service generates and copies this to their clipboard:

```
# Handshake Prompt — Expense Report

## Credentials
- sessionId: 4f2a8c1e...
- token: AbC9Xm2R...      ← single-use, expires in 30 min
- baseUrl: https://oa.company.com
- mode: form-fill

## Current state
(service injects current form data here automatically)

## Instructions
1. GET  https://oa.company.com/handshake/context/4f2a8c1e  (X-Handshake-Token: <token>)
2. POST https://oa.company.com/handshake/action/4f2a8c1e   {"actions":[...]}

## Waiting for your instructions...
```

The Agent parses the credentials, fetches the form schema, reasons about the fields, and submits values — which appear live in the user's browser.

---

## Security by design

- **Token expires in 30 minutes** — leaked prompts become useless quickly
- **192-bit token entropy** — brute force is computationally infeasible
- **User data is protected** — the server refuses any AI attempt to overwrite fields the user has already filled manually
- **Rate limited** — 60 requests/min/session prevents abuse
- **User must confirm** — nothing is saved without the user clicking submit

See [docs/threat-model.md](docs/threat-model.md) for the full analysis.

---

## Get started in 3 lines (Flask)

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
HandshakeManager(app, sock)   # ← HPP is live
```

Your service now exposes:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/handshake/session`       | POST | Browser creates a session, gets token |
| `/handshake/context/<sid>` | GET  | Agent reads schema + current values |
| `/handshake/action/<sid>`  | POST | Agent submits field values (validated, rate-limited) |
| `/handshake/notify/<sid>`  | POST | Browser reports user manual edits |
| `/ws/handshake/<sid>`      | WS   | Browser receives real-time push from Agent |

### Browser (any framework)

```ts
import { HandshakeClient } from 'handshake-prompt-client'

const hpp = new HandshakeClient()
await hpp.createSession({ mode: 'form-fill', schema: FIELDS, context: getFormData() })
hpp.on('action', ({ key, value }) => applyToForm(key, value))   // real-time fill
hpp.connect()
await hpp.copyPrompt()   // user pastes this to their Agent
```

### Agent (CLI or programmatic)

```bash
pip install handshake-prompt-agent

# Parse the prompt the user pasted
handshake-prompt-agent parse-prompt --prompt "$(pbpaste)"

# Read current schema + values (do this before EVERY action)
handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>

# Fill fields — they appear live in the user's browser
handshake-prompt-agent action --sid <sid> --token <token> --base <url> \
    --data '{"name":"Alice","department":"Engineering","startDate":"2026-07-01"}'
```

---

## Install

```bash
# Server-side (Python / Flask)
pip install handshake-prompt

# Browser-side (TypeScript / JavaScript)
npm install handshake-prompt-client

# Agent-side (CLI + Python API, zero external dependencies)
pip install handshake-prompt-agent
```

---

## What's in this repo

```
handshake-prompt/
├── SPEC.md                      ← Protocol specification
├── docs/
│   ├── comparison.md            ← vs OAuth / API Key / MCP
│   └── threat-model.md          ← Security analysis
├── libs/
│   ├── python/                  ← handshake-prompt      (Flask server SDK)
│   ├── js/                      ← handshake-prompt-client (browser, TypeScript)
│   └── agent-python/            ← handshake-prompt-agent  (Agent CLI + SDK)
└── examples/
    ├── server-flask/            ← Minimal end-to-end demo
    ├── oa-expense-report/       ← OA expense form walkthrough
    └── skill/                   ← Reference Agent skill files
```

---

## Run the demo

```bash
git clone https://github.com/CGandGameEngineLearner/handshake-prompt
cd handshake-prompt/examples/server-flask
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

Click "🤖 AI Assistant", paste the prompt to your Agent, tell it what to fill.

---

## Roadmap

- [x] v0.1 — Flask server SDK, TypeScript browser SDK, Python Agent SDK + CLI
- [ ] FastAPI server adapter
- [ ] Express.js server adapter
- [ ] React / Vue component packages
- [ ] Conformance test suite
- [ ] Production deployment guide (nginx, HTTPS, multi-instance with Redis)

---

## License

MIT — free for commercial use.
