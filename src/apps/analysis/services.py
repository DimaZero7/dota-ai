"""Callable analysis services, independent of CLI and model transport."""
from collections.abc import Callable

from .enums import Level, Support
from .schemas import Finding, inherit_limits
from .sources import Sources
from .facts import event_evidence
from .episodes import interval_metrics


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
