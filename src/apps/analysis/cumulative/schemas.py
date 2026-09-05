"""Immutable contracts and validated import envelopes."""
import json
from functools import lru_cache
from pathlib import Path

from ..evidence import digest
from ..longitudinal.schemas import PARAMETERS, validate
from ..spatial.schemas import DEFAULTS

VERSION='cumulative-store-1'


class CumulativeError(ValueError):
    """Invalid import, incompatible method or stale write."""


def encode(value: object) -> str:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


@lru_cache(maxsize=1)
def runtime_method_hash() -> str:
    code={str(p.relative_to(Path(__file__).parent.parent)):digest(p.read_text(encoding='utf-8'))
          for folder in ('cumulative','longitudinal','spatial') for p in (Path(__file__).parent.parent/folder).glob('*.py')}
    return digest(code)


def contract(*, catalog: dict, map_version: str, recent_count: int = 10) -> dict:
    if type(recent_count) is not int or recent_count<1:raise CumulativeError('Positive recent window required')
    return {'schema':VERSION,'catalog_hash':digest(catalog),'map_version':map_version,
            'grouping_version':'longitudinal-strict-relaxed-1','method_hash':runtime_method_hash(),
            'signature_parameters':json.loads(encode(PARAMETERS)),'spatial_parameters':json.loads(encode(DEFAULTS)),
            'recent_count':recent_count,'decay_weighting':False}


def contribution(signature: dict, *, spatial: dict | None = None) -> dict:
    validate(signature,4)
    if spatial is not None:
        from ..spatial.schemas import validate as validate_spatial
        from ..spatial.aggregation import build_match
        validate_spatial(spatial)
        if spatial['level']!=3 or spatial['context']['match_id']!=signature['match_id'] or spatial['context']['account_id']!=signature['account_id']:
            raise CumulativeError('Wrong spatial contribution identity')
        for key in ('hero_id','position','mode'):
            if spatial['context'][key]!=signature['context'][key]:raise CumulativeError('Spatial comparison context differs')
        if spatial['context']['patch_ids'].get('stratz')!=signature['context']['stratz_version']:
            raise CumulativeError('Spatial game version differs')
        parent=build_match(spatial)
        if signature['dependencies'].get(parent['id'])!=parent['revision']:
            raise CumulativeError('Spatial revision is not an input of this signature')
    data={'signature':signature,'spatial':spatial}
    return {**data,'revision':digest(data)}


def validate_contribution(value: dict, account_id: int, spec: dict) -> None:
    if spec['method_hash']!=runtime_method_hash() or spec['grouping_version']!='longitudinal-strict-relaxed-1':
        raise CumulativeError('This runtime cannot publish under a different calculation implementation')
    if value!=contribution(value['signature'],spatial=value['spatial']):raise CumulativeError('Contribution integrity failure')
    row=value['signature']
    if row['account_id']!=account_id or type(row['match_id']) is not int:raise CumulativeError('Wrong player or match ID')
    if row['parameter_version']!=spec['signature_parameters']:raise CumulativeError('Method parameters require a separate contract')
    if value['spatial'] is not None and value['spatial']['parameters']!=spec['spatial_parameters']:
        raise CumulativeError('Coordinate parameters require a separate contract')


def inventory(value: dict) -> dict:
    row=value['signature']
    return {'metrics':{k:{'present':True,'eligible':m['eligible']} for k,m in row['metrics'].items()},
            'phases':bool(row['phases']),'spatial':value['spatial'] is not None,
            'source_revision':row['source_manifest_ref'],'signature_revision':row['revision']}
