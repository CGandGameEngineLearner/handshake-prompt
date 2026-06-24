# OA Expense Report Example

A realistic demo showing how an existing **Office Automation (OA)** expense
report form gains AI Agent support via Handshake Prompt Protocol.

## The point

This example simulates a typical enterprise OA portal scenario:

- The form already exists with its own approval workflow
- The backend is untouched — no new API endpoints, no webhook integration
- **Adding `HandshakeManager(app, sock)` is the only change needed**
- Users can now say *"Fill this expense report for my Shanghai business trip last week"*
  and the Agent will ask clarifying questions, fill the fields, and wait for confirmation

## Run

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5001
```

## Try it

1. Open the page — you'll see a realistic expense report form
2. Click **🤖 AI Assistant**
3. Paste the prompt to your Agent
4. Tell the Agent something like:
   - *"Business trip to Shanghai, June 12-14, hotel ¥1,280, receipt INV-20260614-099, department Engineering"*
   - *"Team lunch for product review meeting, 8 people, ¥640, June 20"*
5. Watch the fields fill in one by one, highlighted in green
6. Edit anything you want, then click **Submit for Approval**

## Key pattern

```python
# Before HPP: no Agent support, pure form
app = Flask(__name__)
# ... routes, business logic, approval workflow

# After HPP: one line addition
from handshake_prompt import HandshakeManager
hm = HandshakeManager(app, sock)   # ← that's it
```

The existing approval workflow, validation, and database writes are completely
unchanged. HPP only handles the *fill* step — the Agent writes to the form,
the human confirms, and then the existing submit button triggers the existing flow.
