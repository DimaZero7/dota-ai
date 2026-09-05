"""Callable offline orchestration and compact numeric-match retrieval."""
import json
from pathlib import Path

from ..evidence import digest
from ..sources import load_sources
from .facts import build_numeric_facts
from .episodes import build_numeric_episodes
from .phases import build_numeric_phases, build_numeric_match
from .schemas import NumericError, PARAMETERS
from .storage import bundle_key, load_node, save_bundle
from .interpretation import prepare_numeric_review, accept_numeric_review, read_numeric_review


def build_numeric_match_from_sources(*, root: Path, match_id: int, account_id: int,
                                     output_root: Path | None = None, use_cache: bool = True) -> dict:
    """Build one of the ten approved local matches; no network/model calls."""
    selection=json.loads((root/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    if account_id!=selection['account_id'] or str(match_id) not in selection['lower_outputs'] or len(selection['lower_outputs'])>10:
        raise NumericError('Only the approved ten-match prototype selection is allowed')
    sources=load_sources(root=root,match_id=match_id,account_id=account_id)
    catalog=json.loads((root/'docs/contracts/statistics-catalog.json').read_text(encoding='utf-8'))
    key=bundle_key(sources.references,{'catalog':catalog,'parameters':PARAMETERS})
    directory=(output_root if output_root is not None else root/'data/analysis/numeric')/str(match_id)/key
    if use_cache and (directory/'manifest.json').exists():
        result=load_node(directory,4)
        return {'directory':str(directory),'cache_hit':True,'match':result}
    l1=build_numeric_facts(sources)
    l2=build_numeric_episodes(l1)
    l3=build_numeric_phases(l2)
    l4=build_numeric_match(l3)
    manifest=save_bundle(directory,[l1,l2,l3,l4],key=key,catalog_hash=digest(catalog))
    return {'directory':str(directory),'cache_hit':False,'match':l4,'manifest':manifest}
