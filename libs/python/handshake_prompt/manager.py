# encoding=utf-8
"""
HandshakeManager — Flask adapter for the HPP ProtocolEngine.

This module is a thin transport binding. Business logic belongs in mode
handlers (handshake_prompt.modes) or application hooks.
"""
from .prompt import build_prompt
from .protocol import ProtocolEngine
from .store import SessionStore


class HandshakeManager:
    """
    Mount HPP on a Flask app + flask_sock instance.

    Example::

        from flask import Flask
        from flask_sock import Sock
        from handshake_prompt import HandshakeManager

        app = Flask(__name__)
        sock = Sock(app)
        hm = HandshakeManager(app, sock)

        @hm.on_create_session
        def bind_owner(sess, request):
            sess.owner = session.get('user_id')
    """

    def __init__(self, app, sock, prefix='/handshake', ws_prefix='/ws/handshake',
                 ttl=1800, rate_limit_per_min=60,
                 store=None, validator=None,
                 require_browser_auth=None, mode_handlers=None):
        self.prefix = prefix.rstrip('/')
        self.ws_prefix = ws_prefix.rstrip('/')
        self.require_browser_auth = require_browser_auth
        self.store = store or SessionStore()

        self.engine = ProtocolEngine(
            prefix=self.prefix,
            ws_prefix=self.ws_prefix,
            ttl=ttl,
            rate_limit_per_min=rate_limit_per_min,
            store=self.store,
            validator=validator,
            mode_handlers=mode_handlers,
        )

        self._register(app, sock)
        self.store.start_cleanup_thread()

    # ── hook proxies ─────────────────────────────────────

    def on_create_session(self, fn):
        return self.engine.on_create_session(fn)

    def on_action(self, fn):
        return self.engine.on_action(fn)

    def on_extend(self, fn):
        return self.engine.on_extend(fn)

    def on_done(self, fn):
        return self.engine.on_done(fn)

    # ── optional prompt helper (application layer) ───────

    def build_prompt(self, sess, base_url, instructions=None):
        """Deprecated convenience — prefer handshake_prompt.prompt.build_prompt."""
        return build_prompt(sess, base_url, prefix=self.prefix, instructions=instructions)

    # ── Flask route registration ───────────────────────────

    def _register(self, app, sock):
        from flask import request, jsonify

        def respond(payload, code):
            if code >= 400:
                return jsonify(payload), code
            return jsonify(payload)

        @app.route(f'{self.prefix}/session', methods=['POST'])
        def _hpp_session():
            body = request.get_json(force=True, silent=True) or {}
            payload, code = self.engine.create_session(body, request)
            return respond(payload, code)

        @app.route(f'{self.prefix}/context/<sid>', methods=['GET'])
        def _hpp_context(sid):
            payload, code = self.engine.get_context(sid, request)
            return respond(payload, code)

        @app.route(f'{self.prefix}/action/<sid>', methods=['POST'])
        def _hpp_action(sid):
            body = request.get_json(force=True, silent=True) or {}
            payload, code = self.engine.post_action(sid, body, request)
            return respond(payload, code)

        @app.route(f'{self.prefix}/notify/<sid>', methods=['POST'])
        def _hpp_notify(sid):
            body = request.get_json(force=True, silent=True) or {}
            payload, code = self.engine.post_notify(
                sid, body, request, self.require_browser_auth)
            return respond(payload, code)

        @app.route(f'{self.prefix}/diff/<sid>', methods=['GET'])
        def _hpp_diff(sid):
            payload, code = self.engine.get_diff(sid, request)
            return respond(payload, code)

        @app.route(f'{self.prefix}/session/<sid>/extend', methods=['POST'])
        def _hpp_extend(sid):
            body = request.get_json(force=True, silent=True) or {}
            payload, code = self.engine.post_extend(sid, body, request)
            return respond(payload, code)

        @sock.route(f'{self.ws_prefix}/<sid>')
        def _hpp_ws(ws, sid):
            self.engine.handle_ws(ws, sid)
