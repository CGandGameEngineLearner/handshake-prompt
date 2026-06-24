"""
OA Expense Report Example
=========================

Demonstrates how an existing OA (Office Automation) expense report form
gains Agent-fill capability via Handshake Prompt Protocol — with zero
changes to the existing approval backend.

Run:
    pip install -r requirements.txt
    python app.py
    # open http://localhost:5001
"""
from flask import Flask, render_template_string
from flask_cors import CORS
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app = Flask(__name__)
app.secret_key = 'demo-oa-change-in-production'
CORS(app, supports_credentials=True)
sock = Sock(app)

# ── One line to add Agent-fill capability to the existing OA portal ──
hm = HandshakeManager(app, sock)


@app.route('/')
def index():
    return render_template_string(OA_PAGE)


OA_PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Expense Report — OA Portal</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 700px; margin: 40px auto;
         padding: 0 20px; color: #1a1a2e; background: #f8f9fa; }
  .card { background: #fff; border-radius: 10px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
  h2 { margin: 0 0 4px; font-size: 20px; }
  .subtitle { color: #888; font-size: 13px; margin-bottom: 24px; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field.full { grid-column: 1 / -1; }
  label { font-size: 12px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: .5px; }
  input, select, textarea { padding: 9px 12px; border: 1.5px solid #e0e0e0; border-radius: 6px;
    font-size: 14px; outline: none; transition: border .2s; }
  input:focus, select:focus, textarea:focus { border-color: #4361ee; }
  input.ai-filled { border-color: #2dc653; background: #f0fff4;
    animation: pop 1s ease-out; }
  @keyframes pop { 0% { background: #b9f1c8; } 100% { background: #f0fff4; } }
  .actions { display: flex; gap: 10px; margin-top: 20px; align-items: center; }
  button { padding: 10px 20px; border: 0; border-radius: 7px; cursor: pointer; font-size: 14px; font-weight: 600; }
  .btn-ai { background: #ff8500; color: #fff; }
  .btn-submit { background: #4361ee; color: #fff; }
  .btn-reset { background: #f1f3f5; color: #555; }
  #status { font-size: 12px; color: #6e7781; flex: 1; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 11px; font-weight: 600; background: #fff3e0; color: #e65100; }
</style>
</head>
<body>
<div class="card">
  <h2>Expense Report</h2>
  <p class="subtitle">Finance → Reimbursement → New Request
    <span class="badge">HPP Demo</span>
  </p>

  <div class="row">
    <div class="field">
      <label>Employee Name *</label>
      <input data-key="employeeName" placeholder="e.g. Alice Chen">
    </div>
    <div class="field">
      <label>Employee ID</label>
      <input data-key="employeeId" placeholder="e.g. EMP-00421">
    </div>
  </div>

  <div class="row">
    <div class="field">
      <label>Department *</label>
      <select data-key="department">
        <option value="">Select department</option>
        <option>Engineering</option>
        <option>Product</option>
        <option>Design</option>
        <option>Finance</option>
        <option>HR</option>
        <option>Sales</option>
      </select>
    </div>
    <div class="field">
      <label>Report Period *</label>
      <input data-key="period" placeholder="e.g. 2026-06">
    </div>
  </div>

  <div class="row">
    <div class="field">
      <label>Category *</label>
      <select data-key="category">
        <option value="">Select category</option>
        <option>Business Travel</option>
        <option>Meals & Entertainment</option>
        <option>Office Supplies</option>
        <option>Software / SaaS</option>
        <option>Training & Conferences</option>
        <option>Other</option>
      </select>
    </div>
    <div class="field">
      <label>Amount (¥) *</label>
      <input data-key="amount" type="number" placeholder="0.00" step="0.01">
    </div>
  </div>

  <div class="row">
    <div class="field">
      <label>Receipt Date *</label>
      <input data-key="receiptDate" type="date">
    </div>
    <div class="field">
      <label>Invoice / Receipt No.</label>
      <input data-key="invoiceNo" placeholder="e.g. INV-20260615-001">
    </div>
  </div>

  <div class="row">
    <div class="field full">
      <label>Purpose / Description *</label>
      <textarea data-key="description" rows="3"
        placeholder="Briefly describe the business purpose of this expense..."></textarea>
    </div>
  </div>

  <div class="row">
    <div class="field">
      <label>Approver</label>
      <input data-key="approver" placeholder="Manager name">
    </div>
    <div class="field">
      <label>Cost Center</label>
      <input data-key="costCenter" placeholder="e.g. CC-ENG-01">
    </div>
  </div>

  <div class="actions">
    <button class="btn-ai" onclick="startHPP()">🤖 AI Assistant</button>
    <button class="btn-submit" onclick="submitForm()">Submit for Approval</button>
    <button class="btn-reset" onclick="resetForm()">Reset</button>
    <span id="status"></span>
  </div>
</div>

<script type="module">
import { HandshakeClient } from 'https://cdn.jsdelivr.net/npm/handshake-prompt-client@0.1/+esm'

// ── Schema: describes every field to the Agent ──────────────────────
const SCHEMA = [
  { key: 'employeeName', label: 'Employee Name',    type: 'string',  required: true },
  { key: 'employeeId',   label: 'Employee ID',      type: 'string' },
  { key: 'department',   label: 'Department',       type: 'enum',    required: true,
    options: ['Engineering','Product','Design','Finance','HR','Sales'].map(v=>({value:v})) },
  { key: 'period',       label: 'Report Period',    type: 'string',  required: true,
    example: '2026-06', desc: 'YYYY-MM format' },
  { key: 'category',     label: 'Expense Category', type: 'enum',    required: true,
    options: ['Business Travel','Meals & Entertainment','Office Supplies',
              'Software / SaaS','Training & Conferences','Other'].map(v=>({value:v})) },
  { key: 'amount',       label: 'Amount (¥)',       type: 'float',   required: true },
  { key: 'receiptDate',  label: 'Receipt Date',     type: 'string',  required: true,
    example: '2026-06-15', desc: 'YYYY-MM-DD' },
  { key: 'invoiceNo',    label: 'Invoice No.',      type: 'string' },
  { key: 'description',  label: 'Description',      type: 'string',  required: true },
  { key: 'approver',     label: 'Approver',         type: 'string' },
  { key: 'costCenter',   label: 'Cost Center',      type: 'string' },
]

const hpp = new HandshakeClient({ baseUrl: location.origin })
const $s  = t => document.getElementById('status').textContent = t

function getFormContext() {
  const ctx = {}
  document.querySelectorAll('[data-key]').forEach(el => {
    ctx[el.dataset.key] = el.value || null
  })
  return ctx
}

window.startHPP = async function() {
  $s('Creating session...')
  await hpp.createSession({ mode: 'form-fill', schema: SCHEMA, context: getFormContext() })

  hpp.on('connected', () => $s('✅ Session ready — paste the prompt to your Agent'))
  hpp.on('action', ({ key, value }) => {
    const el = document.querySelector(`[data-key="${key}"]`)
    if (!el) return
    el.value = value
    el.classList.add('ai-filled')
    setTimeout(() => el.classList.remove('ai-filled'), 1400)
    $s(`✍️  ${key} → ${JSON.stringify(value)}`)
  })
  hpp.on('done', ({ applied, missing }) => {
    const m = missing.length ? ` · Missing: ${missing.join(', ')}` : ' · All required fields filled!'
    $s(`✅ Agent done — ${applied} fields applied${m}`)
  })
  hpp.connect()

  const copied = await hpp.copyPrompt({
    title: 'Expense Report — AI Fill',
    customInstructions:
      'Fill in the expense report based on the user\'s description. ' +
      'Ask the user for any required information that is missing. ' +
      'Do NOT submit — the user will review and click Submit.',
  })
  if (copied) alert('✅ Handshake prompt copied!\n\nPaste it to your AI Agent and describe your expense.')
  else $s('Prompt ready — copy it from the console')
}

// Report user edits back to the session so Agent sees the latest state
document.querySelectorAll('[data-key]').forEach(el => {
  el.addEventListener('change', () => hpp.notifyUserEdit(el.dataset.key, el.value))
})

window.submitForm = function() {
  const data = getFormContext()
  const missing = SCHEMA.filter(f => f.required && !data[f.key]).map(f => f.label)
  if (missing.length) { alert(`Please fill required fields:\n${missing.join('\n')}`); return }
  alert('✅ Submitted for approval!\n\n' + JSON.stringify(data, null, 2))
}

window.resetForm = function() {
  document.querySelectorAll('[data-key]').forEach(el => el.value = '')
  $s('')
}
</script>
</body>
</html>
"""


if __name__ == '__main__':
    print('OA Expense Report HPP Demo → http://localhost:5001')
    app.run(host='0.0.0.0', port=5001, debug=True)
