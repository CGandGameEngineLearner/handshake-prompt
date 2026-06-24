"""
Minimal Flask demo for the Handshake Prompt Protocol.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000
"""
from flask import Flask, render_template_string
from flask_cors import CORS
from flask_sock import Sock

from handshake_prompt import HandshakeManager


app = Flask(__name__)
app.secret_key = 'demo-only-change-in-production'
CORS(app, supports_credentials=True)
sock = Sock(app)

# One-liner integration — that's it.
hm = HandshakeManager(app, sock)


@app.route('/')
def index():
    return render_template_string(DEMO_HTML)


DEMO_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Handshake Prompt Demo</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; color: #222; }
  h2 { margin-top: 0; }
  .field { margin: 14px 0; }
  label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
  input, textarea { width: 100%; padding: 8px 10px; border: 1px solid #d0d7de; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
  input.ai { border-color: #2da44e; background: #f0fff4; animation: pop .8s ease-out; }
  @keyframes pop { 0% { background: #b9f1c8; } 100% { background: #f0fff4; } }
  button { padding: 8px 16px; border: 0; border-radius: 6px; cursor: pointer; font-size: 14px; }
  .btn-ai { background: #fb8500; color: #fff; }
  .btn-submit { background: #2563eb; color: #fff; margin-left: 8px; }
  #status { font-size: 12px; color: #6e7781; margin-top: 12px; }
</style>
</head>
<body>
<h2>🤝 Handshake Prompt Demo</h2>
<p style="font-size:13px;color:#555">
Click "AI Fill", paste the copied prompt into your Agent (e.g. Codemaker, Claude),
and watch the Agent fill the form in real time.
</p>

<div class="field"><label>Product name *</label>
  <input data-key="name" placeholder="e.g. Bluetooth Earbuds"></div>
<div class="field"><label>Price *</label>
  <input data-key="price" type="number" placeholder="e.g. 299"></div>
<div class="field"><label>Category</label>
  <input data-key="category" placeholder="e.g. Electronics"></div>
<div class="field"><label>Description</label>
  <textarea data-key="description" rows="3" placeholder="Describe the product..."></textarea></div>
<div class="field"><label>Stock</label>
  <input data-key="stock" type="number" placeholder="e.g. 100"></div>

<button class="btn-ai" onclick="aiFill()">🤖 AI Fill</button>
<button class="btn-submit" onclick="submitForm()">Submit</button>
<div id="status"></div>

<script type="module">
import { HandshakeClient } from 'https://cdn.jsdelivr.net/npm/@handshake-prompt/client@0.1/+esm'

const SCHEMA = [
  { key: 'name',        type: 'string', required: true,  example: 'Bluetooth Earbuds' },
  { key: 'price',       type: 'float',  required: true,  example: 299.0 },
  { key: 'category',    type: 'string', example: 'Electronics' },
  { key: 'description', type: 'string', example: 'High-quality earbuds, 20h battery' },
  { key: 'stock',       type: 'int',    example: 100 },
]

const hpp = new HandshakeClient()
const $status = document.getElementById('status')

function setStatus(s) { $status.textContent = s }

function getContext() {
  const ctx = {}
  document.querySelectorAll('[data-key]').forEach(el => {
    ctx[el.dataset.key] = el.value || null
  })
  return ctx
}

window.aiFill = async function() {
  setStatus('Creating handshake session...')
  await hpp.createSession({ mode: 'form-fill', schema: SCHEMA, context: getContext() })

  hpp.on('connected', () => setStatus('✅ WebSocket connected, waiting for Agent...'))
  hpp.on('action', ({ key, value }) => {
    const el = document.querySelector(`[data-key="${key}"]`)
    if (el) {
      el.value = value
      el.classList.add('ai')
      setTimeout(() => el.classList.remove('ai'), 1200)
    }
    setStatus(`✍️ Filled ${key} = ${JSON.stringify(value)}`)
  })
  hpp.on('done', ({ applied, missing }) => {
    setStatus(`✅ Done. Applied ${applied} fields. Missing: ${missing.join(', ') || 'none'}`)
  })
  hpp.connect()

  await hpp.copyPrompt({ title: 'Product Entry — AI Fill' })
  alert('Handshake prompt copied to clipboard!\nPaste it into your AI Agent.')
}

// Notify server when user manually edits a field
document.querySelectorAll('[data-key]').forEach(el => {
  el.addEventListener('change', () => hpp.notifyUserEdit(el.dataset.key, el.value))
})

window.submitForm = function() {
  alert('Submitted:\n' + JSON.stringify(getContext(), null, 2))
}
</script>
</body>
</html>
"""


if __name__ == '__main__':
    print('Open http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)
