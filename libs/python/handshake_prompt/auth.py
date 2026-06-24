# encoding=utf-8
"""Token extraction and verification for HPP."""
import secrets


def extract_token_from_request(request):
    """Read token from X-Handshake-Token header or ?token= query param."""
    return request.headers.get('X-Handshake-Token') or request.args.get('token')


def extract_token_from_ws(ws):
    """Read token from WebSocket query string."""
    query = ws.environ.get('QUERY_STRING', '')
    for part in query.split('&'):
        if part.startswith('token='):
            return part[6:]
    return ''


def verify_token(sess, token):
    """Timing-safe token comparison."""
    if not token:
        return False
    return secrets.compare_digest(token, sess.token)
