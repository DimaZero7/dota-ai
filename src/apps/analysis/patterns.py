"""Level 5: conditional observations and falsifiable hypotheses."""
from .schemas import Finding, inherit_limits
from .enums import Level, Support


def build_patterns(comparison: dict, registry: dict) -> list[dict]:
    cards=[]
    for cohort in comparison['cohorts']:
        rows=cohort['matches']; windows=[w for r in rows for w in r['windows']]
        positive=[w for w in windows if w['death_recorded']]
        negative=[w for w in windows if not w['death_recorded']]
        ids=[r['finding_id'] for r in rows]; children=[registry[x] for x in ids]
        n=cohort['numerator']; d=cohort['denominator']; count=len(rows)
        status='single_match' if count==1 else 'preliminary'
        c=rows[0]['context']
        card=Finding(id=cohort['id'],level=Level.PATTERNS,match_ids=[r['match_id'] for r in rows],
            account_id=comparison['account_id'],observation=f"{c.get('hero_name') or c['hero_id']} {c['position']}: own death recorded within {cohort['horizon_seconds']} s after {n}/{d} eligible kills across {count} matches.",
            support=Support.HYPOTHESIS if n and count>1 else Support.INSUFFICIENT,
            hypothesis='Some post-kill situations may merit an earlier reassessment of continued exposure.' if n and count>1 else None,
            children=ids,evidence=[],counterexamples=[w['id'] for w in negative],
            alternatives=['Retaliation in an ongoing fight, a favorable trade, saving allies, or an unavoidable death.',
                          'Several kills may precede the same death; this is not several independent mistakes.'],
            limitations=inherit_limits(children,comparison['limitations']),
            verify=['Inspect a supporting window and a window without recorded death, including both drafts and prior events.',
                    'Reject the error claim unless player-visible options and likely team consequences support it.'],
            metrics={'numerator':n,'denominator':d,'fraction':cohort['fraction'],'match_count':count,
                     'horizon_seconds':cohort['horizon_seconds'],'classification':status,
                     'distinct_following_deaths':len({e for w in positive for e in w['death_events']}),
                     'by_match':[{'match_id':r['match_id'],'numerator':r['numerator'],'denominator':r['denominator'],
                                  'censored_kills':r['censored_kills']} for r in rows],
                     'support_windows':[w['id'] for w in positive], 'counterexample_count':len(negative)}).to_dict()
        card['context']={'cohort_key':cohort['key'],'hero_id':c['hero_id'],'hero_name':c.get('hero_name'),
                         'position':c['position'],'meta_applied':False,
                         'match_contexts':[{k:r['context'][k] for k in ('roster','patch_ids','rank_context','start_time','game_mode','lane')}|{'match_id':r['match_id']} for r in rows]}
        card['windows']=windows
        card['stability_policy']={'single_match':'one compatible game','preliminary':'two or more compatible prototype games',
            'more_stable':'Never assigned automatically in this prototype. Requires independent prospective evidence, stable context and explicit review of alternatives.'}
        cards.append(card)
    if not cards:
        cards.append(Finding(id='patterns:insufficient',level=Level.PATTERNS,match_ids=comparison['match_ids'],
            account_id=comparison['account_id'],observation='No comparable eligible matches.',support=Support.INSUFFICIENT,
            evidence=[],limitations=comparison['limitations']+['No eligible cohort.']).to_dict())
    return cards
