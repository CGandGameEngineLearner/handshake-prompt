# Handshake Prompt Protocol (HPP) · 握手提示词协议

> **Zero configuration. One copy-paste. Your Agent operates any web service.**
>
> **零配置。一次复制粘贴。让 AI Agent 直接操作你的 Web 服务。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt-blue)](https://pypi.org/project/handshake-prompt/)
[![PyPI](https://img.shields.io/badge/PyPI-handshake--prompt--agent-blue)](https://pypi.org/project/handshake-prompt-agent/)
[![npm](https://img.shields.io/badge/npm-handshake--prompt--client-red)](https://www.npmjs.com/package/handshake-prompt-client)

[English](#what-is-it) · [中文](#这是什么)

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

## 这是什么？

**握手提示词（Handshake Prompt）** 是一个开放协议，让任何 AI Agent 代替用户操作现有 Web 服务——**用户无需做任何配置**。

不需要生成 API Key，不需要配置 Token，不需要安装 MCP Server。

用户只需：

1. 在浏览器中打开目标 Web 服务（已登录）
2. 点击页面上的 **「AI 助手」** 按钮，复制一段**握手提示词**
3. 将其粘贴给自己的 Agent（Codemaker、Claude、Cursor、OpenClaw、Workbody 等均可）
4. 用自然语言告诉 Agent 要做什么
5. **实时看到 Agent 逐字段填写**到当前页面
6. 检查、二次修改，确认后提交

整个授权和会话移交的过程都发生在这段提示词文本里。

---

## Why it matters · 为什么重要

### The problem · 现有方案的痛点

Connecting an AI Agent to a legacy web service today requires users to:  
把 AI Agent 接入一个现有 Web 服务，目前的用户需要：

- **API Key**：generate a key, find the config, paste, restart · 生成密钥、找配置文件、粘贴、重启
- **OAuth**：click through consent flows, manage refresh tokens · 走授权流程、管理刷新令牌
- **MCP Server**：install a binary, edit JSON config, manage a daemon — per service · 安装后台服务、编辑配置、每个系统都来一次

And beyond setup friction, there's a deeper problem: **permission ambiguity**.  
除了配置繁琐，还有一个更深层的问题：**权限边界模糊**。

API Keys and Access Tokens require the user to manually define what the Agent *can* and *cannot* do —
a complex permission matrix that most users don't understand, often set too broadly "just to make it work."  
API Key 和 Access Token 需要用户手动配置这个凭证能做什么、不能做什么——
这是一套复杂的权限矩阵，大多数用户并不理解，往往为了"让它能用"而授予过宽的权限。

The result: **accountability is blurry**. A leaked key can be exploited indefinitely across many services.  
结果就是：**权责不清晰**。一个泄露的 Key 可以被无限期用于多个服务。

**This friction kills adoption. Most users never get through it.**  
**这些门槛直接劝退了大多数用户。**

### The solution · 握手提示词的解法

Handshake Prompt takes a fundamentally different approach, inspired by QR-code login:  
握手提示词采用了完全不同的思路，灵感来自二维码登录：

> **一段握手提示词 = 一个服务 + 一次授权 + 用完即失效**
>
> **One handshake prompt = One service + One authorization + Expires when done**

- **No permission configuration needed** — the prompt itself *is* the scope. It grants access to exactly one service operation, nothing more.  
  **无需配置权限** — 提示词本身就是授权范围。它精确对应一个服务操作，仅此而已。

- **Like a QR code, not a password** — you don't configure what a QR code "can do"; it does one thing and expires.  
  **像二维码，不像密码** — 你不需要配置二维码"能做什么"，它做一件事然后失效。

- **Agent's fence is fixed** — the Agent operates only within the session created by the user's click. It cannot drift to other services, other users, or other operations.  
  **Agent 的围栏是固定的** — Agent 只能在用户点击创建的这个会话范围内操作，无法越界到其他服务、其他用户或其他操作。

- **User confirms before anything saves** — the Agent fills, the user reviews, the user submits. The human is always the last gate.  
  **用户确认才保存** — Agent 填写，用户审查，用户提交。人始终是最后一道关卡。

| | API Key | OAuth | MCP | **Handshake Prompt · 握手提示词** |
|--|:-------:|:-----:|:---:|:--------------------:|
| 用户配置步骤 User setup steps | 3–5 | 2–3 | 5–10 | **1** |
| 需要配置权限范围 Requires permission config | ✅ 复杂 | ✅ 复杂 | ✅ 复杂 | **❌ 不需要** |
| 精确对应单一任务 Scoped to single task | ❌ | ❌ | ❌ | **✅** |
| 自动过期 Expires automatically | ❌ | ❌ | ❌ | **✅** |
| 适配任意 Agent Works with any Agent | ✅ | ✅ | MCP-only | **✅** |
| 用户实时看到 Agent 操作 User sees Agent work live | ❌ | ❌ | ❌ | **✅** |
| 后端接入成本 Backend integration cost | medium | heavy | heavy | **3 lines · 3行代码** |

---

## Use cases · 典型场景

Handshake Prompt is purpose-built for **AI-enabling legacy IT systems** that weren't designed with Agent access in mind.  
握手提示词专为**现有 IT 系统的 AI 化改造**而设计。

### 📋 复杂企业表单 · Complex Enterprise Forms

> *"我需要的信息分散在一张 Excel 表、一段聊天记录和我自己的记忆里，你能帮我填好吗？"*
>
> *"The information I need is scattered across an Excel sheet, a chat log, and my own memory. Can you just fill it in for me?"*

企业 Web 系统中存在大量复杂表单，用户需要手动从多个来源抄录数据——Excel 表格、邮件、会议记录、历史提交。这不仅耗时，还容易出错。

**有了握手提示词之后：**

```
1. 用户在浏览器中打开表单（已完成身份认证）
2. 点击「🤖 AI 助手」→ 复制握手提示词
3. 粘贴给自己的 Agent：
      Codemaker · OpenClaw · Workbody · Claude · Cursor · 任意 LLM
4. 用自然语言告诉 Agent：
      "从附件的 Excel 第5行填写"
      "用我昨天和供应商的聊天记录里的收货地址"
      "和上个月的报告一样，只改日期和金额"
5. 实时看到每个字段被逐一填入，带高亮动画
6. 检查内容，修改两个字段，点击提交
```

**Agent 不接触后端。它只写入用户当前正在看的表单，用户确认前不会保存任何内容。**

---

**用户告诉 Agent 的典型指令：**

| 数据来源 | 用户说什么 | Agent 做什么 |
|---------|-----------|-------------|
| Excel 文件 | *"从附件采购表第5行填"* | 读取 Excel，列名映射到表单字段 |
| 聊天记录 | *"用我昨天和供应商聊天里的收货地址"* | 从非结构化文本中提取结构化数据 |
| 历史习惯 | *"和上个月一样，改一下日期和金额"* | 拉取历史状态，只更新变化的字段 |
| 照片/扫描件 | *"这是收据照片，帮我填报销单"* | OCR 识别 + 字段映射 |
| 语音备忘 | *"我录了会议纪要，帮填项目总结表"* | 语音转写 + 信息提取 |
| 混合来源 | *"物品从 Excel，供应商信息从聊天记录，其余参考上月"* | 多源聚合 |

### 📋 OA 办公自动化 · Office Automation
> *"帮我提交这份报销单，日期从日历里取，金额从收据照片里读。"*

请假申请、报销审批、采购申请——这些表单通常困在企业门户里没有任何 API 接口。HPP 无需改造核心系统，一行代码接入。

### 🏦 金融系统 · Financial Systems
> *"帮我填转账申请表，金额是上月余额，备注是发票 #2891。"*

交易平台、内部财务系统、资金划拨表——Agent 填写，人工确认，系统保存。AI 永远不直接接触后端。

### 📊 ERP / CRM 数据录入
> *"从这张名片照片创建一条新客户记录。"*

大批量数据录入。Agent 读取非结构化输入并映射到结构化表单字段，用户确认后保存，审计留痕完整。

### 🏥 医疗 / 法律档案
> *"从转诊信里预填患者入院表格。"*

高风险业务流程，必须由人工确认。HPP 在协议层强制执行这一点：Agent 填写，用户点保存。

### ⚙️ 任何字段密集的内部工具

配置面板、资源配置向导、批量数据上传——只要有表单字段，HPP 就能让 Agent 帮你填。

---

## How a handshake prompt looks · 握手提示词长什么样

用户点击「AI 助手」后，服务自动生成并复制到剪贴板：

```
# Handshake Prompt — 报销申请单

## Credentials · 会话凭证
- sessionId: 4f2a8c1e...
- token: AbC9Xm2R...      ← 一次性令牌，30分钟有效
- baseUrl: https://oa.company.com
- mode: form-fill

## Current state · 当前已填内容
（服务自动注入当前表单数据）

## Instructions · 操作说明
1. GET  https://oa.company.com/handshake/context/4f2a8c1e  (X-Handshake-Token: <token>)
2. POST https://oa.company.com/handshake/action/4f2a8c1e   {"actions":[...]}

## Waiting for your instructions · 等待你的指令...
```

Agent 解析凭证，拉取表单 schema，推理字段值，提交——字段值实时出现在用户的浏览器页面上。

---

## Security by design · 安全设计

- **Token 30分钟过期** — 提示词泄露后很快失效 · Token expires in 30 minutes
- **192-bit token 熵** — 暴力破解不可行 · Brute force is computationally infeasible
- **用户数据保护** — 服务端强制拒绝 AI 覆盖用户已手填的字段 · Server refuses AI overwrites of user-filled fields
- **速率限制** — 每会话每分钟 60 次请求上限 · 60 req/min/session
- **用户必须确认** — 不点提交什么都不保存 · Nothing saves without user clicking submit

详见 [docs/threat-model.md](docs/threat-model.md)。

---

## Get started in 3 lines · 3行代码接入（Flask）

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
HandshakeManager(app, sock)   # ← HPP 接入完成
```

接入后，你的服务自动拥有以下接口：

| 接口 | 方法 | 用途 |
|------|------|------|
| `/handshake/session`       | POST | 浏览器创建会话，获取 token |
| `/handshake/context/<sid>` | GET  | Agent 读取 schema + 当前值 |
| `/handshake/action/<sid>`  | POST | Agent 提交字段值（含校验和速率限制）|
| `/handshake/notify/<sid>`  | POST | 浏览器回报用户手动编辑 |
| `/ws/handshake/<sid>`      | WS   | 浏览器接收 Agent 实时推送 |

### Browser SDK · 浏览器端（任意框架）

```ts
import { HandshakeClient } from 'handshake-prompt-client'

const hpp = new HandshakeClient()
await hpp.createSession({ mode: 'form-fill', schema: FIELDS, context: getFormData() })
hpp.on('action', ({ key, value }) => applyToForm(key, value))   // 实时填入
hpp.connect()
await hpp.copyPrompt()   // 用户把这段文字粘贴给 Agent
```

### Agent SDK · Agent 端（CLI 或代码调用）

```bash
pip install handshake-prompt-agent

# 解析用户粘贴的握手提示词
handshake-prompt-agent parse-prompt --prompt "..."

# 拉取当前 schema + 已填内容（每次操作前必须调用）
handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>

# 填写字段 —— 实时推送到用户浏览器
handshake-prompt-agent action --sid <sid> --token <token> --base <url> \
    --data '{"name":"张三","department":"研发部","startDate":"2026-07-01"}'
```

---

## Install · 安装

```bash
# 服务端 Server-side (Python / Flask)
pip install handshake-prompt

# 浏览器端 Browser-side (TypeScript / JavaScript)
npm install handshake-prompt-client

# Agent 端 Agent-side (CLI + Python API，无外部依赖)
pip install handshake-prompt-agent
```

---

## What's in this repo · 仓库结构

```
handshake-prompt/
├── SPEC.md                      ← 协议规范 Protocol specification
├── docs/
│   ├── comparison.md            ← 对比 OAuth / API Key / MCP
│   └── threat-model.md          ← 安全分析 Security analysis
├── libs/
│   ├── python/                  ← handshake-prompt      (Flask 服务端 SDK)
│   ├── js/                      ← handshake-prompt-client (浏览器 TypeScript SDK)
│   └── agent-python/            ← handshake-prompt-agent  (Agent CLI + SDK)
└── examples/
    ├── server-flask/            ← 最小化端到端示例 Minimal end-to-end demo
    ├── oa-expense-report/       ← OA 报销单示例 OA expense form walkthrough
    └── skill/                   ← Agent skill 参考文件
```

---

## Run the demo · 运行示例

```bash
git clone https://github.com/CGandGameEngineLearner/handshake-prompt
cd handshake-prompt/examples/server-flask
pip install -r requirements.txt
python app.py
# 打开 http://localhost:5000
```

点击「🤖 AI Assistant」，把提示词粘贴给你的 Agent，告诉它要填什么。

OA 场景示例：

```bash
cd handshake-prompt/examples/oa-expense-report
pip install -r requirements.txt
python app.py
# 打开 http://localhost:5001
```

---

## Roadmap · 路线图

- [x] v0.1 — Flask 服务端 SDK、TypeScript 浏览器 SDK、Python Agent SDK + CLI
- [ ] FastAPI 服务端适配器
- [ ] Express.js 服务端适配器
- [ ] React / Vue 组件包
- [ ] 合规性测试套件
- [ ] 生产部署指南（nginx、HTTPS、Redis 多实例）

---

## License · 开源协议

MIT — free for commercial use · 免费商用
