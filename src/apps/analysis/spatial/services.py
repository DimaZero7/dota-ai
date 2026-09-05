"""Offline spatial orchestration; reuses verified numeric L1 without rewriting it."""
import hashlib
import json
from pathlib import Path

from ..evidence import digest
from ..numeric.services import build_numeric_match_from_sources
from ..numeric.storage import load_node, write_json
from ..numeric.schemas import validate_node
from .observations import build_observations, compare_routes
from .aggregation import build_phases, build_match, aggregate_selection
from .schemas import VERSION, SpatialError, parameters, signed, validate


def enrich_numeric_match(numeric: dict, spatial: dict) -> dict:
    validate_node(numeric);validate(spatial)
    if numeric['level']!=4 or spatial['level']!=4 or numeric['context']!=spatial['context']:
        raise SpatialError('Matched numeric/spatial L4 context required')
    return signed({'schema_version':VERSION,'id':spatial['id']+':enriched','level':4,'context':numeric['context'],
                   'dependencies':{numeric['id']:numeric['revision'],spatial['id']:spatial['revision']},
                   'measurements':[m for m in numeric['measurements'] if m['metric_id'] not in spatial['metrics']],
                   'spatial_measurements':spatial['metrics'],'numeric_summary':numeric['summary'],
                   'spatial_summary':spatial['summary'],'spatial_distribution_ref':spatial['id'],
                   'note':'Source numeric artifact retained; unavailable spatial placeholders replaced in this view.'})


def build_spatial_match(*, root: Path, match_id: int, account_id: int, overrides: dict | None = None,
                        output_root: Path | None = None, dataset_path: Path | None = None) -> dict:
    numeric=build_numeric_match_from_sources(root=root,match_id=match_id,account_id=account_id,dataset_path=dataset_path)
    facts=load_node(Path(numeric['directory']),1)
    params=parameters(overrides)
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    for path in (Path(__file__).parent.parent/'numeric').glob('*.py'):
        code['numeric/'+path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    key=digest({'numeric_l1':facts['revision'],'numeric_l4':numeric['match']['revision'],'params':params,'code':code})[:24]
    directory=(output_root or root/'data/analysis/spatial')/str(match_id)/key
    if (directory/'manifest.json').exists():
        return {'directory':directory,'observations':read_spatial(directory,2),'phases':read_spatial(directory,3),
                'match':read_spatial(directory,4),'enriched':read_spatial(directory,'enriched'),'cache_hit':True}
    observations=build_observations(facts,overrides=overrides)
    phases=build_phases(observations);match=build_match(phases)
    enriched=enrich_numeric_match(numeric['match'],match)
    # Default route examples retain death/purchase anchors; arbitrary actions can be selected by API.
    routes=[]
    for kind in ('death','purchase'):
        for e in facts['journals'][kind]['events']:
            time=e['time']+e['timeDead'] if kind=='death' else e['time']
            if not 0<=time<=facts['context']['duration']:continue
            routes.append({'anchor':{'kind':kind,'source_index':e['_source_index'],'time':e['time'],
                                      'time_basis':'reported death end' if kind=='death' else 'purchase event'},
                           'comparison':compare_routes(observations,before=max(0,e['time']),after=time)})
    artifacts={'L2':observations,'L3':phases,'L4':match,'enriched':enriched,'routes':signed({'schema_version':VERSION,'routes':routes,'dependencies':{observations['id']:observations['revision']}})}
    manifest={'version':VERSION,'key':key,'numeric_bundle':str(Path(numeric['directory']).relative_to(root)), 'files':{}}
    for name,data in artifacts.items():
        path=directory/f'{name}.json';write_json(path,data);body=path.read_bytes()
        manifest['files'][name]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
    write_json(directory/'manifest.json',manifest)
    return {'directory':directory,'observations':observations,'phases':phases,'match':match,'enriched':enriched,'cache_hit':False}


def read_spatial(directory: Path, level: int | str) -> dict:
    name=f'L{level}' if type(level) is int else level
    if name not in ('L2','L3','L4','enriched','routes'):raise SpatialError('Invalid spatial artifact name')
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    body=(directory/f'{name}.json').read_bytes();expected=manifest['files'][name]
    if len(body)!=expected['bytes'] or hashlib.sha256(body).hexdigest()!=expected['sha256']:
        raise SpatialError('Spatial file integrity failure')
    data=json.loads(body);validate(data)
    if name in ('L3','L4'):
        child=read_spatial(directory,2 if name=='L3' else 3)
        if data['dependencies']!={child['id']:child['revision']}:raise SpatialError('Spatial dependency changed')
    if name in ('routes','enriched'):
        child=read_spatial(directory,2 if name=='routes' else 4)
        if data['dependencies'].get(child['id'])!=child['revision']:raise SpatialError('Spatial dependency changed')
    return data


def route_for_action(*, facts: dict, observations: dict, kind: str, source_index: int, seconds: int = 60) -> dict:
    validate_node(facts);validate(observations)
    if observations['dependencies']!={facts['id']:facts['revision']}:raise SpatialError('Route facts do not match spatial data')
    if kind not in ('death','purchase','ability','item','kill'):raise SpatialError('Unsupported route anchor')
    e=next((e for e in facts['journals'][kind]['events'] if e['_source_index']==source_index),None)
    if e is None:raise SpatialError('Unknown action source index')
    time=e['time']+e['timeDead'] if kind=='death' else e['time']
    return {'anchor_kind':kind,'source_index':source_index,
            'comparison':compare_routes(observations,before=e['time'],after=time,seconds=seconds)}
