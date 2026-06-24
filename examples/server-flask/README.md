# Minimal Flask Demo

A 50-line Flask app demonstrating the full **Handshake Prompt Protocol**.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

## How it works

```python
from flask import Flask
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app  = Flask(__name__)
sock = Sock(app)
hm   = HandshakeManager(app, sock)   # That's the entire backend!
```

The browser side uses [`@handshake-prompt/client`](https://www.npmjs.com/package/@handshake-prompt/client)
loaded from a CDN. See `app.py` for the full HTML/JS.

## Try it

1. Open the page
2. Click "🤖 AI Fill"
3. Handshake prompt is copied to clipboard
4. Paste it into your AI Agent (Codemaker / Claude / Cursor / etc.)
5. Tell the Agent what you want, e.g. *"Make this a tech product around $300"*
6. Watch fields fill in real time
