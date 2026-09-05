"""Content-addressed profile revisions; previous interpretations remain inspectable."""
import json
from pathlib import Path
from datetime import datetime,timezone
from .evidence import digest
from .sampling import save


def profile_changes(previous: dict | None, current: dict) -> dict:
    before={r['pattern_id']:r for r in (previous or {}).get('metrics',{}).get('conditions',[])}
    after={r['pattern_id']:r for r in current.get('metrics',{}).get('conditions',[])}
    return {'added':sorted(after.keys()-before.keys()),'removed_or_unavailable':sorted(before.keys()-after.keys()),
            'changed':[{'pattern_id':k,'before':before[k],'after':after[k]} for k in sorted(before.keys()&after.keys()) if before[k]!=after[k]],
            'note':'Changed/removed evidence requires reinterpretation; missing data does not demonstrate improvement.'}


def save_profile_version(*, root: Path, profile: dict, source_version: str) -> dict:
    directory=root/'data/analysis/profiles'/str(profile['account_id'])
    directory.mkdir(parents=True,exist_ok=True)
    index_path=directory/'index.json'
    index=json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {'versions':[],'latest':None}
    version=digest({'profile':profile,'source_version':source_version})[:24]
    if version==index['latest']:
        return {'version':version,'reused':True,'path':str(directory/f'{version}.json')}
    previous=json.loads((directory/f"{index['latest']}.json").read_text(encoding='utf-8'))['profile'] if index['latest'] else None
    path=directory/f'{version}.json'
    if not path.exists():
        save(path,{'version':version,'parent':index['latest'],'source_version':source_version,
                   'created_at_utc':datetime.now(timezone.utc).isoformat(),'profile':profile,'changes':profile_changes(previous,profile)})
    index['latest']=version
    if version not in index['versions']:
        index['versions'].append(version)
    save(index_path,index)
    return {'version':version,'reused':False,'path':str(path)}
