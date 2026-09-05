"""Pinned Dota underlay and a source-backed display transform, separate from statistics."""
import base64
import hashlib
import json
from pathlib import Path

from .schemas import SpatialError

ASSETS = Path(__file__).resolve().parents[4] / 'docs/assets/maps'


def load_underlay() -> dict:
    metadata=json.loads((ASSETS/'dota-740.json').read_text(encoding='utf-8'))
    body=(ASSETS/metadata['image']).read_bytes()
    if hashlib.sha256(body).hexdigest()!=metadata['sha256']:
        raise SpatialError('Dota underlay integrity failure')
    return {**metadata,'data_uri':'data:image/jpeg;base64,'+base64.b64encode(body).decode('ascii')}


def project(x: float, y: float, *, size: float) -> tuple[float,float]:
    """OpenDota gameCoordToUV, then image scaling. No side-dependent reflection."""
    return (x-64)*size/127,(191-y)*size/127


def cell_rectangle(key: str, *, cell_size: int, plot_size: int) -> tuple[float,float,float,float]:
    ix,iy=map(int,key.split(','))
    x,y=project(ix*cell_size,(iy+1)*cell_size,size=plot_size)
    side=cell_size*plot_size/127
    return x,y,side,side


def underlay_label(*, lang: str, patch_id: int | None) -> str:
    # Only a verified OD ID is named. Other versions remain explicitly unknown.
    patch='7.41' if patch_id==60 else '7.40' if patch_id==59 else '?'
    if lang=='ru':
        return f'Карта Dota 2 — подложка 7.40 · матчи {patch} · ориентир, не точный рельеф патча'
    return f'Dota 2 map — 7.40 underlay · matches {patch} · reference, not exact patch terrain'
