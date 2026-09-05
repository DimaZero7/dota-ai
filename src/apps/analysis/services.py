"""Callable analysis services, independent of CLI and model transport."""
from collections.abc import Callable

from .enums import Level, Support
from .schemas import Finding, inherit_limits
from .sources import Sources
from .facts import event_evidence
from .episodes import interval_metrics
from .timebases import in_interval


def analyze_episode(*, sources: Sources, facts: dict, episode: dict,
                    interpret: Callable[[dict], dict] | None = None) -> dict:
    by_id = {e['id']:e for e in facts['events']}
    anchors = [by_id[x] for x in episode['anchors']]
    evidence = [event_evidence(sources,e) for e in anchors]
    evidence.append(sources.ref('stratz/overview','/data/match/players'))
    metrics = interval_metrics(facts,episode)
    counts = metrics['counts']
    card = Finding(id=episode['id'],level=Level.EPISODES,match_ids=[sources.match_id],
                   account_id=sources.account_id,interval=(episode['start'],episode['end']),
                   observation=f"{episode['kind']}: [{episode['start']:.1f}, {episode['end']:.1f}) s; "
                               f"target recorded kills={counts.get('kill',0)}, deaths={counts.get('death',0)}, last_hits={counts.get('last_hit',0)}.",
                   evidence=evidence,metrics=metrics,
                   limitations=inherit_limits([facts],['No complete visibility/cooldown state. Interval overlap is not causal evidence.']),
                   verify=['Inspect before/after the anchor; compare with a control episode and both drafts.']).to_dict()
    card.update({'kind':episode['kind'],'context':facts['context'],'anchors':episode['anchors'],
                 'boundary_reason':episode['boundary_reason'],'interpretation_origin':'deterministic factual summary'})
    if interpret is not None:
        interpretation = interpret(card)
        if not isinstance(interpretation,dict):
            raise ValueError('Interpreter must return structured output')
        # Interpretations remain separate, never overwrite source facts.
        card['interpretation'] = interpretation
        card['interpretation_origin'] = 'external interpreter; validation required before promotion'
    return card


def summarize_phase(*, sources: Sources, facts: dict, phase: dict, cards: list[dict]) -> dict:
    children=[c for c in cards if c['id'] in phase['children']]
    slot=facts['context']['target_slot']
    economy=[e for e in facts['events'] if e['slot']==slot and e['kind']=='economy']
    before=[e for e in economy if e['time']<=phase['start']]
    after=[e for e in economy if e['time']<phase['end']]
    snapshots={}
    for name,events,boundary in [('start',before,phase['start']),('end',after,phase['end'])]:
        if events:
            event=events[-1]
            snapshots[name]={'time':event['time'],'age_seconds':boundary-event['time'],
                             'networth':event['data'].get('networth'),'evidence':event_evidence(sources,event)}
    purchases=[{'time':e['time'],'item_id':e['data'].get('itemId'),'evidence':event_evidence(sources,e)}
               for e in facts['events'] if e['slot']==slot and e['kind']=='purchase'
               and in_interval(e['time'],phase['start'],phase['end'])]
    metrics={**phase['metrics'],'economy_snapshots':snapshots,'purchases':purchases}
    counts=metrics['counts']
    card=Finding(id=phase['id'],level=Level.PHASES,match_ids=[sources.match_id],account_id=sources.account_id,
                 interval=(phase['start'],phase['end']),children=phase['children'],
                 observation=f"Stage [{phase['start']}, {phase['end']}) s: {counts.get('kill',0)} kills, "
                             f"{counts.get('death',0)} deaths, {counts.get('last_hit',0)} last hits recorded.",
                 evidence=[sources.ref('stratz/overview','/data/match')],metrics=metrics,
                 limitations=inherit_limits(children,phase['limitations']),
                 verify=['Review the referenced episodes before assigning strategic causes.']).to_dict()
    card.update({'boundary_reason':phase['boundary_reason'],'context':facts['context']})
    return card
