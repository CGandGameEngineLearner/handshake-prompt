"""
Minimal HPP demo — demonstrates session/pair/WebSocket in ~30 lines.
Run: pip install -r requirements.txt && python app.py → http://localhost:5000
"""
from flask import Flask, render_template_string, url_for
from flask_cors import CORS
from flask_sock import Sock
from handshake_prompt import HandshakeManager

app = Flask(__name__)
app.secret_key = 'demo-only-change-in-production'
CORS(app, supports_credentials=True)
sock = Sock(app)
hm = HandshakeManager(app, sock)

@app.route('/')
def index():
    return render_template_string(open('templates/index.html').read())

if __name__ == '__main__':
    print('Open http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)
