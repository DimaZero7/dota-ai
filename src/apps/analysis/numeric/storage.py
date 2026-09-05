"""Separate immutable numeric bundles; historical artifacts are untouched."""
import hashlib
import json
from pathlib import Path

from ..evidence import digest
from .schemas import NumericError, validate_node


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')


def save_bundle(directory: Path, nodes: list[dict], *, key: str, catalog_hash: str) -> dict:
    manifest={'version':'numeric-bundle-1','key':key,'catalog_hash':catalog_hash,'files':{},'new_matches_fetched':0,'meta_applied':False}
    for n in nodes:
        validate_node(n)
        filename=f"L{n['level']}.json"
        write_json(directory/filename,n)
        body=(directory/filename).read_bytes()
        manifest['files'][filename]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'revision':n['revision']}
    write_json(directory/'manifest.json',manifest)
    return manifest


def load_node(directory: Path, level: int) -> dict:
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    filename=f'L{level}.json'
    body=(directory/filename).read_bytes()
    expected=manifest['files'][filename]
    if len(body)!=expected['bytes'] or hashlib.sha256(body).hexdigest()!=expected['sha256']:
        raise NumericError('Numeric artifact integrity failure')
    data=json.loads(body);validate_node(data)
    if data['revision']!=expected['revision']:raise NumericError('Manifest revision mismatch')
    if data['level']!=level:raise NumericError('Wrong numeric level')
    if level>1:
        child=load_node(directory,level-1)
        if data['children_manifest_ref']!={child['id']:child['revision']} or child['scope']!=data['scope'] or child['source_manifest_ref']!=data['source_manifest_ref']:
            raise NumericError('Numeric child dependency mismatch')
    return data


def bundle_key(sources: dict, catalog: dict) -> str:
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    for name in ('sources.py','coverage.py','evidence.py'):
        path=Path(__file__).parent.parent/name
        code['../'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return digest({'sources':sources,'catalog':catalog,'code':code})[:24]
