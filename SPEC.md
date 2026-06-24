# 握手提示词协议规范 v0.1

## 1. 概述

握手提示词协议（Handshake Prompt Protocol，HPP）定义了一种 Web 服务与 AI Agent 之间建立授权连接的标准方式。

协议的核心思想：

> **服务端生成一段"握手提示词"，用户将其发给 Agent，Agent 通过解析提示词中的凭证自动完成鉴权并接入服务。**

---

## 2. 角色定义

| 角色 | 描述 |
|------|------|
| **服务端（Server）** | 提供握手提示词接口的 Web 服务 |
| **用户（User）** | 在浏览器中操作服务的人 |
| **Agent** | 用户使用的 AI 助手（如 Codemaker、Claude、ChatGPT 等） |
| **Skill** | Agent 执行 HPP 操作的工具脚本（语言无关） |

---

## 3. 握手流程

```
用户                     服务端                    Agent
 │                         │                         │
 │── 点击"AI操作"按钮 ───→ │                         │
 │                         │── 创建 Session ────────→│
 │                         │── 生成 Token ──────────→│
 │ ←─ 返回握手提示词 ──────│                         │
 │                         │                         │
 │── 复制握手提示词给 ─────────────────────────────→ │
 │                         │                         │
 │── 打开 WebSocket ──────→│                         │
 │   (携带 Token)          │                         │
 │                         │ ←── GET /context ────── │
 │                         │     (携带 Token)         │
 │                         │─── 返回上下文 ──────────→│
 │                         │                         │
 │                         │ ←── POST /action ─────── │
 │                         │     (携带 Token)         │
 │ ←─ WebSocket 实时推送 ──│                         │
 │   (用户实时看到操作)     │                         │
 │                         │                         │
 │── 用户确认并提交 ───────→│                         │
```

---

## 4. 握手提示词格式规范

```
# 握手提示词 - {服务名} {操作模式}

## 会话凭证
- sessionId: {16字节hex}
- token: {URL-safe base64, 32字节}
- baseUrl: {https://...}
- mode: {服务自定义的操作模式}
- expiresIn: {秒}

## 当前上下文
{服务动态注入，描述当前状态，格式由服务定义}

## 操作说明
{服务定义的 Agent 行动指南}

## 注意事项
- 此令牌有效期 {N} 分钟，请尽快使用
- 请勿将此握手提示词转发给他人
- {其他服务特定注意事项}

---
[等待用户指令]
```

**关键字段说明：**

- `sessionId`：会话唯一标识，用于标识一个握手会话
- `token`：一次性访问令牌，所有 Agent 接口调用必须携带
- `baseUrl`：服务端地址
- `mode`：操作模式，由服务定义（如 `fill-form`、`data-entry`、`config`）

---

## 5. 服务端接口规范

### 5.1 创建会话

```
POST {baseUrl}/handshake/session
Content-Type: application/json

{
  "mode": "fill-form",
  "context": { ... }     // 服务自定义的初始上下文
}

Response 200:
{
  "sessionId": "a1b2c3d4e5f6...",
  "token": "Ax9kR2mP...",
  "wsUrl": "/ws/handshake/{sessionId}",
  "contextUrl": "/handshake/context/{sessionId}",
  "actionUrl": "/handshake/action/{sessionId}",
  "expiresIn": 1800
}
```

### 5.2 获取上下文

```
GET {baseUrl}/handshake/context/{sessionId}
X-Handshake-Token: {token}
```

返回当前会话的完整上下文（服务自定义格式）。

**Agent 每次操作前必须调用此接口，获取最新状态。**

### 5.3 执行操作

```
POST {baseUrl}/handshake/action/{sessionId}
X-Handshake-Token: {token}
Content-Type: application/json

{
  "actions": [
    { "type": "set", "key": "field.name", "value": "..." },
    { "type": "set", "key": "field.age",  "value": 18 }
  ],
  "stream": true,      // 是否逐条实时推送到浏览器
  "intervalMs": 300    // 推送间隔（毫秒）
}

Response 200:
{
  "ok": true,
  "applied": [...],    // 成功应用的操作
  "rejected": [...],   // 被拒绝的操作（如用户已填写保护）
  "errors": [...],     // 校验失败
  "context": { ... }   // 操作后的最新上下文快照
}
```

### 5.4 WebSocket 实时通道

```
WS {wsUrl}?token={token}
```

浏览器订阅，接收服务端推送：

```json
{ "type": "action",    "key": "...", "value": "..." }
{ "type": "done",      "applied": 5, "rejected": 1 }
{ "type": "error",     "msg": "..." }
{ "type": "connected", "sessionId": "..." }
```

---

## 6. Token 鉴权规范

所有 Agent 接口（context、action、diff）必须携带 token：

- **方式一（推荐）**：HTTP Header `X-Handshake-Token: {token}`
- **方式二**：Query 参数 `?token={token}`
- **WebSocket**：Query 参数 `?token={token}`（WS 不支持自定义 Header）

Token 比对**必须**使用常量时间比较（防时序攻击）：
- Python: `hmac.compare_digest` 或 `secrets.compare_digest`
- Node.js: `crypto.timingSafeEqual`

---

## 7. 安全要求

| 要求 | 规范 |
|------|------|
| sessionId 熵 | ≥ 128bit（推荐 `secrets.token_hex(16)`） |
| token 熵 | ≥ 192bit（推荐 `secrets.token_urlsafe(24)`） |
| token 有效期 | 默认 30 分钟，可配置 |
| 速率限制 | 每会话每分钟 ≤ 60 次 Agent 请求 |
| 用户数据保护 | 服务端必须拒绝 Agent 覆盖用户已写入的数据 |
| WebSocket 鉴权 | 连接时校验 token，失败立即关闭 |
| HTTPS | 生产环境必须使用 HTTPS/WSS |

---

## 8. Skill 规范

任何语言实现的 HPP Skill 必须支持以下操作：

```
get-context  --sid <sid> --token <token> --base <url>
             → 打印格式化的当前上下文，供 Agent 理解

action       --sid <sid> --token <token> --base <url> --data '<json>'
             → 提交操作，打印结果

get-diff     --sid <sid> --token <token> --base <url> [--since <iso_ts>]
             → 打印增量变更（用于多轮对话中感知用户修改）
```

输出格式：人类可读 + 原始 JSON（被 `[JSON-BEGIN]` / `[JSON-END]` 包裹）。

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06 | 初始版本，基于 autofill 项目提炼 |
