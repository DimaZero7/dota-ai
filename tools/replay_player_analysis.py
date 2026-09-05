"""Reproduce the reviewed ten-match example offline; never generate an interpretation."""
import argparse
import json
from pathlib import Path
from src.apps.analysis.dossiers import prepare_match_dossiers
from src.apps.analysis.pipeline import run_match
from src.apps.analysis.synthesis import prepare_analysis, accept_analysis, validate_analysis
from src.apps.analysis.match_review import prepare_match_review, accept_match_review


def replay(*, root: Path, store: Path) -> dict:
    base=root/'data/prototype/synthesis'
    selection=json.loads((base/'selection.json').read_text(encoding='utf-8'))
    run=json.loads((base/'run.json').read_text(encoding='utf-8'))
    if len(selection['lower_outputs'])!=10:
        raise ValueError('This saved example requires exactly its original ten matches')
    for key,path in selection['lower_outputs'].items():
        lower=root/path
        if not (lower/'manifest.json').exists():
            _,lower,_=run_match(root=root,match_id=int(key),account_id=selection['account_id'])
        prepare_match_dossiers(root=root,store=store,lower_output=lower,match_id=int(key),
            account_id=selection['account_id'],critical_interval=selection['critical_intervals'][key])
    responses={}
    for file in {r['file'] for r in run['recipes']}:
        for row in json.loads((base/file).read_text(encoding='utf-8')):
            responses[row['id']]=row['response']
    usage=[]
    for recipe in run['recipes']:
        packet=prepare_analysis(store=store,**{k:recipe[k] for k in ('level','child_ids','question','budget_bytes')},node_id=recipe['id'])
        if packet['packet_id']!=recipe['packet_id']:
            raise ValueError(f"Inputs changed for {recipe['id']}; a new analyst review is required")
        accept_analysis(store=store,packet=packet,response=responses[recipe['id']])
        usage.append(packet['usage']['input_utf8_bytes'])
    application=json.loads((base/'match-review.json').read_text(encoding='utf-8'))
    packet=prepare_match_review(store=store,**application['request'])
    if packet['packet_id']!=application['packet_id']:
        raise ValueError('Application inputs changed; new review required')
    accept_match_review(store=store,packet=packet,response=application['response'])
    main=validate_analysis(store=store,node_id=run['profile_id'],root=root)
    baseline=validate_analysis(store=store,node_id=run['baseline_profile_id'],root=root)
    if set(baseline['match_ids']) & set(application['target_match_ids']):
        raise ValueError('Target leaked into baseline evidence')
    return {'main_profile':main,'baseline_profile':baseline,'analyst_reviews_replayed':len(usage),
            'input_bytes_min':min(usage),'input_bytes_max':max(usage),'input_limit_bytes':32000,
            'application_input_bytes':packet['usage']['input_utf8_bytes'],
            'measured_model_tokens':None,'new_matches_fetched':0,'meta_applied':False,
            'semantic_validation':'Analyst critique, not automatically proven truth or blind evaluation.',
            'source_layer':'L0 original response references under L1 nodes',
            'progress':'Training not yet evaluated on future games.'}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--store',type=Path,default=Path('data/analysis/synthesis/current'))
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    try:
        result=replay(root=Path.cwd(),store=args.store)
        body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(body,encoding='utf-8')
        print(body);return 0
    except (OSError,ValueError,KeyError) as exc:
        print(f'Replay failed: {exc}');return 1


if __name__=='__main__':raise SystemExit(main())
