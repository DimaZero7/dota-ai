"""L1 preserves original clocks, source states and event indices."""
from ..coverage import field_state, FINAL_FIELDS
from ..sources import Sources
from .schemas import NumericError, measurement, node, number, quality

JOURNALS = {
    'gold': ('goldEvents', ('time', 'amount')), 'xp': ('experienceEvents', ('time', 'amount')),
    'farm': ('csEvents', ('time',)), 'death': ('deathEvents', ('time', 'timeDead')),
    'kill': ('killEvents', ('time',)), 'assist': ('assistEvents', ('time',)),
    'damage': ('heroDamageEvents', ('time', 'value')), 'heal': ('healEvents', ('time', 'value')),
    'tower_damage': ('towerDamageEvents', ('time', 'damage')),
    'purchase': ('purchaseEvents', ('time', 'itemId')), 'item': ('itemUsedEvents', ('time', 'itemId')),
    'ability': ('abilityUsedEvents', ('time', 'abilityId')), 'level': ('playerUpdateLevelEvents', ('time', 'level')),
    'economy': ('playerUpdateGoldEvents', ('time', 'networth')), 'position': ('playerUpdatePositionEvents', ('time', 'x', 'y')),
    'health': ('playerUpdateHealthEvents', ('time', 'hp', 'maxHp', 'mp', 'maxMp')),
    'buyback': ('buyBackEvents', ('time',)),
}


def journal(record: dict, field: str, required: tuple[str, ...], ref: dict) -> dict:
    state = field_state(record, field)
    raw = record.get(field)
    if raw is not None and not isinstance(raw, list):
        state = 'malformed'
    rows, invalid = [], 0
    for i, event in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(event, dict) or any(not number(event.get(k)) for k in required):
            invalid += 1
            continue
        rows.append({**event, '_source_index': i})
    rows.sort(key=lambda e: (e['time'], e['_source_index']))
    q=quality(state=state, invalid=invalid)
    q.update(raw_events=len(raw) if isinstance(raw,list) else None, valid_events=len(rows),
             first_time=rows[0]['time'] if rows else None,last_time=rows[-1]['time'] if rows else None)
    return {'quality': q, 'events': rows, 'source_ref': ref,
            'raw_count': len(raw) if isinstance(raw, list) else None}


