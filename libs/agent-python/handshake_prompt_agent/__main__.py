# encoding=utf-8
"""
CLI entry point: handshake-prompt-agent
"""
import argparse
import json
import sys

from .client import HandshakeAgent, HPPError, parse_prompt


def _dump(obj):
    """Pretty + machine-readable output."""
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_get_context(args):
    agent = HandshakeAgent(args.sid, args.token, args.base)
    _dump(agent.get_context())


def cmd_action(args):
    try:
        values = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f'--data is not valid JSON: {e}', file=sys.stderr)
        sys.exit(2)
    if not isinstance(values, dict):
        print('--data must be a JSON object {key: value}', file=sys.stderr)
        sys.exit(2)

    agent = HandshakeAgent(args.sid, args.token, args.base)
    _dump(agent.action(values, stream=not args.no_stream,
                       interval_ms=args.interval))


def cmd_get_diff(args):
    agent = HandshakeAgent(args.sid, args.token, args.base)
    _dump(agent.get_diff(since=args.since))


def cmd_parse_prompt(args):
    text = args.prompt if args.prompt else sys.stdin.read()
    _dump(parse_prompt(text))


def main():
    parser = argparse.ArgumentParser(
        prog='handshake-prompt-agent',
        description='Agent-side client for the Handshake Prompt Protocol',
    )
    sub = parser.add_subparsers(dest='cmd', required=True)

    # get-context
    p = sub.add_parser('get-context', help='Fetch schema + current values')
    p.add_argument('--sid', required=True)
    p.add_argument('--token', required=True)
    p.add_argument('--base', required=True, help='base URL of the service')
    p.set_defaults(func=cmd_get_context)

    # action
    p = sub.add_parser('action', help='Submit field values')
    p.add_argument('--sid', required=True)
    p.add_argument('--token', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--data', required=True, help='JSON object {key: value}')
    p.add_argument('--no-stream', action='store_true',
                   help='disable streaming push to browser')
    p.add_argument('--interval', type=int, default=300,
                   help='ms between streaming pushes (default 300)')
    p.set_defaults(func=cmd_action)

    # get-diff
    p = sub.add_parser('get-diff', help='Fetch incremental changes')
    p.add_argument('--sid', required=True)
    p.add_argument('--token', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--since', default='', help='ISO timestamp')
    p.set_defaults(func=cmd_get_diff)

    # parse-prompt
    p = sub.add_parser('parse-prompt',
                       help='Parse a handshake prompt and extract credentials')
    p.add_argument('--prompt', default='', help='prompt text (default: stdin)')
    p.set_defaults(func=cmd_parse_prompt)

    args = parser.parse_args()
    try:
        args.func(args)
    except HPPError as e:
        print(f'[error] {e}', file=sys.stderr)
        if e.body:
            print(json.dumps(e.body, ensure_ascii=False, indent=2),
                  file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f'[error] {e}', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
