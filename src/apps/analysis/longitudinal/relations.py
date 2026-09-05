"""Fixed exploratory families with day blocking and chronological holdout."""
from collections import defaultdict
from datetime import datetime, timezone
import statistics
import math

from ..evidence import digest
from ..numeric.schemas import number
from .schemas import PARAMETERS
from .statistics import association, correlation, permutation_p, bonferroni

PAIRS=[('gold_rate','xp_rate'),('participation','post_combat_xp_change'),
       ('repeat_death_fraction','death_fraction'),('purchase_damage_change','purchase_route_change'),
       ('transitions_per_min','deaths_per_10min'),('space_concentration','death_fraction'),
       ('xp_team_share','death_fraction')]


def split_days(rows: list[dict]) -> dict:
    days=sorted({datetime.fromtimestamp(r['start_time'],timezone.utc).date().isoformat() for r in rows if number(r['start_time'])})
    cut=max(1,min(len(days)-1,int(len(days)*PARAMETERS['discovery_fraction']))) if len(days)>1 else len(days)
    return {'discovery_days':days[:cut],'validation_days':days[cut:],'rule':'earliest 70% of UTC days; never split a day',
            'version':digest([days,cut]),'limitation':'snapshot holdout; future repeated reuse requires a new prospectively frozen validation plan'}


def _points(entries: list[dict], x: str, y: str) -> list[dict]:
    points=[]
    for e in entries:
        a=e['metrics'].get(x);b=e['metrics'].get(y)
        row=e['row']
        if not a or not a['eligible'] or not number(a['value']):continue
        value=float(row['win']) if y=='win' and type(row['win']) is bool else b['value'] if b and b['eligible'] else None
        if not number(value) or not number(row['start_time']):continue
        day=datetime.fromtimestamp(row['start_time'],timezone.utc).date().isoformat()
        points.append({'x':a['value'],'y':value,'day':day,'match_id':row['match_id']})
    return points


def _evaluate(points: list[dict], *, outcome: bool, seed: int, enabled: bool, resamples: int = 999) -> dict:
    blocks=defaultdict(list)
    for p in points:blocks[p['day']].append(p)
    daily=[{'day':d,'x':statistics.mean(p['x'] for p in ps),'y':statistics.mean(p['y'] for p in ps)} for d,ps in sorted(blocks.items())]
    raw=association([p['x'] for p in points],[p['y'] for p in points])
    effect=association([p['x'] for p in daily],[p['y'] for p in daily])
    stability=[]
    if len(daily)>=4 and effect['pearson'] is not None:
        for i in range(len(daily)):
            kept=daily[:i]+daily[i+1:];r=correlation([p['x'] for p in kept],[p['y'] for p in kept])
            if r is not None:stability.append(r*effect['pearson']>0)
    wins=sum(p['y']==1 for p in points);losses=sum(p['y']==0 for p in points)
    reasons=[]
    if not enabled:reasons.append('comparison conditions missing or explicitly relaxed')
    if len(points)<5:reasons.append('fewer than five eligible matches')
    if len(daily)<PARAMETERS['minimum_days']:reasons.append('fewer than eight observed UTC-day blocks')
    if outcome and min(wins,losses)<5:reasons.append('fewer than five matches in an outcome arm')
    if effect['pearson'] is None:reasons.append('constant or insufficient daily values')
    p=None if reasons else permutation_p([v['x'] for v in daily],[v['y'] for v in daily],seed=seed,resamples=resamples)
    return {'match_effect':raw,'day_block_effect':effect,'p_value':p,'withheld_reasons':reasons,
            'planned_permutations':resamples,
            'leave_one_day_out_sign_agreement':sum(stability)/len(stability) if stability else None,
            'outcome_wins':wins if outcome else None,'outcome_losses':losses if outcome else None,
            'assumptions':'UTC days are exchangeable blocks under the null; serial dependence across days is not ruled out',
            'block_unit':'one equally weighted UTC-day mean; episodes never add match outcomes'}


