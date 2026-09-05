"""Small source-linked measurement windows for a human/current-Codex analyst."""
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

from .sources import load_sources
from .storage import load_artifact
from .synthesis import register_measurement, prepare_analysis

LIMITS = [
    'Source position is estimated; same-position economy is not verified lane performance.',
    'Selected intervals do not reconstruct every decision; visibility, cooldowns and intent remain unknown.',
    'No meta or rank-adjusted reference population. Deaths and high totals alone do not establish mistakes or skill.',
]


def prepare_match_dossiers(*, root: Path, store: Path, lower_output: Path,
                           match_id: int, account_id: int, critical_interval: list[int]) -> list[dict]:
    data = load_artifact(lower_output)
    if data is None:
        raise ValueError('Verified lower-level cache required')
    sources = load_sources(root=root, match_id=match_id, account_id=account_id)
    facts = data['facts']; c = facts['context']; slot = c['target_slot']
    if data['match_id'] != match_id or facts['account_id'] != account_id:
        raise ValueError('Wrong match/account')
    # Cached facts must still describe exactly these immutable source documents.
    if data['registry'][f'{match_id}:sources']['evidence'] != [sources.ref(k,'') for k in sources.references]:
        raise ValueError('Cached facts refer to different source snapshots')
    target = next(p for p in c['roster'] if p['playerSlot'] == slot)
    allies = [p for p in c['roster'] if p['isRadiant'] == target['isRadiant']]
    enemies = [p for p in c['roster'] if p['isRadiant'] != target['isRadiant']]
    counterpart = [p for p in enemies if p['position'] == target['position']]
    counterpart = counterpart[0] if len(counterpart) == 1 else None
    economy = defaultdict(list)
    own = []
    for event in facts['events']:
        if event['kind'] == 'economy': economy[event['slot']].append(event)
        if event['slot'] == slot: own.append(event)
    times = {key: [e['time'] for e in values] for key, values in economy.items()}
    def nw(s: int, t: int) -> int | None:
        index = bisect_right(times[s], t)-1
        if index < 0: return None
        event = economy[s][index]
        return event['data'].get('networth') if t-event['time'] <= 5 else None
    def snapshot(t: int) -> dict:
        a = [nw(p['playerSlot'], t) for p in allies]
        b = [nw(p['playerSlot'], t) for p in enemies]
        player = nw(slot, t)
        other = nw(counterpart['playerSlot'], t) if counterpart else None
        return {'time': t, 'own_nw': player, 'counterpart_nw': other,
                'own_minus_counterpart': player-other if player is not None and other is not None else None,
                'team_nw_lead': sum(a)-sum(b) if all(v is not None for v in a+b) else None}
    duration = c['duration']
    if not 0 <= critical_interval[0] < critical_interval[1] <= duration+1:
        raise ValueError('Invalid selected critical interval')
    windows = [('opening', 0, min(601,duration+1)),
               ('transition', min(601,duration), min(1201,duration+1)),
               ('development', min(1201,duration), duration+1),
               ('critical', *critical_interval)]
    context = {'hero': c['hero_name'], 'position': c['position'], 'lane': c['lane'],
               'drafts': [{k: p[k] for k in ('hero_name','position','isRadiant')} for p in c['roster']],
               'own_is_radiant': target['isRadiant'], 'duration': duration,
               'win': c['did_radiant_win'] == target['isRadiant'],
               'patch_ids': c['patch_ids'], 'meta_applied': False,
               'counterpart': counterpart['hero_name'] if counterpart else None}
    packets = []
    for label, start, end in windows:
        events = [e for e in own if start <= e['time'] < end]
        counts = Counter(e['kind'] for e in events)
        points = sorted({min(start, duration), min(end-1,duration)}
                        | {t for t in range(600,duration+1,600) if start <= t < end})
        documents = set(e['document'] for e in facts['events'] if e['kind'] == 'economy')
        documents.update(e['document'] for e in events)
        refs = [sources.ref('stratz/overview','/data/match')]
        refs += [sources.ref(key,'') for key in sorted(documents)]
        payload = {'context': context, 'interval': [start,end],
                   'method': 'Native source seconds, half-open interval. NW last observation <= time, maximum age 5s. Counts are journal events, not final totals.',
                   'snapshots': [snapshot(t) for t in points],
                   'counts': {k: counts[k] if c['journal_available'].get(k) else None for k in ('kill','death','assist','last_hit')},
                   'deaths': [{'time': e['time'], 'attacker_hero_id': e['data'].get('attacker'),
                               'time_dead': e['data'].get('timeDead')} for e in events if e['kind']=='death'],
                   'kills': [e['time'] for e in events if e['kind']=='kill'],
                   'journal_vs_total': data['validation']['journal_vs_total']}
        if label == 'development':
            payload['final'] = {k: target[k] for k in ('kills','deaths','assists','numLastHits','heroDamage','towerDamage','networth')}
            payload['team_final'] = {k: sum(p[k] for p in allies) for k in ('kills','heroDamage','towerDamage')}
        register_measurement(store=store, node_id=f'{match_id}:facts:{label}', match_id=match_id,
                             payload=payload, source_refs=refs, root=root, limitations=LIMITS)
        packets.append(prepare_analysis(store=store, node_id=f'{match_id}:L2:{label}', level=2,
            child_ids=[f'{match_id}:facts:{label}'],
            question='What does this selected sequence suggest about how this player obtains resources, participates, or handles pressure? Explain outcomes, alternatives and missing information.'))
    return packets
