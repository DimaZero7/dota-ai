"""Offline prepare → optional drill → authored JSON → accept workflow."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from ..cumulative.schemas import encode
from .services import prepare, accept_profile, read_profile
from .retrieval import drill, accept_lower
from .comparison import prepare_match, accept_match
from .storage import audit
from .reports import render_profile


def main() -> int:
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--contract',required=True);p.add_argument('--question',required=True)
    p.add_argument('--metric',action='append');p.add_argument('--budget',type=int,default=32000)
    p=sub.add_parser('drill');p.add_argument('--session',required=True);p.add_argument('--kind',choices=['group','match','phase','episode'],required=True)
    p.add_argument('--target',required=True);p.add_argument('--reason',required=True);p.add_argument('--metric',default='death_fraction')
    p.add_argument('--selector');p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--registry',type=Path)
    for name in ('accept-profile','accept-lower','accept-match'):
        p=sub.add_parser(name);p.add_argument('--session',required=True);p.add_argument('--response',type=Path,required=True)
        if name=='accept-lower':p.add_argument('--ref',required=True)
    p=sub.add_parser('profile');p.add_argument('--contract',required=True);p.add_argument('--revision')
    p=sub.add_parser('report');p.add_argument('--contract',required=True);p.add_argument('--revision');p.add_argument('--language',choices=['ru','en'],default='ru')
    p=sub.add_parser('audit');p.add_argument('--session',required=True)
    p=sub.add_parser('match');p.add_argument('--contract',required=True);p.add_argument('--match-id',type=int,required=True)
    p.add_argument('--question',required=True);p.add_argument('--mode',choices=['past_only','retrospective','forecast'],default='past_only')
    args=parser.parse_args()
    try:
        if args.command=='prepare':result=prepare(path=args.db,contract_id=args.contract,question=args.question,metrics=args.metric,budget=args.budget)
        elif args.command=='drill':
            registry={int(k):v for k,v in json.loads(args.registry.read_text(encoding='utf-8')).items()} if args.registry else None
            result=drill(path=args.db,session_id=args.session,kind=args.kind,target=args.target,reason=args.reason,metric=args.metric,
                         selector=args.selector,root=args.root,numeric_bundles=registry)
        elif args.command.startswith('accept-'):
            response=json.loads(args.response.read_text(encoding='utf-8'))
            service={'accept-profile':accept_profile,'accept-lower':accept_lower,'accept-match':accept_match}[args.command]
            kw={'ref':args.ref} if args.command=='accept-lower' else {}
            result=service(path=args.db,session_id=args.session,response=response,**kw)
        elif args.command=='profile':result=read_profile(path=args.db,contract_id=args.contract,revision=args.revision)
        elif args.command=='report':result=render_profile(read_profile(path=args.db,contract_id=args.contract,revision=args.revision),language=args.language)
        elif args.command=='audit':result=audit(path=args.db,session_id=args.session)
        else:result=prepare_match(path=args.db,contract_id=args.contract,match_id=args.match_id,question=args.question,mode=args.mode)
        body=result if isinstance(result,str) else encode(result)+'\n'
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(body,encoding='utf-8')
            print(encode({'output':str(args.output),'bytes':len(body.encode('utf-8'))}))
        else:print(body,end='')
        return 0
    except (ValueError,KeyError,OSError,sqlite3.Error) as exc:parser.exit(1,str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
