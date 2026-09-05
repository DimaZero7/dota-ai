"""Prospective exercises with recorded baselines and explicit untested status."""
from copy import deepcopy
from .comparison import cohort_key


def plan_training(profile: dict, patterns: list[dict]) -> dict:
    result=deepcopy(profile)
    candidates=[p for p in patterns if p.get('metrics',{}).get('match_count',0)>=2
                and p.get('metrics',{}).get('numerator',0)>0 and p.get('support')=='hypothesis']
    priorities=[]
    for pattern in candidates[:1]:
        m=pattern['metrics']; c=pattern['context']
        priorities.append({'id':pattern['id']+':reassess','pattern_id':pattern['id'],
            'context':{'hero_id':c['hero_id'],'hero_name':c['hero_name'],'position':c['position']},
            'status':'untested','exercise':'After a kill, explicitly reassess the next objective, known enemy threats and current resources before choosing to continue or disengage.',
            'expected_use':'Make the decision explainable and identify avoidable exposure without discouraging useful fights.',
            'baseline':{'numerator':m['numerator'],'denominator':m['denominator'],'horizon_seconds':m['horizon_seconds'],
                        'distinct_following_deaths':m['distinct_following_deaths'],'match_ids':pattern['match_ids'],
                        'cohort_key':c['cohort_key'],'last_start_time':max(x['start_time'] for x in c['match_contexts'])},
            'process_measure':'Manually annotate the first 10 eligible post-kill situations in future compatible games: information available, decision, alternative, outcome. Unknown information stays unknown.',
            'process_target':'10 documented opportunities; this is a completion target, not a skill norm.',
            'outcome_measure':'Repeat the same post-kill death frequency, distinct death count and qualitative team-trade review. Lower frequency alone is not success.',
            'followup_match_ids':[],'result':'No prospective follow-up yet; effectiveness unknown.'})
    result['metrics']['training_priorities']=priorities
    result['metrics']['followup_status']='untested' if priorities else 'no_supported_training_candidate'
    return result


def evaluate_followup(priority: dict, followup_rows: list[dict]) -> dict:
    baseline=priority['baseline']; context=priority['context']
    if any(r['match_id'] in baseline['match_ids'] for r in followup_rows):
        raise ValueError('Baseline games cannot be counted as prospective follow-up')
    ids=[r['match_id'] for r in followup_rows]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate follow-up match')
    if any(not r['eligible'] or r['context']['hero_id']!=context['hero_id']
           or r['context']['position']!=context['position'] or r['horizon_seconds']!=baseline['horizon_seconds']
           or list(cohort_key(r['context']))!=baseline['cohort_key']
           or r['context']['start_time']<=baseline['last_start_time'] for r in followup_rows):
        raise ValueError('Follow-up context or measurement differs')
    if not followup_rows:
        return {'status':'untested','match_ids':[],'result':'No prospective follow-up supplied.'}
    n=sum(r['numerator'] for r in followup_rows); d=sum(r['denominator'] for r in followup_rows)
    return {'status':'observed_followup_only','match_ids':ids,'numerator':n,'denominator':d,'fraction':n/d if d else None,
            'effectiveness':'Not established by an uncontrolled before/after comparison.'}
