# encoding=utf-8
"""
ProtocolEngine — framework-agnostic HPP request handling.

This is the core network component: session lifecycle, token auth, mode dispatch.
Flask/Express/FastAPI adapters should delegate to this class.
"""
import secrets

from .auth import extract_token_from_request, extract_token_from_ws, verify_token
from .modes import get_handler
from .session import Session

EVT_CONNECTED = 'connected'
EVT_ACTION    = 'action'
EVT_DONE      = 'done'
EVT_ERROR     = 'error'


class ProtocolEngine:
    """Mode-agnostic HPP protocol engine."""

    def __init__(self, prefix='/handshake', ws_prefix='/ws/handshake',
                 ttl=1800, rate_limit_per_min=60,
                 store=None, validator=None, mode_handlers=None):
        self.prefix = prefix.rstrip('/')
        self.ws_prefix = ws_prefix.rstrip('/')
        self.ttl = ttl
        self.rate_limit_per_min = rate_limit_per_min
        self.store = store
        self.validator = validator
        self.mode_handlers = mode_handlers

        self._on_create_callbacks = []
        self._on_action_callbacks = []
        self._on_done_callbacks = []
        self._on_extend_callbacks = []

    # ── hooks ────────────────────────────────────────────

    def on_create_session(self, fn):
        self._on_create_callbacks.append(fn)
        return fn

    def on_action(self, fn):
        self._on_action_callbacks.append(fn)
        return fn

    def on_extend(self, fn):
        self._on_extend_callbacks.append(fn)
        return fn

    def on_done(self, fn):
        self._on_done_callbacks.append(fn)
        return fn

    def _handler(self, sess):
        return get_handler(sess.mode, self.mode_handlers)

    def _broadcast(self, sess):
        return sess.broadcast

    # ── endpoints ────────────────────────────────────────

    def create_session(self, body, request=None):
        mode = body.get('mode', 'default')
        meta = body.get('meta', {})

        sid = secrets.token_hex(16)
        sess = Session(
            sid=sid, mode=mode,
            schema=body.get('schema'),
            context=body.get('context'),
            ttl=self.ttl,
            rate_limit_per_min=self.rate_limit_per_min,
            meta=meta,
            validator=self.validator,
        )
        self._handler(sess).setup_session(sess, body)

        for cb in self._on_create_callbacks:
            try:
                cb(sess, request)
            except Exception as e:
                return {'error': str(e)}, 403

        self.store.put(sess)
        prefix = self.prefix
        return {
            'sessionId':  sid,
            'token':      sess.token,
            'wsUrl':      f'{self.ws_prefix}/{sid}',
            'contextUrl': f'{prefix}/context/{sid}',
            'actionUrl':  f'{prefix}/action/{sid}',
            'diffUrl':    f'{prefix}/diff/{sid}',
            'notifyUrl':  f'{prefix}/notify/{sid}',
            'expiresIn':  self.ttl,
        }, 200

    def get_context(self, sid, request):
        sess = self.store.get(sid)
        if not sess:
            return {'error': 'session not found or expired'}, 404
        if not verify_token(sess, extract_token_from_request(request)):
            return {'error': 'invalid token'}, 403
        if not sess.check_rate_limit():
            return {'error': 'rate limit exceeded'}, 429
        return self._handler(sess).context_response(sess), 200

    def post_action(self, sid, body, request):
        sess = self.store.get(sid)
        if not sess:
            return {'error': 'session not found or expired'}, 404
        if not verify_token(sess, extract_token_from_request(request)):
            return {'error': 'invalid token'}, 403
        if not sess.check_rate_limit():
            return {'error': 'rate limit exceeded'}, 429

        actions  = body.get('actions', [])
        stream   = body.get('stream', True)
        interval = max(0, body.get('intervalMs', 300)) / 1000.0
        handler  = self._handler(sess)

        wrapped_cbs = [lambda s, a, r, _cb=cb: _cb(s, a, request)
                       for cb in self._on_action_callbacks]

        applied, rejected, errors, extra = handler.process_actions(
            sess, actions, stream, interval,
            wrapped_cbs,
            self._broadcast(sess),
        )

        missing = extra.get('missing', [])
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

        result = {
            'ok':       True,
            'applied':  applied,
            'rejected': rejected,
            'errors':   errors,
        }
        result.update(extra)
        return result, 200

    def post_notify(self, sid, body, request, browser_auth=None):
        sess = self.store.get(sid)
        if not sess:
            return {'error': 'session not found or expired'}, 404
        if browser_auth is not None and not browser_auth(request, sess):
            return {'error': 'browser auth failed'}, 403

        key = body.get('key')
        value = body.get('value')
        if key is None:
            return {'error': 'key is required'}, 400

        self._handler(sess).process_notify(sess, key, value)
        return {'ok': True}, 200

    def get_diff(self, sid, request):
        sess = self.store.get(sid)
        if not sess:
            return {'error': 'session not found or expired'}, 404
        if not verify_token(sess, extract_token_from_request(request)):
            return {'error': 'invalid token'}, 403
        if not sess.check_rate_limit():
            return {'error': 'rate limit exceeded'}, 429

        since = request.args.get('since', '')
        changes = sess.get_diff_since(since) if since else sess.changes[-50:]
        return {'sessionId': sid, 'since': since, 'changes': changes}, 200

    def post_extend(self, sid, body, request):
        sess = self.store.get(sid)
        if not sess:
            return {'error': 'session not found or expired'}, 404
        if not verify_token(sess, extract_token_from_request(request)):
            return {'error': 'invalid token'}, 403

        extra = int(body.get('extraSeconds', 1800))
        if extra <= 0 or extra > 86400:
            return {'error': 'extraSeconds must be between 1 and 86400'}, 400

        for cb in self._on_extend_callbacks:
            try:
                result = cb(sess, extra, request)
                if result is False:
                    return {'error': 'extension denied by server policy'}, 403
                if isinstance(result, int) and result > 0:
                    extra = result
            except Exception as e:
                return {'error': str(e)}, 403

        new_expires = sess.extend(extra)
        sess.broadcast({'type': 'extended', 'expiresIn': new_expires})
        return {'ok': True, 'extended': extra, 'expiresIn': new_expires}, 200

    def handle_ws(self, ws, sid):
        import json

        sess = self.store.get(sid)
        if not sess:
            ws.send(json.dumps({'type': EVT_ERROR, 'msg': 'session not found'}))
            ws.close()
            return

        token = extract_token_from_ws(ws)
        if not verify_token(sess, token):
            ws.send(json.dumps({'type': EVT_ERROR, 'msg': 'invalid token'}))
            ws.close()
            return

        sess.ws_clients.add(ws)
        ws.send(json.dumps({
            'type':      EVT_CONNECTED,
            'sessionId': sid,
            'mode':      sess.mode,
        }))

        handler = self._handler(sess)
        try:
            while True:
                raw = ws.receive(timeout=60)
                if raw is None:
                    break
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                handler.process_ws_message(sess, msg)
        except Exception:
            pass
        finally:
            sess.ws_clients.discard(ws)
