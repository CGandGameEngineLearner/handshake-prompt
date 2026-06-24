# CI 密钥配置

打 tag `v*` 后会触发三个发布 workflow：

| Workflow | 产物 | Secret |
|----------|------|--------|
| `publish-pypi-server.yml` | `handshake-prompt` | `PYPI_API_TOKEN` |
| `publish-pypi-agent.yml` | `handshake-prompt-agent` | `PYPI_API_TOKEN` |
| `publish-npm.yml` | `handshake-prompt-client` | `NPM_TOKEN` |

## PyPI

1. 登录 [pypi.org](https://pypi.org) → Account settings → API tokens
2. 创建 token（scope: 整个账户或指定项目）
3. 在 GitHub 仓库 Settings → Secrets → Actions 添加 `PYPI_API_TOKEN`

## npm（常见 403 原因）

若 workflow 报：

```
403 Forbidden - Two-factor authentication or granular access token
with bypass 2fa enabled is required to publish packages.
```

说明当前 `NPM_TOKEN` 无效或权限不足。按以下步骤重新配置：

1. 登录 [npmjs.com](https://www.npmjs.com) → Access Tokens
2. 点击 **Generate New Token** → 选择 **Granular Access Token**
3. 配置权限：
   - **Packages and scopes** → 选择 `handshake-prompt-client`（或 All packages）→ **Read and write**
   - 勾选 **Bypass two-factor authentication for automation**（自动化发布必须）
4. 复制 token，在 GitHub 仓库添加/更新 Secret：`NPM_TOKEN`
5. 重新发布：
   - Actions → 选择失败的 `Publish handshake-prompt-client to npm` → **Re-run all jobs**
   - 若该版本已部分发布失败，需 bump `libs/js/package.json` 版本号后打新 tag

### 手动发布（临时方案）

```bash
cd libs/js
npm install
npm run build
npm login   # 或 export NODE_AUTH_TOKEN=...
npm publish --access public
```

## 验证

```bash
pip index versions handshake-prompt
npm view handshake-prompt-client version --registry https://registry.npmjs.org
```
