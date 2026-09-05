"""Build local numeric artifacts or exchange one optional episode review."""
import argparse
import json
from pathlib import Path

from .services import build_numeric_match_from_sources
from .interpretation import prepare_numeric_review, accept_numeric_review
from .storage import write_json


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('build');build.add_argument('--match-id',type=int);build.add_argument('--all',action='store_true')
    build.add_argument('--output-root',type=Path);build.add_argument('--summary',type=Path)
    prep=sub.add_parser('prepare-review');prep.add_argument('--directory',type=Path,required=True)
    prep.add_argument('--episode',required=True);prep.add_argument('--question',required=True)
    prep.add_argument('--store',type=Path,default=Path('data/analysis/numeric-reviews'))
    accept=sub.add_parser('accept-review');accept.add_argument('--directory',type=Path,required=True)
    accept.add_argument('--packet',type=Path,required=True);accept.add_argument('--response',type=Path,required=True)
    accept.add_argument('--store',type=Path,default=Path('data/analysis/numeric-reviews'))
    args=parser.parse_args();root=Path.cwd()
    if args.command=='build':
        if args.all==bool(args.match_id):parser.error('Choose exactly one of --all or --match-id')
        selection=json.loads((root/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
        ids=[int(k) for k in selection['lower_outputs']] if args.all else [args.match_id]
        results=[]
        for mid in ids:
            result=build_numeric_match_from_sources(root=root,match_id=mid,account_id=selection['account_id'],output_root=args.output_root)
            summary={'match_id':mid,'directory':result['directory'],'cache_hit':result['cache_hit'],
                     'revision':result['match']['revision'],'level4_bytes':len(json.dumps(result['match'],ensure_ascii=False,separators=(',',':')).encode())}
            results.append(summary);print(json.dumps(summary),flush=True)
        if args.summary:write_json(args.summary,{'matches':results,'new_matches_fetched':0,'meta_applied':False})
    elif args.command=='prepare-review':
        packet=prepare_numeric_review(root=root,directory=args.directory,episode_id=args.episode,question=args.question,store=args.store)
        print(json.dumps({'packet_id':packet['packet_id'],'file':str(args.store/'packets'/f"{packet['packet_id']}.json")}))
    else:
        record=accept_numeric_review(root=root,directory=args.directory,store=args.store,
            packet=json.loads(args.packet.read_text(encoding='utf-8')),response=json.loads(args.response.read_text(encoding='utf-8')))
        print(json.dumps({'revision':record['revision'],'semantic_truth_validated':False}))


if __name__=='__main__':
    try:
        main()
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(f'Numeric analysis failed: {error}') from error
