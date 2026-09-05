"""Offline field audit for task 4; not the future metric calculation engine."""
import json
from collections import Counter
from pathlib import Path

from src.apps.analysis.sources import load_sources


FIELDS = {
    'st.match': 'startDateTime durationSeconds didRadiantWin gameMode gameVersionId rank averageRank radiantExperienceLeads radiantNetworthLeads towerDeaths.time towerDeaths.npcId towerDeaths.attacker pickBans laneReport',
    'st.player': 'heroId position lane role isRadiant isVictory partyId kills deaths assists numLastHits numDenies goldPerMinute experiencePerMinute networth level heroDamage towerDamage heroHealing',
    'st.stats': 'wards.time wards.type wards.positionX wards.positionY wardDestruction.time wardDestruction.isWard campStack actionsPerMinute actionReport.scanUsed actionReport.pingUsed farmDistributionReport abilityCastReport heroDamageReport inventoryReport networthPerMinute experiencePerMinute goldPerMinute locationReport',
    'st.playback': 'experienceEvents.time experienceEvents.amount experienceEvents.reason goldEvents.time goldEvents.amount goldEvents.reason goldEvents.isValidForStats playerUpdateGoldEvents.time playerUpdateGoldEvents.networth playerUpdateGoldEvents.gold playerUpdateGoldEvents.unreliableGold playerUpdateLevelEvents.time playerUpdateLevelEvents.level playerUpdatePositionEvents.time playerUpdatePositionEvents.x playerUpdatePositionEvents.y playerUpdateHealthEvents.hp playerUpdateHealthEvents.maxHp playerUpdateHealthEvents.mp playerUpdateHealthEvents.maxMp deathEvents.time deathEvents.timeDead deathEvents.goldLost deathEvents.xpFed deathEvents.attacker killEvents.time assistEvents.time csEvents.time csEvents.isNeutral csEvents.isAncient csEvents.isCreep csEvents.gold csEvents.xp healEvents.time healEvents.value healEvents.target heroDamageEvents.time heroDamageEvents.value heroDamageEvents.target heroDamageEvents.attacker towerDamageEvents.time towerDamageEvents.damage towerDamageEvents.npcId purchaseEvents.time purchaseEvents.itemId itemUsedEvents.time itemUsedEvents.itemId abilityUsedEvents.time abilityUsedEvents.abilityId abilityUsedEvents.target abilityLearnEvents.time inventoryEvents.time buyBackEvents.time buyBackEvents.cost buyBackEvents.deathTimeRemaining',
    'od.match': 'start_time duration radiant_win average_rank patch objectives teamfights radiant_gold_adv radiant_xp_adv',
    'od.player': 'kills deaths assists last_hits denies gold_per_min xp_per_min net_worth hero_damage tower_damage hero_healing party_size times xp_t gold_t obs_log sen_log obs_left_log sen_left_log stuns purchase_log life_state_dead',
}
MISSING = object()


def values_at(value: object, parts: list[str]) -> list:
    if value is MISSING or value is None:
        return [value]
    if isinstance(value, list):
        return [item for entry in value for item in values_at(entry, parts)] if value else [value]
    if not parts:
        return [value]
    return values_at(value.get(parts[0], MISSING), parts[1:]) if isinstance(value, dict) else [MISSING]


def state(value: object) -> str:
    if value is MISSING:
        return 'missing'
    if value is None:
        return 'null'
    if value is False:
        return 'false'
    if value == [] or value == {}:
        return 'empty'
    if type(value) in (int, float) and value == 0:
        return 'zero'
    return 'value'


