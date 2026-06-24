# encoding=utf-8
"""
HandshakeManager - 把 HPP 协议集成到 Flask 应用
"""
import json
import secrets
import time

from .session import Session
from .store import SessionStore


# WebSocket 客户端的协议事件名称
EVT_CONNECTED = 'connected'
EVT_ACTION    = 'action'
EVT_DONE      = 'done'
EVT_ERROR     = 'error'


class HandshakeManager:
    """
    将 HPP 注册到 Flask app + flask_sock 实例。

    使用：

        from flask import Flask
        from flask_sock import Sock
        from handshake_prompt import HandshakeManager

        app = Flask(__name__)
        sock = Sock(app)
        hm = HandshakeManager(app, sock)

        # 可选：通过钩子绑定业务身份
        @hm.on_create_session
        def bind_owner(sess, request):
            sess.owner = session.get('user_id')   # Flask session

    路由（默认 prefix='/handshake'）：
        POST  /handshake/session         创建会话
        GET   /handshake/context/<sid>   Agent 读取上下文（需 token）
        POST  /handshake/action/<sid>    Agent 执行操作（需 token）
        POST  /handshake/notify/<sid>    浏览器通知用户编辑（需 session 鉴权）
        GET   /handshake/diff/<sid>      Agent 增量变更（需 token）
        WS    /ws/handshake/<sid>        实时推送通道（需 token）
    """

    def __init__(self, app, sock, prefix='/handshake', ws_prefix='/ws/handshake',
                 ttl=1800, rate_limit_per_min=60,
                 store=None, validator=None,
                 require_browser_auth=None):
        self.app = app
        self.sock = sock
        self.prefix = prefix.rstrip('/')
        self.ws_prefix = ws_prefix.rstrip('/')
        self.ttl = ttl
        self.rate_limit_per_min = rate_limit_per_min
        self.store = store or SessionStore()
        self.validator = validator
        self.require_browser_auth = require_browser_auth   # callable(request) -> bool

        # 钩子
        self._on_create_callbacks = []
        self._on_action_callbacks = []
        self._on_done_callbacks = []

        self._register(app, sock)
        self.store.start_cleanup_thread()

    # ── 钩子注册 ──────────────────────────────────────────

    def on_create_session(self, fn):
        """装饰器：会话创建时调用 fn(session, request)"""
        self._on_create_callbacks.append(fn)
        return fn

    def on_action(self, fn):
        """装饰器：Agent 提交 action 时调用 fn(session, action, request)"""
        self._on_action_callbacks.append(fn)
        return fn

    def on_done(self, fn):
        """装饰器：单次 action 批次完成后调用 fn(session, applied, rejected, errors)"""
        self._on_done_callbacks.append(fn)
        return fn

    # ── 工具 ────────────────────────────────────────────

    @staticmethod
    def _check_token(sess, request):
        token = request.headers.get('X-Handshake-Token') or request.args.get('token')
        if not token:
            return False
        return secrets.compare_digest(token, sess.token)

    @staticmethod
    def _parse_ws_token(ws):
        query = ws.environ.get('QUERY_STRING', '')
        for part in query.split('&'):
            if part.startswith('token='):
                return part[6:]
        return ''

    def build_prompt(self, sess, base_url, instructions=None):
        """
        生成标准格式的握手提示词。
        服务可调用此方法或自行实现，下方提供默认模板。
        """
        lines = [
            f"# Handshake Prompt - {sess.mode}",
            "",
            "## Credentials",
            f"- sessionId: {sess.sid}",
            f"- token: {sess.token}",
            f"- baseUrl: {base_url}",
            f"- mode: {sess.mode}",
            f"- expiresIn: {sess.expires_in()}s",
            "",
        ]
        if instructions:
            lines += ["## Instructions", instructions, ""]
        lines += [
            "## Usage",
            "1. GET  {base}/handshake/context/{sid}   (header X-Handshake-Token: <token>)",
            "2. POST {base}/handshake/action/{sid}    {\"actions\":[{\"type\":\"set\",\"key\":...,\"value\":...}]}",
            "",
            "## Security Notes",
            "- This token is single-use and expires in 30 minutes",
            "- Do NOT forward this prompt to others",
            "- The server will reject any AI attempt to overwrite user-filled fields",
            "",
            "## Waiting for user's request...",
        ]
        return "\n".join(lines)

    # ── 路由注册 ─────────────────────────────────────────

    def _register(self, app, sock):
        from flask import request, jsonify

        prefix = self.prefix

        def err(msg, code=400):
            return jsonify({'error': msg}), code

        # POST /session
        @app.route(f'{prefix}/session', methods=['POST'])
        def _hpp_session():
            body = request.get_json(force=True, silent=True) or {}
            mode    = body.get('mode', 'default')
            schema  = body.get('schema', [])
            context = body.get('context', {})
            meta    = body.get('meta', {})

            sid = secrets.token_hex(16)    # 128bit
            sess = Session(
                sid=sid, mode=mode, schema=schema, context=context,
                ttl=self.ttl,
                rate_limit_per_min=self.rate_limit_per_min,
                meta=meta,
                validator=self.validator,
            )
            # 钩子可写入 owner / 校验权限等
            for cb in self._on_create_callbacks:
                try:
                    cb(sess, request)
                except Exception as e:
                    return err(str(e), 403)

            self.store.put(sess)

            return jsonify({
                'sessionId':  sid,
                'token':      sess.token,
                'wsUrl':      f'{self.ws_prefix}/{sid}',
                'contextUrl': f'{prefix}/context/{sid}',
                'actionUrl':  f'{prefix}/action/{sid}',
                'diffUrl':    f'{prefix}/diff/{sid}',
                'notifyUrl':  f'{prefix}/notify/{sid}',
                'expiresIn':  self.ttl,
            })

        # GET /context/<sid>
        @app.route(f'{prefix}/context/<sid>', methods=['GET'])
        def _hpp_context(sid):
            sess = self.store.get(sid)
            if not sess:
                return err('session not found or expired', 404)
            if not self._check_token(sess, request):
                return err('invalid token', 403)
            if not sess.check_rate_limit():
                return err('rate limit exceeded', 429)
            return jsonify(sess.to_dict())

        # POST /action/<sid>
        @app.route(f'{prefix}/action/<sid>', methods=['POST'])
        def _hpp_action(sid):
            sess = self.store.get(sid)
            if not sess:
                return err('session not found or expired', 404)
            if not self._check_token(sess, request):
                return err('invalid token', 403)
            if not sess.check_rate_limit():
                return err('rate limit exceeded', 429)

            body     = request.get_json(force=True, silent=True) or {}
            actions  = body.get('actions', [])
            stream   = body.get('stream', True)
            interval = max(0, body.get('intervalMs', 300)) / 1000.0

            applied  = []
            rejected = []
            errors   = []

            for act in actions:
                if act.get('type') != 'set':
                    errors.append({'action': act, 'msg': 'unsupported action type'})
                    continue
                key   = act.get('key')
                value = act.get('value')
                if key is None:
                    errors.append({'action': act, 'msg': 'missing key'})
                    continue

                # 钩子：业务可以拒绝某个 action
                veto = False
                for cb in self._on_action_callbacks:
                    try:
                        result = cb(sess, act, request)
                        if result is False:
                            veto = True
                            break
                    except Exception as e:
                        errors.append({'key': key, 'msg': str(e)})
                        veto = True
                        break
                if veto:
                    rejected.append(key)
                    continue

                # schema 类型校验
                ok, msg = sess.validate_value(key, value)
                if not ok:
                    errors.append({'key': key, 'msg': msg})
                    continue

                # 写入（AI 不得覆盖用户字段）
                ok = sess.set_value(key, value, 'ai')
                if not ok:
                    rejected.append(key)
                    continue

                applied.append(key)
                if stream:
                    sess.broadcast({'type': EVT_ACTION, 'key': key, 'value': value})
                    if interval > 0:
                        time.sleep(interval)

            missing = sess.get_missing()
            sess.broadcast({
                'type':     EVT_DONE,
                'applied':  len(applied),
                'rejected': rejected,
                'missing':  missing,
            })

            for cb in self._on_done_callbacks:
                try:
                    cb(sess, applied, rejected, errors)
                except Exception:
                    pass

            return jsonify({
                'ok':       True,
                'applied':  applied,
                'rejected': rejected,
                'errors':   errors,
                'missing':  missing,
                'context':  sess.get_context(),
            })

        # POST /notify/<sid>
        @app.route(f'{prefix}/notify/<sid>', methods=['POST'])
        def _hpp_notify(sid):
            sess = self.store.get(sid)
            if not sess:
                return err('session not found or expired', 404)
            # 浏览器身份校验（可选 hook）
            if self.require_browser_auth is not None:
                if not self.require_browser_auth(request, sess):
                    return err('browser auth failed', 403)
            body  = request.get_json(force=True, silent=True) or {}
            key   = body.get('key')
            value = body.get('value')
            if key is None:
                return err('key is required')
            sess.set_value(key, value, 'user')
            return jsonify({'ok': True})

        # GET /diff/<sid>
        @app.route(f'{prefix}/diff/<sid>', methods=['GET'])
        def _hpp_diff(sid):
            sess = self.store.get(sid)
            if not sess:
                return err('session not found or expired', 404)
            if not self._check_token(sess, request):
                return err('invalid token', 403)
            if not sess.check_rate_limit():
                return err('rate limit exceeded', 429)
            since = request.args.get('since', '')
            changes = sess.get_diff_since(since) if since else sess.changes[-50:]
            return jsonify({'sessionId': sid, 'since': since, 'changes': changes})

        # WS /ws/handshake/<sid>
        @sock.route(f'{self.ws_prefix}/<sid>')
        def _hpp_ws(ws, sid):
            sess = self.store.get(sid)
            if not sess:
                ws.send(json.dumps({'type': EVT_ERROR, 'msg': 'session not found'}))
                ws.close()
                return

            token = self._parse_ws_token(ws)
            if not token or not secrets.compare_digest(token, sess.token):
                ws.send(json.dumps({'type': EVT_ERROR, 'msg': 'invalid token'}))
                ws.close()
                return

            sess.ws_clients.add(ws)
            ws.send(json.dumps({
                'type':      EVT_CONNECTED,
                'sessionId': sid,
                'mode':      sess.mode,
            }))

            try:
                while True:
                    raw = ws.receive(timeout=60)
                    if raw is None:
                        break
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if msg.get('type') == 'userEdit':
                        key   = msg.get('key')
                        value = msg.get('value')
                        if key is not None:
                            sess.set_value(key, value, 'user')
            except Exception:
                pass
            finally:
                sess.ws_clients.discard(ws)
