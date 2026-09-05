"""Callable analysis services, independent of CLI and model transport."""
from collections.abc import Callable

from .enums import Level, Support
from .schemas import Finding, inherit_limits
from .sources import Sources
from .facts import event_evidence
from .episodes import interval_metrics
from .timebases import in_interval
from .synthesis import prepare_analysis, accept_analysis, read_analysis, validate_analysis


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
    if episode['kind']=='unavailable':
        card.update(support=Support.INSUFFICIENT.value,observation='Parsed playback unavailable; no episode conclusions supported.')
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
    if not facts['context']['playback_available']:
        card.update(support=Support.INSUFFICIENT.value,observation='Stage events unavailable; final totals do not reconstruct the course of play.')
    return card


def summarize_match(*, sources: Sources, facts: dict, stages: list[dict], episodes: list[dict]) -> dict:
    slot=facts['context']['target_slot']
    target=next(p for p in facts['context']['roster'] if p['playerSlot']==slot)
    deaths=[e for e in facts['events'] if e['kind']=='death' and e['slot']==slot]
    longest=sorted(deaths,key=lambda e:e['data'].get('timeDead') or 0,reverse=True)[:3]
    candidates=[c for c in episodes if c.get('kind')=='risk' and any(e['id'] in c.get('anchors',[]) for e in longest)]
    priorities=[{'question':'Which decisions preceded the largest recorded periods spent dead?',
                 'episode_ids':[c['id'] for c in candidates],
                 'expected_use':'Find reviewable decisions with measurable consequences, without equating death with error.',
                 'verification':'Inspect pre-death context and a positive/control episode; record one observable decision to test next match.',
                 'status':'review_candidate; no error established'}]
    total_dead=sum(min(max(0,e['data'].get('timeDead') or 0),max(0,facts['context']['duration']-e['time'])) for e in deaths)
    death_available=facts['context']['journal_available']['death']
    if not death_available:
        total_dead=None
        priorities=[]
    card=Finding(id=f'{sources.match_id}:match',level=Level.MATCH,match_ids=[sources.match_id],account_id=sources.account_id,
                 observation=f"Hero {target['heroId']}, {target['position']}: {target['kills']}/{target['deaths']}/{target['assists']}, "
                             f"{target['numLastHits']} last hits. No meta-based rating applied.",
                 evidence=[sources.ref('stratz/overview','/data/match/players')],children=[s['id'] for s in stages],
                 metrics={'target':target,'recorded_dead_seconds':total_dead,'death_journal_count':len(deaths) if death_available else None,
                          'longest_deaths':[{'time':e['time'],'time_dead':e['data'].get('timeDead'),'evidence':event_evidence(sources,e)} for e in longest],
                          'stage_counts':[{'id':s['id'],'interval':s['interval'],'counts':s['metrics']['counts']} for s in stages]},
                 limitations=inherit_limits(stages,['High resource or damage totals alone do not establish good decisions.']),
                 verify=['Review candidate episodes and record testable recommendations through the model response workflow.']).to_dict()
    card.update({'context':facts['context'],'priorities':priorities,'interpretation_status':'awaiting_model_review'})
    if not facts['context']['playback_available']:
        card['support']=Support.INSUFFICIENT.value
    return card
