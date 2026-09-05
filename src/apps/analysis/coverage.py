"""Explicit presence states and source disagreements."""
from .sources import Sources

FINAL_FIELDS = [('kills','kills'),('deaths','deaths'),('assists','assists'),
                ('last_hits','numLastHits'),('denies','numDenies'),('gold_per_min','goldPerMinute'),
                ('xp_per_min','experiencePerMinute'),('net_worth','networth'),
                ('hero_damage','heroDamage'),('tower_damage','towerDamage'),('hero_healing','heroHealing')]


def field_state(record: dict, key: str, *, requested: bool = True) -> str:
    if key not in record:
        return 'missing' if requested else 'not_requested'
    value = record[key]
    if value is None:
        return 'null'
    if isinstance(value, (list,dict,str)) and len(value) == 0:
        return 'empty'
    if value is False:
        return 'false'
    if type(value) in (int,float) and value == 0:
        return 'zero'
    return 'value'


def coverage(sources: Sources) -> dict:
    od = {p['player_slot']:p for p in sources.opendota['players']}
    disagreements, players = [], []
    for p in sources.stratz['players']:
        for left,right in FINAL_FIELDS:
            a,b = od[p['playerSlot']],p
            if field_state(a,left) in ('missing','null') or field_state(b,right) in ('missing','null') or a.get(left) != b.get(right):
                disagreements.append({'slot':p['playerSlot'],'fields':[left,right],
                                      'values':[a.get(left),b.get(right)],'states':[field_state(a,left),field_state(b,right)]})
        players.append({'slot':p['playerSlot'],'account_id':p['steamAccountId'],
                        'position_state':field_state(p,'position'),
                        'stats':{k:field_state(p.get('stats') or {},k) for k in ('deathEvents','itemPurchases','impPerMinute')},
                        'playback':{k:field_state(p.get('playbackData') or {},k) for k in ('playerUpdatePositionEvents','playerUpdateHealthEvents','abilityUsedEvents')}})
    return {'level':0,'match_id':sources.match_id,'sources':sources.references,
            'opendota_parse_status':sources.opendota.get('od_data'),
            'participant_id_gaps':[slot for slot,p in od.items() if p.get('account_id') is None],
            'participants':players,'final_comparisons':len(players)*len(FINAL_FIELDS),
            'disagreements':disagreements,
            'not_requested':['STRATZ profile histories','hero reference details','meta'],
            'limitations':['Empty event arrays do not prove absence in the game.',
                           'Visibility, full state and event completeness are not established.']}
