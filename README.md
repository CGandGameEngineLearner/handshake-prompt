# 握手提示词协议（Handshake Prompt Protocol）

> **一个提示词，完成鉴权与服务接入。**
> 无需配置 API Key、MCP、Skill —— 用户复制一段文字，Agent 即进入工作模式。

---

## 这是什么

**握手提示词**是一种让 AI Agent 无缝接入已有 Web 服务的轻量协议。

用户点一个按钮，得到一段"握手提示词"，把它发给自己的 Agent（如 Codemaker、Cursor、Claude 等），Agent 即可：

- 自动鉴权（提示词内含一次性 Token）
- 实时读取当前页面状态
- 代替用户操作页面（填写表单、提交数据等）
- 所有操作在用户浏览器中**实时可见**

整个过程**用户不需要**：
- ❌ 配置 API Key
- ❌ 安装 MCP Server
- ❌ 设置环境变量
- ❌ 懂任何技术

---

## 类比

| 技术 | 目的 | 用户操作 |
|------|------|---------|
| 扫码登录 | 手机授权网页登录 | 扫一下 |
| OAuth | 第三方应用授权 | 点击授权 |
| **握手提示词** | Agent 授权操作网页服务 | 复制粘贴 |

握手提示词解决的问题和扫码登录类似：**把"授权+接入"这件复杂的事，压缩成用户的一个简单动作。**

---

## 协议核心

### 握手提示词结构

```
# 握手提示词 - [服务名称] [操作模式]

## 会话凭证
- sessionId: a1b2c3d4e5f6...   （会话标识）
- token: Ax9kR2mP...            （一次性访问令牌，有效期 N 分钟）
- baseUrl: https://your-service.com
- mode: fill-form               （操作模式，由服务定义）

## 当前上下文
[服务动态注入的当前状态，如表单已填内容、用户当前页面等]

## Agent 行动指南
[服务定义的操作说明，Agent 读懂后即可行动]

## 等待用户指令...
```

### 三个角色

```
┌──────────┐  ①点按钮       ┌──────────────┐  ②生成会话+Token  ┌──────────┐
│   用户    │ ────────────→ │   Web 服务    │ ←────────────────  │          │
│ (浏览器)  │               │  (服务端)     │                    │          │
│          │  ③复制提示词   │              │                    │          │
│          │ ←────────────  │              │                    │          │
│          │                │              │                    │          │
│          │  ④粘贴给 Agent │              │                    │  Agent   │
│          │ ────────────→  │              │                    │ (本地)   │
│          │                │  ⑤Token鉴权  │                    │          │
│          │                │ ←────────────────────────────────  │          │
│          │                │  ⑥读取/操作  │                    │          │
│ ⑦实时看到 │ ←──────────── │  (WebSocket) │                    │          │
│ Agent操作 │                └──────────────┘                    └──────────┘
└──────────┘
```

---

## 安全设计

- **Token 一次性**：每次点按钮生成新 Token，有效期可配置
- **Token 高熵**：192bit 随机（`secrets.token_urlsafe(24)`），暴力破解不可行
- **时序攻击防护**：Token 比对使用 `hmac.compare_digest`
- **用户数据保护**：服务端强制拒绝 Agent 覆盖用户已填写的字段
- **速率限制**：每会话每分钟请求次数上限，防滥用
- **会话绑定**：Token 绑定创建者身份（登录 session），他人无法回报数据
- **WebSocket 鉴权**：WS 连接需携带 Token，防止任意人订阅会话流

---

## 适用场景

任何有"让 AI 帮用户操作"需求的 Web 系统都可以接入：

- 📋 **表单填写**：策划配表、行政申请、工单填报
- 📊 **数据录入**：ERP、CRM、内容管理系统
- 🔧 **配置操作**：系统配置、权限管理、参数调整
- 📦 **任务提交**：订单创建、发布流程、审批提交

**特别适合旧系统 AI 化改造**：不需要改造核心业务逻辑，只需在前端加一个按钮，后端加几个轻量接口，旧系统即获得 AI 操作能力。

---

## 参考实现

本仓库提供基于 Python (Flask) + Vue 3 的参考实现：

- [`server/`](./server/) — 服务端：会话管理、Token 鉴权、WebSocket 中继、REST API
- [`client/`](./client/) — 前端：`AIFillPanel` 通用组件
- [`skill/`](./skill/) — Agent Skill：`handshake_client.py` 通用客户端脚本

### 快速体验

```bash
# 1. 启动服务端
cd server && pip install -r requirements.txt && python app.py

# 2. 打开浏览器访问示例页面
# 3. 点击"AI 操作"按钮，复制握手提示词
# 4. 粘贴给你的 Agent，告诉它你想做什么
```

---

## 接入指南（为服务开发者）

### 服务端（3 个接口 + 1 个 WebSocket）

```
POST /handshake/session          创建会话，返回 sessionId + token
GET  /handshake/context/<sid>    Agent 读取当前上下文（需 token）
POST /handshake/action/<sid>     Agent 执行操作（需 token，有速率限制）
WS   /ws/handshake/<sid>         实时推送通道（需 token）
```

### 前端（1 个组件）

```vue
<HandshakeButton
  :context-builder="() => getCurrentFormData()"
  :action-handler="(key, value) => applyFieldValue(key, value)"
  service-name="我的表单"
/>
```

### Agent Skill（1 个脚本，无需修改）

```bash
python handshake_client.py get-context --sid <sid> --token <token> --base <url>
python handshake_client.py action --sid <sid> --token <token> --base <url> --data '{...}'
```

---

## 协议规范

完整协议规范见 [SPEC.md](./SPEC.md)。

---

## 开源协议

MIT License

---

## 起源

> 本协议源于一个旧填表系统的 AI 化改造实践。
> 我们发现用户最大的痛点不是 AI 不够聪明，而是"接入太麻烦"。
> 握手提示词协议就是为了解决这个问题而生的。
