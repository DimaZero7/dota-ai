"""Thin offline JSON interface for contribution imports and addressed reads."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .schemas import CumulativeError, contribution, contract, encode
from .services import apply_batch, change_packet
from .storage import connect, decode_checked


def main() -> int:
    # Redirected Windows stdout can otherwise select a legacy encoding without metric symbols.
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    imp=sub.add_parser('import');imp.add_argument('--account',type=int,required=True);imp.add_argument('--catalog',type=Path,required=True)
    imp.add_argument('--map-version',required=True);imp.add_argument('--recent',type=int,default=10)
    imp.add_argument('--signature',type=Path,action='append',default=[]);imp.add_argument('--envelope',type=Path,action='append',default=[])
    imp.add_argument('--expected',type=Path,help='JSON mapping match ID to current contribution revision')
    imp.add_argument('--remove',type=int,action='append',default=[]);imp.add_argument('--generation',type=int)
    read=sub.add_parser('read');read.add_argument('--contract',required=True);read.add_argument('--group');read.add_argument('--change',type=int);read.add_argument('--sequence')
    args=p.parse_args()
    try:
        if args.command=='import':
            spec=contract(catalog=json.loads(args.catalog.read_text(encoding='utf-8')),map_version=args.map_version,recent_count=args.recent)
            values=[contribution(json.loads(f.read_text(encoding='utf-8'))) for f in args.signature]
            values += [json.loads(f.read_text(encoding='utf-8')) for f in args.envelope]
            expected={int(k):v for k,v in json.loads(args.expected.read_text(encoding='utf-8')).items()} if args.expected else {}
            result=change_packet(apply_batch(path=args.db,account_id=args.account,spec=spec,values=values,remove=args.remove,
                                            expected_generation=args.generation,expected_revisions=expected))
        else:
            with connect(args.db,readonly=True) as db:
                db.execute('BEGIN')
                if args.sequence:
                    record=db.execute('SELECT payload FROM sequences WHERE contract=? AND id=?',(args.contract,args.sequence)).fetchone()
                    result=json.loads(record[0]) if record else None
                elif args.group:
                    record=db.execute('SELECT payload,revision FROM groups WHERE contract=? AND gid=?',(args.contract,args.group)).fetchone()
                    result=decode_checked(record[0],record[1]) if record else None
                elif args.change is not None:
                    record=db.execute('SELECT payload FROM changes WHERE contract=? AND generation=?',(args.contract,args.change)).fetchone()
                    result=change_packet(json.loads(record[0])) if record else None
                else:
                    record=db.execute('SELECT generation,spec FROM contracts WHERE id=?',(args.contract,)).fetchone()
                    state=db.execute('SELECT payload FROM states WHERE contract=?',(args.contract,)).fetchone()
                    result={'contract':args.contract,'generation':record[0],'spec':json.loads(record[1]),
                            'summary':{k:v for k,v in json.loads(state[0]).items() if k not in ('chronology','sensitivity','recent_ids','sequence_refs')}} if record and state else None
                db.execute('COMMIT')
                if result is None:raise CumulativeError('Requested record not found')
        print(encode(result));return 0
    except (CumulativeError,OSError,ValueError,KeyError,sqlite3.Error) as exc:
        p.exit(1,str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
