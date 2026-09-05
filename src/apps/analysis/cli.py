"""Thin local CLI with explicit collection and model file exchange."""
import argparse
import json
import re
from pathlib import Path
from dataclasses import asdict
from src.settings import BASE_DIR,config_toml
from .pipeline import run_match
from .series import run_series
from .context import make_packet,ContextBudget
from .sources import load_sources
from .retrieval import DrillSession,query_events
from .review import save_review
from .sampling import collect_sample,save
from .evidence import digest


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['build','sample','series','packet','detail','import-review'])
    parser.add_argument('--match-id',type=int,default=8960626424)
    parser.add_argument('--total',type=int,default=5)
    parser.add_argument('--series',action='store_true')
    parser.add_argument('--finding')
    parser.add_argument('--question',default='Describe what is supported, uncertain and worth inspecting; no meta.')
    parser.add_argument('--focus-match-ids',nargs='+',type=int)
    parser.add_argument('--budget-bytes',type=int,default=24000)
    parser.add_argument('--start',type=float); parser.add_argument('--end',type=float)
    parser.add_argument('--slot',type=int); parser.add_argument('--kinds'); parser.add_argument('--fields')
    parser.add_argument('--offset',type=int,default=0)
    parser.add_argument('--session',default='review')
    parser.add_argument('--packet',type=Path); parser.add_argument('--response',type=Path)
    args=parser.parse_args(); root=BASE_DIR.parent; account=config_toml['player']['account_id']
    try:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',args.session):
            raise ValueError('Session name must contain 1..64 letters, digits, underscores or hyphens')
        state_path=root/'data/analysis/drills'/f'{args.session}.json'
        if args.command=='sample':
            data=collect_sample(root=root,account_id=account,token=config_toml['stratz']['token'],total=args.total)
            print(json.dumps({'match_ids':[r['match_id'] for r in data['matches']]})); return 0
        if args.command=='import-review':
            if args.packet is None or args.response is None:
                raise ValueError('--packet and --response required')
            state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
            response=json.loads(args.response.read_text(encoding='utf-8'))
            output=root/'data/analysis/reviews'/f'{args.session}-{digest(response)[:16]}.review.json'
            output.parent.mkdir(parents=True,exist_ok=True)
            save_review(packet_path=args.packet,response=response,output_path=output,
                        extra_ids=set(state.get('session',{}).get('evidence_ids',[])))
            print(json.dumps({'review':str(output)})); return 0
        if args.command=='series' or args.series:
            data,output=run_series(root=root,account_id=account); reused=None
        else:
            data,output,reused=run_match(root=root,match_id=args.match_id,account_id=account)
        if args.command=='packet':
            finding=data['registry'][args.finding or data.get('profile_id',data.get('match_finding'))]
            children=[data['registry'][k] for k in finding.get('children',[]) if k in data['registry']]
            bundle=make_packet(finding=finding,question=args.question,budget=ContextBudget(total=args.budget_bytes),
                               child_findings=children if finding['level']<5 else [],focus_match_ids=args.focus_match_ids)
            path=output/f"packet-{bundle['packet']['packet_id']}.json"; save(path,bundle)
            print(json.dumps({'packet':str(path),'usage':bundle['usage']},ensure_ascii=False))
        elif args.command=='detail':
            if args.series or args.start is None or args.end is None:
                raise ValueError('Detail requires one --match-id, --start and --end')
            source_version=output.name
            state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
            versions=state.get('source_versions',{})
            if str(args.match_id) in versions and versions[str(args.match_id)]!=source_version:
                raise ValueError('Sources/rules changed; use a new review session')
            session=DrillSession(**state['session']) if state else DrillSession()
            sources=load_sources(root=root,match_id=args.match_id,account_id=account)
            query={'start':args.start,'end':args.end,'slot':args.slot,'kinds':args.kinds.split(',') if args.kinds else None,
                   'fields':args.fields.split(',') if args.fields else None,'offset':args.offset}
            result=session.request(lambda:query_events(sources=sources,facts=data['facts'],**query),query)
            versions[str(args.match_id)]=source_version
            save(state_path,{'source_versions':versions,'session':asdict(session)})
            path=state_path.with_name(f'{args.session}-detail-{session.calls}.json'); save(path,result)
            print(json.dumps({'detail':str(path),'calls':session.calls,'used_bytes':session.used_bytes,'pending':session.pending}))
        else:
            print(json.dumps({'output':str(output),'cache_hit':reused,'trace':data.get('trace'),
                              'episodes':data.get('episode_counts'),
                              'status':'measurements_ready; analyst synthesis required',
                              'personal_profile':'Use src.apps.analysis.synthesis_cli; legacy numeric profile is not a player report.'},ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print(f'Analysis failed: {exc}'); return 1


if __name__=='__main__':
    raise SystemExit(main())
