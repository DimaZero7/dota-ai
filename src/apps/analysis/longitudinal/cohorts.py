"""Explicit comparison strata, outcome contrasts and composition-aware recent periods."""
from collections import Counter, defaultdict

from ..evidence import digest
from ..numeric.schemas import number
from .schemas import CORE_CONTEXT
from .statistics import distribution, describe


def composition(rows: list[dict]) -> dict:
    return {key:dict(sorted(Counter(str(r['context'].get(key)) for r in rows).items()))
            for key in ('hero_id','position','side','mode','rank_band','stratz_version','opendota_version')}


def _summary(entries: list[dict]) -> dict:
    keys=sorted(set().union(*(e['metrics'].keys() for e in entries)))
    outcomes={True:[e for e in entries if e['row']['win'] is True],False:[e for e in entries if e['row']['win'] is False]}
    metrics={k:distribution([e['metrics'].get(k) for e in entries]) for k in keys}
    comparisons={}
    for key in keys:
        w=distribution([e['metrics'].get(key) for e in outcomes[True]])
        l=distribution([e['metrics'].get(key) for e in outcomes[False]])
        comparisons[key]={'wins':w,'losses':l,'mean_win_minus_loss':w['mean']-l['mean'] if w['mean'] is not None and l['mean'] is not None else None,
                          'pooled_win_minus_loss':w['pooled_value']-l['pooled_value'] if w['pooled_value'] is not None and l['pooled_value'] is not None else None,
                          'minimum_outcome_sample_met':w['n']>=5 and l['n']>=5,
                          'inference':'descriptive; outcome contrasts do not establish cause or predictability'}
    return {'n':len(entries),'wins':len(outcomes[True]),'losses':len(outcomes[False]),
            'unknown_outcomes':len(entries)-len(outcomes[True])-len(outcomes[False]),'metrics':metrics,
            'outcome_comparisons':comparisons,'duration_seconds':describe([e['row']['duration'] for e in entries]),
            'composition':composition([e['row'] for e in entries]),
            'distinct_drafts':len({digest([e['row']['context'].get('draft_allies'),e['row']['context'].get('draft_enemies')]) for e in entries})}


def build_cohorts(rows: list[dict]) -> tuple[list[dict],dict]:
    groups=defaultdict(list);scopes={}
    def add(row: dict, kind: str, metrics: dict, extra: dict | None = None, relaxed: bool = False) -> None:
        required=('hero_id','position','mode','stratz_version','opendota_version') if relaxed else CORE_CONTEXT
        scope={k:row['context'].get(k) for k in required}
        if kind=='match' and not relaxed:scope['duration_band']=row['context']['duration_band']
        scope.update(extra or {});scope['kind']=kind;scope['grouping']='hero_position_relaxed' if relaxed else 'strict'
        unknown=[k for k in required if scope[k] is None]
        if scope.get('state') in (None,'unknown') and kind!='match':unknown.append('state')
        # Unverified source versions cannot silently pool across matches.
        if scope.get('stratz_version') is None or scope.get('opendota_version') is None:scope['unknown_version_match']=row['match_id']
        key=digest(scope)[:20];scopes[key]=(scope,unknown)
        groups[key].append({'row':row,'metrics':metrics})
    for row in rows:
        add(row,'match',row['metrics']);add(row,'match',row['metrics'],relaxed=True)
        for p in row['phases']:
            extra={k:p[k] for k in ('phase','complete_phase','state','state_basis')}
            add(row,'phase',p['metrics'],extra)
        for p in row['death_states']:
            extra={k:p[k] for k in ('phase','complete_phase','state','state_basis')}
            add(row,'death_state',p['metrics'],extra)
    outputs=[]
    for key,entries in sorted(groups.items()):
        # One row per match in every comparison; repeated episodes never add outcomes.
        if len({e['row']['match_id'] for e in entries})!=len(entries):raise ValueError('Repeated match in comparison stratum')
        scope,unknown=scopes[key]
        relaxed=scope['grouping']!='strict'
        outputs.append({'id':key,'scope':scope,'unknown_conditions':unknown,'comparison_eligible':not unknown and not relaxed,
                        'relaxed_conditions':['side','rank_band','duration_band'] if relaxed else [],
                        'uncontrolled_conditions':['full drafts','team decisions','source completeness','exact individual skill'],
                        'summary':_summary(entries),'drill_ref':f'cohort:{key}'})
    return outputs,dict(groups)


def recent_comparison(rows: list[dict], cohorts: list[dict], members: dict, *, recent_count: int = 3) -> dict:
    ordered=sorted((r for r in rows if number(r['start_time'])),key=lambda r:(r['start_time'],r['match_id']))
    if not 1<=recent_count<len(ordered):return {'status':'unavailable','reason':'Both historical and recent periods required'}
    recent=ordered[-recent_count:];history=ordered[:-recent_count];ids={r['match_id'] for r in recent}
    comparisons=[]
    for cohort in cohorts:
        if cohort['scope']['kind']!='match' or not cohort['comparison_eligible']:continue
        entries=members[cohort['id']];a=[e for e in entries if e['row']['match_id'] not in ids];b=[e for e in entries if e['row']['match_id'] in ids]
        if not a or not b:continue
        keys=sorted(set().union(*(e['metrics'].keys() for e in entries)));metrics={}
        for key in keys:
            old=distribution([e['metrics'].get(key) for e in a]);new=distribution([e['metrics'].get(key) for e in b])
            metrics[key]={'history':old,'recent':new,'mean_change':new['mean']-old['mean'] if old['mean'] is not None and new['mean'] is not None else None,
                          'coverage_change':new['coverage']-old['coverage'] if old['coverage'] is not None and new['coverage'] is not None else None}
        comparisons.append({'cohort_ref':cohort['id'],'scope':cohort['scope'],'history_n':len(a),'recent_n':len(b),'metrics':metrics})
    return {'status':'observed','history_n':len(history),'recent_n':len(recent),'recent_start_time':recent[0]['start_time'],
            'history_composition':composition(history),'recent_composition':composition(recent),'matched_groups':comparisons,
            'matched_group_count':len(comparisons),'unknown_clock_rows':len(rows)-len(ordered),
            'interpretation':'Recent is disjoint from historical baseline; composition/coverage changes are not skill changes'}
