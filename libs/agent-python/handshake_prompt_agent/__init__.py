# encoding=utf-8
"""
handshake-prompt-agent
======================

Agent-side SDK for the Handshake Prompt Protocol (HPP).

Usage (programmatic)::

    from handshake_prompt_agent import HandshakeAgent

    agent = HandshakeAgent(sid="...", token="...", base_url="https://...")
    ctx = agent.get_context()        # returns schema + current values
    agent.action({"name": "Alice", "age": 30})

Usage (CLI)::

    handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>
    handshake-prompt-agent action      --sid <sid> --token <token> --base <url> --data '{...}'
    handshake-prompt-agent get-diff    --sid <sid> --token <token> --base <url>
    handshake-prompt-agent parse-prompt --prompt 'paste-the-handshake-prompt-here'
"""
from .client import HandshakeAgent, parse_prompt

__version__ = "0.1.0"
__all__ = ["HandshakeAgent", "parse_prompt", "__version__"]
