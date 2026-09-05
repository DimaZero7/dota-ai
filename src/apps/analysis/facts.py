"""Deterministic measurements with original source clocks and evidence pointers."""
from .coverage import coverage
from .sources import Sources
from .timebases import clock_report
import json

KINDS = {'playerUpdatePositionEvents':'position','playerUpdateHealthEvents':'health',
         'playerUpdateGoldEvents':'economy','abilityUsedEvents':'ability','itemUsedEvents':'item',
         'killEvents':'kill','deathEvents':'death','assistEvents':'assist','csEvents':'last_hit',
         'goldEvents':'gold','experienceEvents':'experience','healEvents':'heal',
         'heroDamageEvents':'damage','towerDamageEvents':'tower_damage','purchaseEvents':'purchase',
         'abilityLearnEvents':'learn','buyBackEvents':'buyback','runeEvents':'rune',
         'inventoryEvents':'inventory','playerUpdateLevelEvents':'level'}


def build_facts(sources: Sources) -> dict:
    events = []
    st = sources.stratz
    roster = [{k:p.get(k) for k in ('playerSlot','steamAccountId','heroId','isRadiant','position','lane','role',
                                   'kills','deaths','assists','numLastHits','numDenies','goldPerMinute',
                                   'experiencePerMinute','networth','heroDamage','towerDamage','heroHealing')}
              for p in st['players']]
    target = next(p for p in roster if p['steamAccountId'] == sources.account_id)
    names_path=sources.root/'data/prototype/hero_names.json'
    names=json.loads(names_path.read_text(encoding='utf-8'))['names'] if names_path.exists() else {}
    for player in roster:
        player['hero_name']=names.get(str(player['heroId']))

    def add(key: str, pointer: str, kind: str, slot: int | None, entry: dict, time: float) -> None:
        if type(time) not in (int,float):
            return
        events.append({'id':f'{sources.match_id}:{key}:{pointer}', 'kind':kind,'time':time,
                       'slot':slot,'document':key,'pointer':pointer,'data':entry})

    for key, payload in sources.documents.items():
        if not key.startswith('stratz/playback-'):
            continue
        for i,p in enumerate(payload['data']['match']['players']):
            for field,kind in KINDS.items():
                for j,event in enumerate((p.get('playbackData') or {}).get(field) or []):
                    if isinstance(event,dict):
                        add(key,f'/data/match/players/{i}/playbackData/{field}/{j}',kind,p['playerSlot'],event,event.get('time'))
    for i,entry in enumerate(sources.opendota.get('objectives') or []):
        add('opendota',f'/objectives/{i}','objective',entry.get('player_slot'),entry,entry.get('time'))
    for i,entry in enumerate(sources.opendota.get('teamfights') or []):
        # Participant fight statistics remain in the referenced source, not duplicated in every packet.
        small = {k:entry[k] for k in ('start','end','last_death','deaths') if k in entry}
        add('opendota',f'/teamfights/{i}','fight',None,small,entry.get('start'))
    for i,p in enumerate(sources.opendota['players']):
        for j,entry in enumerate(p.get('purchase_log') or []):
            add('opendota',f'/players/{i}/purchase_log/{j}','purchase_opendota',p['player_slot'],entry,entry.get('time'))
    events.sort(key=lambda e:(e['time'],e['id']))
    return {'level':1,'match_id':sources.match_id,'account_id':sources.account_id,
            'context':{'hero_id':target['heroId'],'hero_name':target['hero_name'],'position':target['position'],'lane':target['lane'],
                       'position_origin':'STRATZ estimate','target_slot':target['playerSlot'],
                       'roster':roster,'duration':st['durationSeconds'],'start_time':st['startDateTime'],
                       'did_radiant_win':st['didRadiantWin'],'game_mode':st.get('gameMode'),
                       'patch_ids':{'opendota':sources.opendota.get('patch'),'stratz':st.get('gameVersionId')},
                       'meta_applied':False},
            'clocks':clock_report(sources),'coverage':coverage(sources),'events':events,
            'limitations':['Source event clocks may differ; exact cross-source ordering is not asserted.',
                           'Position and role are source estimates, not prescribed responsibilities.',
                           'No meta, ability cooldown reconstruction, complete visibility or intent inference.']}


def event_evidence(sources: Sources, event: dict) -> dict:
    return sources.ref(event['document'],event['pointer'])
