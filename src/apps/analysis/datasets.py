"""Explicit month-scoped ranked history and resumable snapshot collection."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .sampling import save, has_snapshot
from src.apps.opendota.clients import OpenDotaClient
from src.apps.opendota.services import collect_match as collect_opendota
from src.apps.stratz.clients import TransientRetryStratzClient
from src.apps.stratz.services import collect_match as collect_stratz


def month_bounds(year: int, month: int) -> tuple[int, int]:
    tz=timezone(timedelta(hours=3))
    begin=datetime(year,month,1,tzinfo=tz)
    end=datetime(year+int(month==12),1 if month==12 else month+1,1,tzinfo=tz)
    return int(begin.timestamp()),int(end.timestamp())


def validate_selection(data: dict, *, account_id: int, match_id: int | None = None) -> None:
    if data.get('version')!='ranked-month-1' or data.get('account_id')!=account_id:
        raise ValueError('Wrong dataset version/account')
    begin,end=month_bounds(data['year'],data['month'])
    ids=[]
    for row in data['matches']:
        if type(row.get('match_id')) is not int or row.get('lobby_type')!=7 or not begin<=row['start_time']<end:
            raise ValueError('Match outside ranked month scope')
        ids.append(row['match_id'])
    if len(ids)!=len(set(ids)) or (match_id is not None and match_id not in ids):
        raise ValueError('Duplicate or unselected match')


def discover_month(*, directory: Path, account_id: int, year: int, month: int,
                   client: OpenDotaClient, pause=time.sleep) -> dict:
    """Read unfiltered history so visible non-ranked games can break ranked adjacency."""
    begin,end=month_bounds(year,month);path=directory/'selection.json'
    if path.exists():
        data=json.loads(path.read_text(encoding='utf-8'))
        validate_selection(data,account_id=account_id)
        if (data['year'],data['month'])!=(year,month):raise ValueError('Saved month differs')
        return data
    rows={};requests=[];previous_oldest=None;finished=False
    for offset in range(0,10000,100):
        body,request=client.fetch(f'/players/{account_id}/matches?limit=100&offset={offset}')
        page=json.loads(body)
        if not isinstance(page,list):raise ValueError('Invalid history page')
        directory.mkdir(parents=True,exist_ok=True)
        filename=f'history-{offset}.json';(directory/filename).write_bytes(body)
        requests.append({**request,'file':filename})
        starts=[r['start_time'] for r in page]
        if starts!=sorted(starts,reverse=True) or (starts and previous_oldest is not None and max(starts)>previous_oldest):
            raise ValueError('History changed order during pagination; retry discovery')
        for row in page:
            mid=row['match_id']
            if mid in rows:raise ValueError('History pagination overlap; retry discovery')
            rows[mid]=row
        if len(page)<100 or (starts and min(starts)<begin):finished=True;break
        previous_oldest=min(starts);pause(1.1)
    if not finished:raise ValueError('History safety page limit reached; month not declared complete')
    visible=sorted((r for r in rows.values() if begin<=r['start_time']<end),key=lambda r:(r['start_time'],r['match_id']))
    chosen=[{**r,'collection_status':'selected'} for r in visible if r.get('lobby_type')==7 and r.get('duration',0)>0 and type(r.get('radiant_win')) is bool]
    data={'version':'ranked-month-1','account_id':account_id,'year':year,'month':month,
          'timezone':'Europe/Moscow UTC+03:00','begin_inclusive':begin,'end_exclusive':end,
          'history_boundary_reached':finished,'history_complete':False,'requests':requests,
          'visible_history':visible,'matches':chosen,
          'limitations':['All eligible ranked matches visible in this API snapshot; private or missing games are unknown.',
                         'Pagination is not a transactional snapshot; ordered non-overlapping pages required.']}
    validate_selection(data,account_id=account_id);save(path,data)
    return data


def collect_month(*, root: Path, directory: Path, account_id: int, token: str,
                  year: int, month: int, discover_only: bool = False) -> dict:
    od=OpenDotaClient();data=discover_month(directory=directory,account_id=account_id,year=year,month=month,client=od)
    print(f"Ranked month: {len(data['matches'])} matches; {len(data['visible_history'])} visible games",flush=True)
    if discover_only:return data
    st=TransientRetryStratzClient(token=token)
    for index,row in enumerate(data['matches'],1):
        mid=row['match_id'];print(f"{index}/{len(data['matches'])}: {mid}",flush=True)
        selection={'account_id':account_id,'match_id':mid,'hero_id':row['hero_id'],'player_slot':row['player_slot'],
                   'duration_seconds':row['duration'],'selected_history_entry':{k:row[k] for k in ('start_time','duration','radiant_win','game_mode','lobby_type')},
                   'source':'OpenDota','patch_id':None}
        selected=directory/'selections'/f'{mid}.json';save(selected,selection)
        try:
            if not has_snapshot(root,mid,'opendota'):
                collect_opendota(selection_path=selected,account_id=account_id,output_root=root/'data/matches',client=od)
            if not has_snapshot(root,mid,'stratz'):
                collect_stratz(selection_path=selected,account_id=account_id,output_root=root/'data/matches',client=st,reuse_verified_queries=True)
            row['collection_status']='collected' if has_snapshot(root,mid,'stratz') else 'partial'
        except Exception as exc:
            # Preserve the scope and stop on transport/quota errors; retry resumes snapshots.
            row['collection_status']='failed';row['error_type']=type(exc).__name__
            save(directory/'selection.json',data)
            if any(f'HTTP {status} ' in str(exc) for status in (502,503,504)):
                print(f'{mid}: gateway failure retained; continuing other selected matches',flush=True)
                continue
            raise
        save(directory/'selection.json',data)
    return data
