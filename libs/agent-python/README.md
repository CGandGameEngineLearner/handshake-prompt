# handshake-prompt-agent

> Agent-side SDK + CLI for the **Handshake Prompt Protocol (HPP)**.
> Zero external dependencies (Python stdlib only).

## Install

```bash
pip install handshake-prompt-agent
```

## CLI

```bash
# Extract credentials from a handshake prompt
handshake-prompt-agent parse-prompt --prompt "$(pbpaste)"

# Get current schema + values
handshake-prompt-agent get-context --sid <sid> --token <token> --base <url>

# Submit field values
handshake-prompt-agent action --sid <sid> --token <token> --base <url> \
    --data '{"name":"Alice","age":30}'

# Get incremental changes since last submit
handshake-prompt-agent get-diff --sid <sid> --token <token> --base <url> \
    --since "2026-06-23T10:22:00+08:00"
```

## Programmatic API

```python
from handshake_prompt_agent import HandshakeAgent, parse_prompt

# Parse user-pasted prompt
creds = parse_prompt(prompt_text)
agent = HandshakeAgent(
    sid=creds['sessionId'],
    token=creds['token'],
    base_url=creds['baseUrl'],
)

# Read current state (call this BEFORE every action!)
state = agent.get_context()
print(state['schema'])     # field definitions
print(state['context'])    # current values + who filled (user/ai/empty/user_edit)
print(state['missing'])    # required-but-empty keys

# Apply values
result = agent.action({
    'name':  'Alice',
    'email': 'alice@example.com',
    'age':   30,
})
print(result['applied'])   # fields successfully written
print(result['rejected'])  # fields blocked (e.g. user already filled)
print(result['context'])   # full state snapshot after the action
```

## Skill integration

This package is intended to be used inside an Agent **skill** (e.g.
Codemaker, Claude, Cursor). A typical skill file:

```markdown
# my-handshake-skill SKILL.md

Triggered when user pastes a message containing `sessionId:` and `token:`.

Workflow:
1. parse-prompt to extract credentials
2. get-context to read current schema + values
3. reason out field values based on user's request
4. action to submit values

Always call get-context BEFORE each action to see latest state
(user may have edited fields manually).
```

## License

MIT
