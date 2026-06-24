# encoding=utf-8
"""
handshake-prompt
================

Core network component for the Handshake Prompt Protocol (HPP).

Provides session pairing, token auth, HTTP + WebSocket transport.
Application logic (form-fill, device control, etc.) plugs in via mode handlers.

Quick start (Flask)::

    from flask import Flask
    from flask_sock import Sock
    from handshake_prompt import HandshakeManager

    app = Flask(__name__)
    sock = Sock(app)
    HandshakeManager(app, sock)
"""

from .session import Session
from .store import SessionStore
from .protocol import ProtocolEngine
from .manager import HandshakeManager
from .prompt import build_prompt

__version__ = "0.2.0"
__all__ = [
    "HandshakeManager",
    "ProtocolEngine",
    "Session",
    "SessionStore",
    "build_prompt",
    "__version__",
]
