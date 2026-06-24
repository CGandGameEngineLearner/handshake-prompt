# encoding=utf-8
"""
handshake-prompt
================

Server-side SDK for the Handshake Prompt Protocol (HPP).

A lightweight protocol that lets users grant any AI Agent access to a web
service via a single copy-paste of a "handshake prompt". No API keys, no MCP
servers, no environment variables required for the end user.

Quick start (Flask)::

    from flask import Flask
    from flask_sock import Sock
    from handshake_prompt import HandshakeManager

    app = Flask(__name__)
    sock = Sock(app)
    hm = HandshakeManager(app, sock)
"""

from .session import Session
from .manager import HandshakeManager

__version__ = "0.1.2"
__all__ = ["HandshakeManager", "Session", "__version__"]
