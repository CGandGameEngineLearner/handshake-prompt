# encoding=utf-8
"""
Session 仓库 - 线程安全的会话存储与清理
"""
import threading
import time

from .session import Session


class SessionStore:
    """
    内存型会话仓库。生产环境可继承并替换为 Redis 等持久化方案。
    """

    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()

    def put(self, sess: Session):
        with self._lock:
            self._sessions[sess.sid] = sess

    def get(self, sid):
        with self._lock:
            sess = self._sessions.get(sid)
        if sess and sess.is_expired():
            with self._lock:
                self._sessions.pop(sid, None)
            return None
        if sess:
            sess.touch()
        return sess

    def remove(self, sid):
        with self._lock:
            self._sessions.pop(sid, None)

    def cleanup_expired(self):
        with self._lock:
            expired = [k for k, v in self._sessions.items() if v.is_expired()]
            for k in expired:
                del self._sessions[k]
        return len(expired)

    def start_cleanup_thread(self, interval=300):
        def _loop():
            while True:
                time.sleep(interval)
                try:
                    self.cleanup_expired()
                except Exception:
                    pass
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        return t
