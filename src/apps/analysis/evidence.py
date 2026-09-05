"""Content-addressed JSON-pointer references into immutable source responses."""
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def reference(*, root: Path, file: Path, source: str, pointer: str) -> dict:
    resolved = file.resolve()
    relative = resolved.relative_to(root.resolve())
    return {'id': digest([relative.as_posix(), hashlib.sha256(resolved.read_bytes()).hexdigest(), pointer])[:24],
            'source': source, 'file': relative.as_posix(), 'sha256': hashlib.sha256(resolved.read_bytes()).hexdigest(),
            'pointer': pointer}


def resolve(*, root: Path, ref: dict) -> Any:
    path = (root / ref['file']).resolve()
    path.relative_to(root.resolve())
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != ref['sha256']:
        raise ValueError('Evidence hash mismatch')
    value = json.loads(body)
    pointer = ref['pointer']
    if pointer and not pointer.startswith('/'):
        raise ValueError('Expected JSON pointer')
    for part in pointer.split('/')[1:]:
        key = part.replace('~1','/').replace('~0','~')
        value = value[int(key)] if isinstance(value,list) else value[key]
    return value