def build_audit(root: Path) -> dict:
    selection = json.loads((root / 'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    fields = {f'{group}.{path}': {'states_by_match': {}, 'element_states': Counter(), 'numeric_range': None}
              for group, paths in FIELDS.items() for path in paths.split()}
    matches = []
    pairs = [('kills', 'kills'), ('deaths', 'deaths'), ('assists', 'assists'),
             ('numLastHits', 'last_hits'), ('numDenies', 'denies'), ('goldPerMinute', 'gold_per_min'),
             ('experiencePerMinute', 'xp_per_min'), ('networth', 'net_worth'),
             ('heroDamage', 'hero_damage'), ('towerDamage', 'tower_damage'), ('heroHealing', 'hero_healing')]
    for mid in selection['lower_outputs']:
        sources = load_sources(root=root, match_id=int(mid), account_id=selection['account_id'])
        st, od = sources.stratz, sources.opendota
        p = next(p for p in st['players'] if p['steamAccountId'] == selection['account_id'])
        q = next(p for p in od['players'] if p.get('account_id') == selection['account_id'])
        pb = p.get('playbackData') or {}
        groups = {'st.match': st, 'st.player': p, 'st.stats': p.get('stats') or {},
                  'st.playback': pb, 'od.match': od, 'od.player': q}
        for group, paths in FIELDS.items():
            for path in paths.split():
                row = fields[f'{group}.{path}']
                values = values_at(groups[group], path.split('.'))
                counts = Counter(map(state, values))
                row['states_by_match'][mid] = sorted(counts)
                row['element_states'].update(counts)
                nums = [v for v in values if type(v) in (int, float)]
                if nums:
                    previous = row['numeric_range'] or []
                    row['numeric_range'] = [min([*nums, *previous]), max([*nums, *previous])]
        checks = {}
        for journal, final in [('killEvents', 'kills'), ('deathEvents', 'deaths'),
                               ('assistEvents', 'assists'), ('csEvents', 'numLastHits')]:
            events = pb.get(journal)
            checks[journal] = {'journal_count': len(events) if isinstance(events, list) else None,
                               'final': p.get(final), 'equal': isinstance(events, list) and len(events) == p.get(final)}
        xp = [e for e in pb.get('experienceEvents', []) if 0 <= e['time'] <= st['durationSeconds']]
        xp_by_reason = Counter()
        for e in xp:
            xp_by_reason[e['reason']] += e['amount']
        position_times = sorted(set(e['time'] for e in pb.get('playerUpdatePositionEvents', []) if e['time'] >= 0))
        journal_death_seconds = sum(e['timeDead'] for e in pb.get('deathEvents', []) if e.get('timeDead') is not None)
        death_intervals = sorted((max(0, e['time']), min(st['durationSeconds'], e['time'] + e['timeDead']))
                                 for e in pb.get('deathEvents', []) if e.get('timeDead') is not None)
        union_seconds, previous_end = 0, 0
        for start, end in death_intervals:
            union_seconds += max(0, end - max(previous_end, start))
            previous_end = max(previous_end, end)
        phase_counts = [sum(start <= e['time'] < (st['durationSeconds'] + 1 if start + 600 >= st['durationSeconds'] else start + 600)
                            for e in pb.get('deathEvents', []))
                        for start in range(0, st['durationSeconds'], 600)]
        mismatch = []
        for player in st['players']:
            other = next(x for x in od['players'] if x['player_slot'] == player['playerSlot'])
            mismatch.extend({'slot': player['playerSlot'], 'field': a, 'stratz': player.get(a), 'opendota': other.get(b)}
                            for a, b in pairs if player.get(a) != other.get(b))
        matches.append({'match_id': int(mid), 'start_time': st['startDateTime'], 'duration': st['durationSeconds'],
                        'hero_id': p['heroId'], 'position': p['position'], 'win': p['isVictory'],
                        'isStats': st['isStats'], 'playback_players': sum(bool(x.get('playbackData')) for x in st['players']),
                        'position_players': sum(bool((x.get('playbackData') or {}).get('playerUpdatePositionEvents')) for x in st['players']),
                        'economy_players': sum(bool((x.get('playbackData') or {}).get('playerUpdateGoldEvents')) for x in st['players']),
                        'journals': checks, 'source_final_disagreements': mismatch,
                        'death_seconds_reported': journal_death_seconds, 'od_life_state_dead': q.get('life_state_dead'),
                        'example_death_interval_union_seconds': union_seconds,
                        'example_death_phase_counts_600s': phase_counts,
                        'example_xp_first_600s': sum(e['amount'] for e in xp if e['time'] < 600),
                        'xp_journal_sum': sum(e['amount'] for e in xp), 'xp_by_reason': dict(xp_by_reason),
                        'xpm_reported': p['experiencePerMinute'], 'xp_from_rounded_xpm': p['experiencePerMinute'] * st['durationSeconds'] / 60,
                        'position_max_observation_gap_seconds': max((b-a for a,b in zip(position_times, position_times[1:])), default=None),
                        'final': {a: p.get(a) for a,b in pairs},
                        'sources': sources.references})
    for row in fields.values():
        row['matches_with_numeric_or_value'] = sum(bool(set(states) & {'value', 'zero', 'false'}) for states in row['states_by_match'].values())
        row['matches_with_empty'] = sum('empty' in states for states in row['states_by_match'].values())
        row['matches_with_missing_or_null'] = sum(bool(set(states) & {'missing', 'null'}) for states in row['states_by_match'].values())
    return {'audit_version': 'catalog-audit-1', 'account_id': selection['account_id'], 'real_matches': len(matches),
            'new_matches_fetched': 0, 'scope': 'Observed local payload values; availability does not establish completeness or field semantics.',
            'field_path_convention': 'Target player only unless st.match/od.match. Dots traverse objects and every list element. Empty ancestors remain empty; missing and null propagate.',
            'fields': fields, 'matches': matches}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_audit(Path.cwd())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'real_matches': result['real_matches'], 'fields': len(result['fields']),
                      'new_matches_fetched': 0, 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
