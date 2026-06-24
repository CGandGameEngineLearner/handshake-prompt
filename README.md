# Handshake Prompt Protocol (HPP) · 握手提示词协议

> **Zero configuration. One copy-paste. Session established.**
>
> **零配置。一次复制粘贴。建立鉴权会话。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt-blue)](https://pypi.org/project/handshake-prompt/)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt--agent-blue)](https://pypi.org/project/handshake-prompt-agent/)
[![npm](https://img.shields.io/badge/npm-handshake--prompt--client-red)](https://www.npmjs.com/package/handshake-prompt-client)

---

## What is it?

**Handshake Prompt** is a **lightweight auth & pairing protocol** for the Agent era.

It generates a single-use credential embedded in a plain-text prompt, letting any
AI Agent establish a temporary (or long-term) session with a web service, a
smart device, or another Agent — with zero user-side configuration.

No API keys to generate. No tokens to configure. No MCP servers to install.

---

## 这是什么？

**握手提示词** 是一个为 Agent 时代设计的**轻量鉴权与配对协议**。

它生成一个内嵌在纯文本中的一次性凭证，让任何 AI Agent 与 Web 服务、智能设备
或其他 Agent 建立临时或长期的会话 —— **用户无需做任何配置**。

不需要生成 API Key，不需要配置 Token，不需要安装 MCP Server。

---

## Core capability · 核心能力

```
一段握手提示词 = 一段文本内嵌的会话凭证（sessionId + token）
                ↓
        任何人拿到它，在有效期/次数内可以用它调用对应的受限接口
                ↓
        服务端验证 token、控制边界、记录审计
```

HPP 只做一件事：**建立安全、有时效、有边界的一次性会话**。  
会话内具体做什么，由接入方自行定义。

---

## Why it matters · 为什么重要

| | API Key | OAuth | MCP | **Handshake Prompt** |
|--|:-------:|:-----:|:---:|:--------------------:|
| User setup steps · 用户配置步骤 | 3–5 | 2–3 | 5–10 | **1** |
| Permission config required · 需要配置权限 | ✅ complex | ✅ complex | ✅ complex | **❌** |
| Scoped to single grant · 单次授权 | ❌ | ❌ | ❌ | **✅** |
| Expires automatically · 自动过期 | ❌ | ❌ | ❌ | **✅** |
| Works with any Agent · 适配任意 Agent | ✅ | ✅ | MCP-only | **✅** |
| Short or long pairing · 短期或长期配对 | ❌ | ✅ | ✅ | **✅** |
| Backend integration · 后端接入 | medium | heavy | heavy | **3 lines** |

---

## Two pairing modes · 两种配对模式

| | Short-term · 短期 | Long-term · 长期 |
|--|--------------------|------------------|
| TTL | 30 min default, configurable | Token rotated server-side |
| Use case | One form fill, one device command | Agent ⇄ service, Agent ⇄ Agent |
| Token lifecycle | Single session, expires | Renewable, revocable |
| Persistent state | None | Session persisted, auditable |

> Both modes start from the same handshake flow. Whether a session becomes
> long-lived is up to the **server policy**, not the protocol.

---

## Protocol endpoints · 协议接口

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/handshake/session`           | POST | Create session, return sessionId + token |
| `/handshake/context/<sid>`     | GET  | Agent reads current session state (token-auth) |
| `/handshake/action/<sid>`      | POST | Agent performs an action (token-auth, rate-limited) |
| `/handshake/session/<sid>/extend` | POST | Extend TTL (server may accept/reject/cap) |
| `/handshake/notify/<sid>`      | POST | Browser-side reports user interaction |
| `/handshake/diff/<sid>`        | GET  | Agent fetches incremental changes |
| `/ws/handshake/<sid>`          | WS   | Real-time push to browser (token-auth at upgrade) |

---

## Applications built on HPP

Since HPP only handles **auth & pairing**, the application layer is up to you:

- **Form filling** — autofill, OA expense reports, ERP data entry
- **Device pairing** — QR code → Agent ↔ robot / appliance / car
- **Agent-to-Agent** — temporary credential exchange between Agents
- **Login / SSO** — handshake prompt as a passwordless login flow
- **Smart hardware** — NFC / Bluetooth broadcast containing handshake credentials

---

## Get started in 3 lines (Flask)

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
hm   = HandshakeManager(app, sock)   # HPP endpoints mounted
```

### Browser (any framework)

```ts
import { HandshakeClient } from 'handshake-prompt-client'

const hpp = new HandshakeClient()
await hpp.createSession()   // returns { sessionId, token, wsUrl }
hpp.on('action', ({ key, value }) => { /* your logic */ })
hpp.connect()               // WebSocket
await hpp.copyPrompt()      // user pastes to Agent
```

### Agent (CLI or API)

```bash
pip install handshake-prompt-agent

handshake-prompt-agent parse-prompt --prompt "..."
handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>
handshake-prompt-agent action      --sid <sid> --token <token> --base <url> --data '{...}'
handshake-prompt-agent extend      --sid <sid> --token <token> --base <url> --extra-seconds 1800
```

---

## Install · 安装

```bash
pip install handshake-prompt           # server SDK (Flask)
npm install handshake-prompt-client    # browser SDK
pip install handshake-prompt-agent     # Agent SDK (zero-dep, stdlib only)
```

---

## Spec & docs · 协议与文档

| File | Description |
|------|-------------|
| [SPEC.md](SPEC.md) | Protocol specification |
| [docs/threat-model.md](docs/threat-model.md) | Security analysis |
| [docs/comparison.md](docs/comparison.md) | vs API Key / OAuth / MCP |
| [libs/python/](libs/python/) | Server SDK |
| [libs/js/](libs/js/) | Browser SDK |
| [libs/agent-python/](libs/agent-python/) | Agent SDK |
| [examples/server-flask/](examples/server-flask/) | Minimal demo |

---

## License · 开源协议

MIT — free for commercial use · 免费商用
