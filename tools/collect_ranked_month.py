"""Explicitly collect a month of public ranked history, retaining prior snapshots."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.settings import config_toml
from src.apps.analysis.datasets import collect_month

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year',type=int,required=True)
    parser.add_argument('--month',type=int,required=True)
    parser.add_argument('--discover-only',action='store_true')
    args=parser.parse_args()
    collect_month(root=ROOT,directory=ROOT/f'data/datasets/{args.year}-{args.month:02d}-ranked',
                  account_id=config_toml['player']['account_id'],token=config_toml['stratz'].get('token',''),
                  year=args.year,month=args.month,discover_only=args.discover_only)