def build_numeric_facts(sources: Sources) -> dict:
    st, od = sources.stratz, sources.opendota
    target = next(p for p in st['players'] if p.get('steamAccountId') == sources.account_id)
    duration = st.get('durationSeconds')
    if type(duration) is not int or duration <= 0:
        raise NumericError('Positive match duration required')
    roster_keys = ('playerSlot', 'heroId', 'isRadiant', 'position', 'lane', 'role', 'kills', 'deaths', 'assists',
                   'numLastHits', 'numDenies', 'goldPerMinute', 'experiencePerMinute', 'networth', 'level',
                   'heroDamage', 'towerDamage', 'heroHealing')
    roster = [{k: p.get(k) for k in roster_keys} for p in st['players']]
    if len({p['playerSlot'] for p in roster}) != 10 or any(type(p['isRadiant']) is not bool for p in roster):
        raise NumericError('Ten participants with known sides required')
    context = {'account_id': sources.account_id, 'match_id': sources.match_id, 'target_slot': target['playerSlot'],
               'hero_id': target['heroId'], 'position': target.get('position'), 'lane': target.get('lane'),
               'position_origin': 'STRATZ estimate', 'duration': duration, 'start_time': st['startDateTime'],
               'win': target['isRadiant'] == st['didRadiantWin'], 'roster': roster,
               'mode': st.get('gameMode'), 'rank': {'stratz': st.get('rank'), 'opendota_average': od.get('average_rank'),
                                                'meaning': 'source estimates; not verified individual match-time rank'},
               'patch_ids': {'stratz': st.get('gameVersionId'), 'opendota': od.get('patch')},
               'map_transform': 'unvalidated', 'meta_applied': False}
    target_slot = target['playerSlot']
    journals, all_players = {}, {}
    for key, document in sources.documents.items():
        if not key.startswith('stratz/playback-'):
            continue
        for index, p in enumerate(document['data']['match']['players']):
            slot = p['playerSlot']
            original = next(x for x in roster if x['playerSlot'] == slot)
            if p['heroId'] != original['heroId']:
                raise NumericError('Playback identity mismatch')
            raw = p.get('playbackData') or {}
            fields = JOURNALS if slot == target_slot else {k: JOURNALS[k] for k in ('economy', 'level', 'position', 'xp')}
            parsed = {name: journal(raw, field, required, sources.ref(key, f'/data/match/players/{index}/playbackData/{field}'))
                      for name, (field, required) in fields.items()}
            all_players[str(slot)] = {k: parsed[k] for k in ('economy', 'level', 'position', 'xp')}
            if slot == target_slot:
                journals.update(parsed)
    if set(all_players) != {str(p['playerSlot']) for p in roster}:
        raise NumericError('Missing participant playback document')
    for kind, final in [('kill', 'kills'), ('death', 'deaths'), ('assist', 'assists'), ('farm', 'numLastHits')]:
        j = journals[kind]
        expected = target.get(final)
        j['reconciliation'] = {'journal': j['raw_count'], 'final': expected,
                                'equal': j['raw_count'] is not None and number(expected) and j['raw_count'] == expected}
        if not j['reconciliation']['equal']:
            j['quality'].update(status='conflicting' if j['quality']['status'] != 'unavailable' else 'unavailable',
                                eligible=False, reason='journal/final disagreement or missing final')
    death_bad = sum(e['timeDead'] < 0 for e in journals['death']['events'])
    if death_bad:
        journals['death']['quality'].update(status='conflicting', eligible=False, reason='negative timeDead')
    level_rows=journals['level']['events']
    if any(e['level']<1 for e in level_rows) or any(b['level']<a['level'] for a,b in zip(level_rows,level_rows[1:])) or (level_rows and level_rows[-1]['level']!=target.get('level')):
        journals['level']['quality'].update(status='conflicting',eligible=False,reason='non-monotone levels or final-level disagreement')
    # Preserve source estimates but do not silently choose one conflicting final total.
    final_conflicts = []
    for p in roster:
        other = next(x for x in od['players'] if x['player_slot'] == p['playerSlot'])
        for left, right in FINAL_FIELDS:
            if not number(p.get(right)) or not number(other.get(left)) or p[right] != other[left]:
                final_conflicts.append({'slot': p['playerSlot'], 'field': right, 'stratz': p.get(right), 'opendota': other.get(left)})
    stats_index = next(i for i,p in enumerate(sources.documents['stratz/stats']['data']['match']['players']) if p['playerSlot'] == target_slot)
    stats = target.get('stats') or {}
    for name, field, required in [('wards','wards',('time','type','positionX','positionY')),
                                  ('ward_destruction','wardDestruction',('time',))]:
        journals[name] = journal(stats, field, required, sources.ref('stratz/stats', f'/data/match/players/{stats_index}/stats/{field}'))
    journals['objects'] = journal(st, 'towerDeaths', ('time','npcId'), sources.ref('stratz/overview','/data/match/towerDeaths'))
    actions=stats.get('actionReport') or {}
    support_actions={'scan_used':actions.get('scanUsed'),'ping_used':actions.get('pingUsed'),
                     'camp_stack':None,'camp_stack_reason':'minute-vector semantics unvalidated',
                     'source_ref':sources.ref('stratz/stats',f'/data/match/players/{stats_index}/stats/actionReport')}
    m = [measurement('context.match', context, 'record', kind='source_observation', provenance=[sources.ref('stratz/overview','/data/match')]),
         measurement('economy.networth', {'journal_ref': 'players/*/economy'}, 'gold', kind='source_observation', q=journals['economy']['quality']),
         measurement('space.observations', {'journal_ref': 'players/*/position'}, 'source coordinates', kind='source_observation', q=journals['position']['quality'])]
    return node(level=1, context=context, measurements=m, source_manifest=sources.references, children=[],
                payload={'context': context, 'sources': sources.references, 'journals': journals, 'players': all_players,
                         'final_conflicts': final_conflicts, 'support_actions':support_actions,
                         'source_clock': 'STRATZ event seconds; no OD event joins'})
