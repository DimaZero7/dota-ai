"""Local analyst file exchange; never calls a paid model or fetches new matches."""
import argparse
import json
from pathlib import Path
from .synthesis import prepare_analysis, accept_analysis, read_analysis, validate_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'accept', 'show', 'check'])
    parser.add_argument('--store', type=Path, default=Path('data/analysis/synthesis/current'))
    parser.add_argument('--node')
    parser.add_argument('--level', type=int)
    parser.add_argument('--children', nargs='+')
    parser.add_argument('--question', default='Explain this player from the child analyses; include contradictions.')
    parser.add_argument('--packet', type=Path)
    parser.add_argument('--response', type=Path)
    parser.add_argument('--verify-sources', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            if args.node is None or args.level is None or not args.children:
                raise ValueError('--node, --level and --children required')
            result = prepare_analysis(store=args.store, node_id=args.node, level=args.level,
                                      child_ids=args.children, question=args.question)
        elif args.command == 'accept':
            if args.packet is None or args.response is None:
                raise ValueError('--packet and --response required')
            result = accept_analysis(store=args.store,
                packet=json.loads(args.packet.read_text(encoding='utf-8')),
                response=json.loads(args.response.read_text(encoding='utf-8')))
        else:
            if args.node is None:
                raise ValueError('--node required')
            result = (read_analysis(store=args.store, node_id=args.node) if args.command == 'show'
                      else validate_analysis(store=args.store, node_id=args.node,
                                             root=Path.cwd() if args.verify_sources else None))
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Synthesis failed: {exc}'); return 1


if __name__ == '__main__':
    raise SystemExit(main())
