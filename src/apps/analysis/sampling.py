"""Small persisted latest-match sample; hard cap of ten distinct match IDs."""
import json
from datetime import datetime, timezone
from pathlib import Path

from src.apps.opendota.clients import OpenDotaClient
from src.apps.opendota.services import collect_match as collect_opendota
from src.apps.stratz.clients import StratzClient
from src.apps.stratz.services import collect_match as collect_stratz


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def has_snapshot(root: Path, match_id: int, source: str) -> bool:
    for path in (root/'data/matches'/str(match_id)/source).glob('*/metadata.json'):
        metadata=json.loads(path.read_text(encoding='utf-8'))
        allowed=('complete','needs_parse_review') if source=='opendota' else ('complete',)
        if metadata.get('status') in allowed and metadata.get('match_id')==match_id and (path.parent/'match.json').exists():
            return True
    return False


def collect_sample(*, root: Path, account_id: int, token: str, total: int = 4) -> dict:
    if not 2<=total<=10:
        raise ValueError('Prototype sample must contain 2..10 matches including the frozen match')
    manifest_path=root/'data/prototype_matches.json'
    frozen=json.loads((root/'data/selected_match.json').read_text(encoding='utf-8'))
    if frozen['account_id']!=account_id:
        raise ValueError('Configured account mismatch')
    od=OpenDotaClient()
    st=StratzClient(token=token)
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['account_id']!=account_id or len(manifest['matches'])>10:
            raise ValueError('Invalid saved sample')
    else:
        history=od.get(f'/players/{account_id}/matches?limit=10')
        now=datetime.now(timezone.utc)
        completed=[r for r in history if type(r.get('match_id')) is int and r.get('duration',0)>0
                   and type(r.get('radiant_win')) is bool and r['start_time']+r['duration']<=now.timestamp()]
        completed.sort(key=lambda r:(r['start_time'],r['match_id']),reverse=True)
        chosen=[frozen['match_id']]
        for row in completed:
            if len(chosen)>=total:
                break
            if row['match_id'] not in chosen:
                chosen.append(row['match_id'])
        known={int(p.name) for p in (root/'data/matches').iterdir() if p.is_dir() and p.name.isdigit()}
        if len(known|set(chosen))>10:
            raise ValueError('Ten-match cap would be exceeded')
        manifest={'account_id':account_id,'frozen_match_id':frozen['match_id'],'checked_at_utc':now.isoformat(),
                  'history_url':od.base_url+f'/players/{account_id}/matches?limit=10',
                  'selection':'Frozen original plus latest available completed matches, without outcome/hero filtering.',
                  'limit':10,'requested_total':total,'matches':[{'match_id':mid,'status':'selected'} for mid in chosen],
                  'limitations':['Available API history may lag behind actual play. This is a small prototype sample.']}
        save(manifest_path,manifest)
    known={int(p.name) for p in (root/'data/matches').iterdir() if p.is_dir() and p.name.isdigit()}
    if len(known|{r['match_id'] for r in manifest['matches']})>10:
        raise ValueError('Ten-match cap would be exceeded')
    for row in manifest['matches']:
        mid=row['match_id']
        print(f'Sample match {mid}: checking local snapshots',flush=True)
        if mid==frozen['match_id']:
            selection_path=root/'data/selected_match.json'
            selection=frozen
        else:
            selection_path=root/'data/prototype/selections'/f'{mid}.json'
            if selection_path.exists():
                selection=json.loads(selection_path.read_text(encoding='utf-8'))
            else:
                raw=od.get(f'/matches/{mid}')
                if raw.get('match_id')!=mid:
                    raise ValueError('Wrong match returned')
                players=[p for p in raw.get('players',[]) if p.get('account_id')==account_id]
                if len(players)!=1:
                    raise ValueError('Sample participation not verified')
                player=players[0]
                selection={'account_id':account_id,'match_id':mid,'hero_id':player['hero_id'],
                           'player_slot':player['player_slot'],'duration_seconds':raw['duration'],
                           'selected_history_entry':{k:raw[k] for k in ('start_time','duration','radiant_win','game_mode','lobby_type')},
                           'patch_id':raw.get('patch'),'source':'OpenDota','match_url':od.base_url+f'/matches/{mid}'}
                save(selection_path,selection)
        row.update({'hero_id':selection['hero_id'],'duration_seconds':selection['duration_seconds'],
                    'start_time':selection['selected_history_entry']['start_time'],'patch_id':selection.get('patch_id')})
        try:
            if not has_snapshot(root,mid,'opendota'):
                result=collect_opendota(selection_path=selection_path,account_id=account_id,output_root=root/'data/matches',client=od)
                row['opendota_status']=result['status']
            if not has_snapshot(root,mid,'stratz'):
                output=collect_stratz(selection_path=selection_path,account_id=account_id,output_root=root/'data/matches',client=st)
                if json.loads((output/'metadata.json').read_text())['status']!='complete':
                    raise ValueError('STRATZ returned partial data')
            row['status']='collected'
        except Exception:
            row['status']='failed; retained for explicit review'
            save(manifest_path,manifest)
            raise
        save(manifest_path,manifest)
        print(f'Sample match {mid}: collected',flush=True)
    return manifest
