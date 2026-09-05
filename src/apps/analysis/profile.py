"""Level 6: a conditional evidence inventory, not a psychological diagnosis."""
from .schemas import Finding, inherit_limits
from .enums import Level, Support
from .evidence import digest


def build_profile(patterns: list[dict], *, account_id: int) -> dict:
    if not patterns or any(p['account_id']!=account_id for p in patterns):
        raise ValueError('Profile requires patterns from the requested player')
    matches=sorted({mid for p in patterns for mid in p['match_ids']})
    contexts={m['match_id']:m for p in patterns for m in p.get('context',{}).get('match_contexts',[])}
    conditions=[{'pattern_id':p['id'],'hero':p.get('context',{}).get('hero_name'),
                 'position':p.get('context',{}).get('position'),'match_ids':p['match_ids'],
                 'classification':p.get('metrics',{}).get('classification','insufficient_data'),
                 'numerator':p.get('metrics',{}).get('numerator'),'denominator':p.get('metrics',{}).get('denominator'),
                 'status':p['support']} for p in patterns]
    card=Finding(id=f'profile:{account_id}:{digest(matches)[:12]}',level=Level.PROFILE,
        match_ids=matches,account_id=account_id,support=Support.INSUFFICIENT,
        observation=f'{len(matches)} prototype matches support a conditional review agenda; stable style and psychological traits are not established.',
        evidence=[],children=[p['id'] for p in patterns],
        metrics={'conditions':conditions,'stable_traits':[],'psychological_inferences':[],
                 'profile_status':'insufficient_for_stable_style','meta_applied':False},
        limitations=inherit_limits(patterns,['No psychological traits, intentions or diagnoses can be inferred from these event counts.',
                                            'A review priority is an experiment, not a confirmed weakness.']),
        verify=['Collect prospective evidence only under explicit collection limits; keep incompatible heroes and positions separate.']).to_dict()
    card['context']={'account_id':account_id,'match_contexts':list(contexts.values()),'meta_applied':False}
    return card
