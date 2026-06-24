# handshake-prompt-client

> Browser SDK for the **Handshake Prompt Protocol (HPP)** —
> grant AI Agents access to your web service via a single copy-paste prompt.

Framework-agnostic. Works with plain JS, React, Vue, Svelte, etc.

## Install

```bash
npm i handshake-prompt-client
```

## Quick start

```ts
import { HandshakeClient } from 'handshake-prompt-client'

const hpp = new HandshakeClient()

// 1. User clicks the "AI Action" button
async function onClickAIButton() {
  // Tell the server what fields exist and their current values
  await hpp.createSession({
    mode: 'form-fill',
    schema: [
      { key: 'name',  type: 'string', required: true, example: 'Alice' },
      { key: 'email', type: 'string', required: true },
      { key: 'age',   type: 'int' },
    ],
    context: {
      name:  document.getElementById('name').value,
      email: document.getElementById('email').value,
      age:   null,
    },
  })

  // 2. Listen for real-time updates from Agent
  hpp.on('action', ({ key, value }) => {
    document.getElementById(key).value = value
    highlight(key)
  })
  hpp.on('done', ({ applied, missing }) => {
    alert(`Agent filled ${applied} fields. Missing: ${missing.join(', ')}`)
  })
  hpp.connect()

  // 3. Copy the handshake prompt to clipboard
  await hpp.copyPrompt({ title: 'My Form AI Fill' })
  alert('Prompt copied! Paste it into your AI Agent.')
}

// Notify server when user manually edits a field
document.getElementById('name').addEventListener('input', (e) => {
  hpp.notifyUserEdit('name', e.target.value)
})
```

## API

### `new HandshakeClient(options)`

```ts
const hpp = new HandshakeClient({
  baseUrl:  'https://your-service.com',  // default: location.origin
  prefix:   '/handshake',                // default: '/handshake'
  wsPrefix: '/ws/handshake',             // default: '/ws/handshake'
})
```

### `await hpp.createSession({ mode, schema, context, meta })`

Create a session on the server. Returns `SessionInfo` (also stored on `hpp.session`).

### `hpp.connect()`

Open the WebSocket channel. Call after `createSession`.

### `hpp.on(eventType, callback)`

Subscribe to events. Returns an unsubscribe function.

| Event       | Payload                                                                |
|-------------|------------------------------------------------------------------------|
| `connected` | `{ sessionId, mode }` — WebSocket connected and authenticated          |
| `action`    | `{ key, value }` — Agent applies a value to a field                    |
| `done`      | `{ applied, rejected, missing }` — Batch complete                      |
| `error`     | `{ msg }` — Server-side error                                          |

### `hpp.notifyUserEdit(key, value)`

Tell the server that the user manually edited a field.
The server marks it as `by=user_edit` and prevents the AI from overwriting it.

### `hpp.buildPrompt(opts?)`  /  `await hpp.copyPrompt(opts?)`

Build or copy-to-clipboard the handshake prompt text.

```ts
const text = hpp.buildPrompt({
  title: 'Product Entry AI Fill',
  customInstructions: 'Focus on tech products with prices in CNY.',
  skillName: 'form-fill',
})
```

## Vue 3 example

```vue
<script setup>
import { ref, onUnmounted } from 'vue'
import { HandshakeClient } from 'handshake-prompt-client'

const hpp = new HandshakeClient()
const status = ref('idle')

async function startSession() {
  await hpp.createSession({ mode: 'form-fill', schema, context })
  hpp.on('action', applyToForm)
  hpp.on('done', () => status.value = 'done')
  hpp.connect()
  await hpp.copyPrompt()
}

onUnmounted(() => hpp.disconnect())
</script>
```

## License

MIT
