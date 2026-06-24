# encoding=utf-8
"""
Optional prompt text builder — application-layer utility, not part of core transport.

Services may use this helper or generate their own handshake prompt format.
"""


def build_prompt(sess, base_url, prefix='/handshake', instructions=None):
    """
    Generate a standard handshake prompt text block.

    This is a convenience helper for services that want a default template.
  Core HPP only requires returning sessionId + token from POST /session.
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
        f"1. GET  {base_url.rstrip('/')}{prefix}/context/{sess.sid}   (header X-Handshake-Token: <token>)",
        f"2. POST {base_url.rstrip('/')}{prefix}/action/{sess.sid}    {{\"actions\":[{{\"type\":\"set\",\"key\":...,\"value\":...}}]}}",
        f"3. POST {base_url.rstrip('/')}{prefix}/session/{sess.sid}/extend  {{\"extraSeconds\":1800}}  (optional)",
        "",
        "## Security Notes",
        f"- Token expires in {sess.expires_in()} seconds by default",
        "- Do NOT forward this prompt to others",
        "",
        "## Waiting for user's request...",
    ]
    return "\n".join(lines)
