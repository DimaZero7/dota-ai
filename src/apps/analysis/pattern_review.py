"""Select falsifiable cross-match cases and revise hypotheses without rewriting evidence."""
from copy import deepcopy


def review_cases(pattern: dict) -> dict:
    windows=pattern.get('windows',[])
    supporting=next((w for w in windows if w['death_recorded']),None)
    # Prefer a counterexample from the same game to reduce context changes.
    controls=[w for w in windows if not w['death_recorded']]
    control=next((w for w in controls if supporting and w['match_id']==supporting['match_id']),next(iter(controls),None))
    return {'supporting':supporting,'control':control,
            'limitations':['A kill without a following death is an outcome contrast, not a matched counterfactual.']}


def revise_pattern(pattern: dict, *, verdict: str, reason: str, evidence_ids: list[str]) -> dict:
    if verdict not in ('retained_for_review','refined','rejected') or not reason.strip() or not evidence_ids:
        raise ValueError('Verdict, reason and evidence are required')
    allowed={pattern['id'],*pattern.get('children',[])}
    for w in pattern.get('windows',[]):
        allowed.update([w['id'],w['kill_event'],*w['death_events'],*w['episode_ids']])
    if not set(evidence_ids)<=allowed:
        raise ValueError('Revision cites unknown evidence')
    result=deepcopy(pattern)
    result.setdefault('review_history',[]).append({'verdict':verdict,'reason':reason,'evidence_ids':evidence_ids})
    if verdict=='rejected':
        result.update(hypothesis=None,support='insufficient_data')
    result['interpretation_status']=verdict
    return result
