"""Offline L4 signature preparation and numerical L5 aggregation."""
import hashlib
import json
from pathlib import Path

from ..evidence import digest
from ..numeric.storage import load_node, write_json
from ..spatial.services import build_spatial_match, read_spatial
from .schemas import VERSION, PARAMETERS, LongitudinalError, signed, validate
from .signatures import build_signature
from .cohorts import build_cohorts, recent_comparison, composition
from .sessions import chronology, sensitivity
from .relations import find_relations


def code_version() -> str:
    return digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})


def prepare_match(*, root: Path, account_id: int, match_id: int,
                  dataset_path: Path | None = None) -> dict:
    spatial=build_spatial_match(root=root,account_id=account_id,match_id=match_id,dataset_path=dataset_path)
    manifest=json.loads((spatial['directory']/'manifest.json').read_text(encoding='utf-8'))
    numeric_dir=root/manifest['numeric_bundle']
    numeric=load_node(numeric_dir,4);episodes=load_node(numeric_dir,2)
    routes=read_spatial(spatial['directory'],'routes')
    key=digest([numeric['revision'],spatial['match']['revision'],routes['revision'],code_version()])[:24]
    directory=root/'data/analysis/longitudinal/matches'/str(match_id)/key
    if (directory/'signature.json').exists():
        row=json.loads((directory/'signature.json').read_text(encoding='utf-8'));validate(row,4)
    else:
        row,detail=build_signature(numeric,episodes,spatial['match'],routes)
        write_json(directory/'signature.json',row)
        write_json(directory/'detail.json',signed({'schema_version':VERSION,**detail}))
    return {'directory':directory,'signature':row}


def known_history_gaps(rows: list[dict], dataset: dict | None) -> set[tuple[int,int]]:
    if not dataset:return set()
    ordered=sorted(rows,key=lambda r:(r['start_time'],r['match_id']))
    history=dataset['visible_history'];result=set()
    for a,b in zip(ordered,ordered[1:]):
        if any(a['start_time']<r['start_time']<b['start_time'] for r in history):
            result.add((a['match_id'],b['match_id']))
    return result


def chronology_rows(rows: list[dict], dataset: dict | None) -> list[dict]:
    """Retain known timestamps/results even if detailed journals could not be fetched."""
    if dataset is None:return rows
    by_id={r['match_id']:r for r in rows};result=[]
    for h in dataset['matches']:
        existing=by_id.get(h['match_id'])
        if existing is not None:
            if (existing['start_time'],existing['duration'],existing['win'])!=(h['start_time'],h['duration'],(h['player_slot']<128)==h['radiant_win']):
                raise LongitudinalError('History and detailed chronology disagree')
            result.append(existing)
        else:
            result.append({'match_id':h['match_id'],'start_time':h['start_time'],'duration':h['duration'],
                           'win':(h['player_slot']<128)==h['radiant_win'],
                           'context':{'hero_id':h['hero_id'],'position':None},'metrics':{},
                           'source':'verified selected OpenDota history; detailed journals unavailable'})
    return result


def aggregate_signatures(rows: list[dict], *, recent_count: int = 3,
                         dataset: dict | None = None) -> tuple[dict,dict]:
    """Only retained numerical L4 rows; no raw snapshots, network or L1-L3 reads."""
    if not rows:raise LongitudinalError('At least one match signature required')
    for row in rows:
        validate(row,4)
        if row['parameter_version']!=PARAMETERS:raise LongitudinalError('Signature parameters differ')
    if len({r['match_id'] for r in rows})!=len(rows):raise LongitudinalError('Duplicate match')
    if len({r['account_id'] for r in rows})!=1:raise LongitudinalError('Mixed player accounts')
    if dataset is not None:
        from ..datasets import validate_selection
        validate_selection(dataset,account_id=rows[0]['account_id'])
        selected={r['match_id'] for r in dataset['matches']}
        if any(r['match_id'] not in selected for r in rows):raise LongitudinalError('Signature outside selected dataset')
    rows=sorted(rows,key=lambda r:r['match_id'])
    cohorts,members=build_cohorts(rows);relations=find_relations(rows,cohorts,members)
    relation_detail=relations.pop('details');time_rows=chronology_rows(rows,dataset);gaps=known_history_gaps(time_rows,dataset)
    sessions=chronology(time_rows,known_gaps=gaps)
    data=signed({'schema_version':VERSION,'level':5,'id':f"{rows[0]['account_id']}:longitudinal:L5",
                 'account_id':rows[0]['account_id'],'parameters':PARAMETERS,'implementation':code_version(),
                 'dependencies':{r['id']:r['revision'] for r in rows},'n':len(rows),
                 'wins':sum(r['win'] is True for r in rows),'losses':sum(r['win'] is False for r in rows),
                 'composition':composition(rows),'cohorts':cohorts,'relations':relations,
                 'sessions':{'rule_version':sessions['rule_version'],'gap_minutes':sessions['gap_minutes'],
                             'n':len(time_rows),'chronology_revision':digest(time_rows),
                             'summary':sessions['summary'],'sensitivity':sensitivity(time_rows,known_gaps=gaps)},
                 'recent':recent_comparison(rows,cohorts,members,recent_count=recent_count),
                 'dataset_coverage':{'selected':len(dataset['matches']) if dataset else len(rows),'analyzed':len(rows),
                                     'known_broken_links':len(gaps),'history_complete':False},
                 'limitations':['descriptive observational data; no causal or psychological labels',
                                'patch identifiers restrict pooling; meta not applied',
                                'no complete-draft adjustment or population/player benchmark',
                                'numerical L5 is analyst input, not an automatically inferred player personality']})
    detail=signed({'schema_version':VERSION,'l5_revision':data['revision'],
                   'matches':{str(r['match_id']):r for r in rows},'relations':relation_detail,
                   'cohorts':{k:[{'match_id':e['row']['match_id'],'metrics':e['metrics']} for e in es] for k,es in members.items()},
                   'sessions':sessions})
    return data,detail


def save_analysis(directory: Path, data: dict, detail: dict) -> None:
    validate(data,5);validate(detail)
    if detail['l5_revision']!=data['revision']:raise LongitudinalError('Detail revision mismatch')
    write_json(directory/'L5.json',data);write_json(directory/'detail.json',detail)


def read_analysis(directory: Path) -> tuple[dict,dict]:
    data=json.loads((directory/'L5.json').read_text(encoding='utf-8'))
    detail=json.loads((directory/'detail.json').read_text(encoding='utf-8'))
    validate(data,5);validate(detail)
    if detail['l5_revision']!=data['revision']:raise LongitudinalError('Detail revision mismatch')
    return data,detail