def find_relations(rows: list[dict], cohorts: list[dict], members: dict) -> dict:
    split=split_days(rows);train=set(split['discovery_days']);validation=set(split['validation_days'])
    declared=[];too_small_groups=0
    for cohort in cohorts:
        if cohort['summary']['n']<3:too_small_groups+=1;continue
        metrics=set(cohort['summary']['metrics']);pairs=[(x,y) for x,y in PAIRS if x in metrics and y in metrics]
        pairs.extend((x,'win') for x in sorted(metrics))
        for x,y in pairs:declared.append((cohort,x,y))
    family_size=len(declared)
    resamples=min(PARAMETERS['max_permutations'],max(PARAMETERS['permutations'],math.ceil(family_size/PARAMETERS['alpha'])-1))
    candidates=[]
    for cohort,x,y in declared:
        key=digest([cohort['id'],x,y])[:20];points=_points(members[cohort['id']],x,y)
        discovery=[p for p in points if p['day'] in train];holdout=[p for p in points if p['day'] in validation]
        observed=_evaluate(discovery,outcome=y=='win',seed=int(key[:8],16),enabled=cohort['comparison_eligible'],resamples=resamples)
        r=observed['day_block_effect']['pearson'];coverage=len(discovery)/sum(number(e['row']['start_time']) and datetime.fromtimestamp(e['row']['start_time'],timezone.utc).date().isoformat() in train for e in members[cohort['id']]) if discovery else 0
        # Rank only discovery evidence. Holdout measurements never determine the ranking.
        repeatability=observed['leave_one_day_out_sign_agreement']
        priority=(abs(r) if r is not None else 0)*coverage*min(1,observed['day_block_effect']['n']/8)*(repeatability if repeatability is not None else 0)
        candidates.append({'id':key,'cohort_ref':cohort['id'],'scope':cohort['scope'],'x':x,'y':y,
                           'discovery':observed,'discovery_coverage':coverage,'priority':priority,
                           'priority_definition':'|daily correlation| × eligible match coverage × min(day blocks/8,1) × leave-one-day-out sign agreement',
                           'practical_check':f'Freeze {x} × {y} and these conditions; compare the same features in new matching games, inspect low/high agreement examples, record alternative explanations.',
                           'exploratory':True,'causal':False,'drill_ref':f'relation:{key}',
                           '_holdout':holdout,'_points':points,'_enabled':cohort['comparison_eligible']})
    candidates.sort(key=lambda c:(-c['priority'],c['id']))
    # Family size is declared before scoring, including tests withheld for missing data.
    family_size=len(declared)
    for i,c in enumerate(candidates):
        c['discovery']['adjusted_p']=bonferroni(c['discovery']['p_value'],family_size) if family_size else None
        c['validation']=_evaluate(c.pop('_holdout'),outcome=c['y']=='win',seed=int(c['id'][8:16],16),enabled=c.pop('_enabled'),resamples=resamples)
        c['validation']['adjusted_p']=bonferroni(c['validation']['p_value'],family_size) if family_size else None
        a=c['discovery']['day_block_effect']['pearson'];b=c['validation']['day_block_effect']['pearson']
        c['same_direction']=a*b>0 if a is not None and b is not None else None
        c['status']='observational_temporal_replication' if c['discovery']['adjusted_p'] is not None and c['validation']['adjusted_p'] is not None and max(c['discovery']['adjusted_p'],c['validation']['adjusted_p'])<=.05 and c['same_direction'] else 'needs_more_data_or_validation'
    details={c['id']:c.pop('_points') for c in candidates}
    return {'split':split,'family_size':family_size,'groups_below_three':too_small_groups,
            'planned_permutations':resamples,'smallest_possible_adjusted_p':min(1,family_size/(resamples+1)),
            'correction':'Bonferroni over the entire declared family, separately in discovery and validation',
            'candidate_count':len(candidates),'replicated_count':sum(c['status']=='observational_temporal_replication' for c in candidates),
            'candidates':candidates,'details':details,
            'limits':['observational associations, not causes','terminal statistics may encode outcome rather than predict it',
                      'linear/monotone summaries and predefined conditions, not exhaustive nonlinear discovery',
                      'UTC-day blocks reduce within-day pseudoreplication, not all serial dependence',
                      'multiple testing correction cannot fix biased samples or missing confounders']}
