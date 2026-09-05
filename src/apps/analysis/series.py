"""Legacy numeric screening over local snapshots, not a personal player analysis.

The authored hierarchy lives in synthesis.py. Its accepted reviews must be consumed
bottom-up; this historical comparator alone does not establish playing style.
"""
import json
from pathlib import Path
from .pipeline import run_match
from .comparison import compare_matches
from .patterns import build_patterns
from .profile import build_profile
from .training import plan_training
from .history import save_profile_version
from .storage import save_artifact,load_artifact
from .evidence import digest
from .quality import verify_trace


def run_series(*, root: Path, account_id: int, horizon: int = 90) -> tuple[dict,Path]:
    manifest=json.loads((root/'data/prototype_matches.json').read_text(encoding='utf-8'))
    ids=[r['match_id'] for r in manifest['matches']]
    if manifest['account_id']!=account_id or not 1<=len(ids)<=10 or len(set(ids))!=len(ids):
        raise ValueError('Invalid prototype manifest')
    matches=[]; outputs={}
    for mid in ids:
        data,path,_=run_match(root=root,match_id=mid,account_id=account_id)
        matches.append(data); outputs[str(mid)]=path.relative_to(root).as_posix()
    key=digest({'outputs':outputs,'horizon':horizon})[:24]
    output=root/'data/analysis/series'/key
    data=load_artifact(output)
    if data is None:
        comparison=compare_matches(matches,horizon=horizon)
        registry={k:v for m in matches for k,v in m['registry'].items()}
        patterns=build_patterns(comparison,registry)
        profile=plan_training(build_profile(patterns,account_id=account_id),patterns)
        registry.update({p['id']:p for p in [*patterns,profile]})
        data={'account_id':account_id,'match_ids':ids,'lower_outputs':outputs,'registry':registry,
              'comparison':comparison,'pattern_ids':[p['id'] for p in patterns],'profile_id':profile['id'],
              'trace':verify_trace(registry,profile['id']),'meta_applied':False}
        save_artifact(output,data)
    history=save_profile_version(root=root,profile=data['registry'][data['profile_id']],source_version=key)
    return {**data,'profile_version':history},output
