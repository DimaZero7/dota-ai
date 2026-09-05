"""Local analysis CLI; never starts model/API requests implicitly."""
import argparse
import json
from src.settings import BASE_DIR, config_toml
from .pipeline import run_match
from .context import make_packet, ContextBudget


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['build','packet'])
    parser.add_argument('--match-id',type=int,default=8960626424)
    parser.add_argument('--finding')
    parser.add_argument('--question',default='Describe what is supported, uncertain and worth inspecting; no meta.')
    args=parser.parse_args()
    try:
        data,output,reused=run_match(root=BASE_DIR.parent,match_id=args.match_id,account_id=config_toml['player']['account_id'])
        if args.command=='packet':
            finding=data['registry'][args.finding or data['match_finding']]
            children=[data['registry'][k] for k in finding.get('children',[]) if k in data['registry']]
            packet=make_packet(finding=finding,question=args.question,budget=ContextBudget(),child_findings=children)
            path=output/f"packet-{packet['packet']['packet_id']}.json"
            path.write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'packet':str(path),'usage':packet['usage']},ensure_ascii=False))
        else:
            print(json.dumps({'output':str(output),'cache_hit':reused,'episodes':data['episode_counts'],
                              'coverage':data['coverage']},ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print(f'Analysis failed: {exc}')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
