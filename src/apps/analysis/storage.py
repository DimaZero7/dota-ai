"""Versioned artifacts, reused only for identical inputs and analysis code."""
import hashlib
import json
from pathlib import Path

from .evidence import digest
from .enums import RULES_VERSION, META_POLICY


def cache_key(source_refs: dict, parameters: dict) -> str:
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    return digest({'sources':source_refs,'parameters':parameters,'code':code,
                   'rules':RULES_VERSION,'meta':META_POLICY,'model':'current_codex_file_exchange_v1'})[:24]


def save_artifact(directory: Path, data: dict) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    body=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
    (directory/'data.json').write_bytes(body)
    (directory/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(body).hexdigest(),
        'bytes':len(body),'rules_version':RULES_VERSION,'meta_applied':False},indent=2),encoding='utf-8')


def load_artifact(directory: Path) -> dict | None:
    if not (directory/'manifest.json').exists():
        return None
    metadata=json.loads((directory/'manifest.json').read_text())
    body=(directory/'data.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=metadata['sha256']:
        raise ValueError('Derived artifact integrity failure')
    return json.loads(body)
