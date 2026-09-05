"""Bounded numerical analyst input and explicitly budgeted evidence retrieval."""
import json
from datetime import datetime, timezone

from .schemas import LongitudinalError, validate
from ..numeric.schemas import number

MAIN_METRICS=('xp_rate','gold_rate','death_fraction','participation','repeat_death_fraction',
              'tower_damage_rate','post_combat_xp_change','purchase_damage_change','purchase_route_change',
              'transitions_per_min','space_concentration','xp_team_share','death_state_share')


def size(data: dict) -> int:
    return len(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())


def short_distribution(data: dict) -> dict:
    return {k:data[k] for k in ('n','missing','coverage','median','q25','q75','mean','min','max','pooled_value','pooled_numerator','pooled_denominator','pooled_n','denominator_range','unit')}


def cohort_view(cohort: dict, metric: str | None = None) -> dict:
    s=cohort['summary'];metrics={}
    for k,d in s['metrics'].items():
        if (metric is None and k not in MAIN_METRICS) or (metric is not None and k!=metric):continue
        c=s['outcome_comparisons'][k]
        metrics[k]={'distribution':short_distribution(d),'wins_n':c['wins']['n'],'losses_n':c['losses']['n'],
                    'wins_mean':c['wins']['mean'],'losses_mean':c['losses']['mean'],
                    'mean_win_minus_loss':c['mean_win_minus_loss'],'enough_each_outcome':c['minimum_outcome_sample_met']}
    return {'id':cohort['id'],'scope':cohort['scope'],'n':s['n'],'wins':s['wins'],'losses':s['losses'],
            'comparison_eligible':cohort['comparison_eligible'],'relaxed_conditions':cohort['relaxed_conditions'],
            'uncontrolled_conditions':cohort['uncontrolled_conditions'],'unknown_conditions':cohort['unknown_conditions'],
            'metrics':metrics,'drill_ref':cohort['drill_ref']}


def compact_packet(data: dict, *, budget: int = 32000) -> dict:
    validate(data,5)
    if not 4000<=budget<=32000:raise LongitudinalError('Main packet budget must be 4000..32000 bytes')
    session=data['sessions'];summary=session['summary'];relations=data['relations']
    packet={'version':'longitudinal-packet-1','l5_revision':data['revision'],'n':data['n'],'wins':data['wins'],'losses':data['losses'],
            'chronology_n':session['n'],
            'dataset_coverage':data['dataset_coverage'],'composition':data['composition'],
            'sessions':{k:summary[k] for k in ('estimated_sessions','session_sizes','max_observed_win_run','max_observed_loss_run','history_complete')},
            'session_sensitivity':[{'gap_minutes':s['gap_minutes'],'estimated_sessions':s['estimated_sessions'],'session_sizes':s['session_sizes']} for s in session['sensitivity']],
            'after_result':{k:{a:v[a] for a in ('n','wins','win_fraction','within_session_n','hero_changes','role_changes','role_change_unknown')} for k,v in summary['after_result'].items()},
            'recent':{k:v for k,v in data['recent'].items() if k!='matched_groups'},
            'screening':{k:relations[k] for k in ('split','family_size','candidate_count','replicated_count','planned_permutations','smallest_possible_adjusted_p','correction','limits')},
            'cohorts':[],'candidates':[],'limitations':data['limitations'],
            'omitted':{'cohorts':len(data['cohorts']),'candidates':len(relations['candidates']),
                       'features':'Non-primary metrics and complete distributions remain in L5/drill.',
                       'examples':'No per-game records in the main packet.',
                       'reason':'Explicit byte budget; descriptive large hero/position groups then strict cohorts and discovery-ranked candidates.'},
            'drill':{'max_calls':3,'total_bytes':8000,'refs':['cohort:<id>','relation:<id>','sessions','recent','index']}}
    packet['screening']['positive_priority_candidates']=sum(c['priority']>0 for c in relations['candidates'])
    packet['screening']['discovery_tests_performed']=sum(c['discovery']['p_value'] is not None for c in relations['candidates'])
    packet['screening']['display_rule']='Only positive discovery priorities are shown; zero priorities remain in full L5.'
    # Reserve at most 25% for candidates; keep matched groups visible even when screening has little power.
    for candidate in [c for c in relations['candidates'] if c['priority']>0][:5]:
        packet['candidates'].append(candidate)
        if size(packet)>min(budget-1500,8000):packet['candidates'].pop();break
    ordered=sorted(data['cohorts'],key=lambda c:(c['scope']['kind']!='match',c['scope']['grouping']=='strict',-c['summary']['n'],c['id']))
    for c in ordered:
        view=cohort_view(c);packet['cohorts'].append(view)
        if size(packet)>budget-128:packet['cohorts'].pop();continue
    packet['omitted']['cohorts']-=len(packet['cohorts']);packet['omitted']['candidates']-=len(packet['candidates'])
    if size(packet)>budget:raise LongitudinalError('Mandatory packet context exceeds budget')
    return packet


class DrillSession:
    """One analyst review: at most three calls sharing an 8000-byte allowance."""

    def __init__(self, data: dict, detail: dict) -> None:
        validate(data,5);validate(detail)
        if detail['l5_revision']!=data['revision']:raise LongitudinalError('Stale drill details')
        self.data=data;self.detail=detail;self.calls=0;self.bytes=0

    def query(self, ref: str, *, metric: str = 'death_fraction', offset: int = 0) -> dict:
        if self.calls>=3 or self.bytes>=8000:raise LongitudinalError('Review drill allowance exhausted')
        if type(offset) is not int or offset<0:raise LongitudinalError('Nonnegative offset required')
        rows=[];context={}
        if ref.startswith('cohort:'):
            key=ref.split(':',1)[1];cohort=next((c for c in self.data['cohorts'] if c['id']==key),None)
            if cohort is None or metric not in cohort['summary']['metrics']:raise LongitudinalError('Unknown cohort/metric')
            context=cohort_view(cohort,metric)
            entries=[e for e in self.detail['cohorts'][key] if e['metrics'].get(metric) and e['metrics'][metric]['eligible']]
            entries.sort(key=lambda e:(e['metrics'][metric]['value'],e['match_id']))
            # Interleave low and high cases; neither tail is presented as proof of cause.
            while entries:
                e=entries.pop(0);rows.append({**self._identity(e['match_id']),'measure':e['metrics'][metric],'selection':'lower tail'})
                if entries:
                    e=entries.pop();rows.append({**self._identity(e['match_id']),'measure':e['metrics'][metric],'selection':'upper tail'})
        elif ref.startswith('relation:'):
            key=ref.split(':',1)[1];candidate=next((c for c in self.data['relations']['candidates'] if c['id']==key),None)
            if candidate is None:raise LongitudinalError('Unknown relation')
            context=candidate;points=self.detail['relations'][key]
            train=set(self.data['relations']['split']['discovery_days']);discovery=[p for p in points if p['day'] in train]
            mx=sum(p['x'] for p in discovery)/len(discovery) if discovery else 0
            my=sum(p['y'] for p in discovery)/len(discovery) if discovery else 0
            direction=candidate['discovery']['day_block_effect']['pearson'] or 0
            # Agreement with discovery direction, centered on discovery means only.
            ranked=sorted(points,key=lambda p:((p['x']-mx)*(p['y']-my)*direction,p['match_id']))
            while ranked:
                p=ranked.pop(0);rows.append({**self._identity(p['match_id']),**p,'selection':'least directional agreement' if direction else 'unranked; discovery direction unavailable'})
                if ranked:
                    p=ranked.pop();rows.append({**self._identity(p['match_id']),**p,'selection':'greatest directional agreement' if direction else 'unranked; discovery direction unavailable'})
        elif ref=='sessions':
            context={'rule':self.data['sessions']['gap_minutes'],'limits':self.data['sessions']['summary']['limitations']}
            rows=[{'kind':'after_result','value':self.data['sessions']['summary']['after_result']},
                  *({'kind':'observed_order','order':k,**v} for k,v in self.data['sessions']['summary']['by_observed_order'].items())]
        elif ref=='recent':
            rows=[{**{k:v for k,v in g.items() if k!='metrics'},'metrics':{metric:g['metrics'][metric]}}
                  for g in self.data['recent'].get('matched_groups',[]) if metric in g['metrics']]
        elif ref=='index':
            rows=[{'id':c['id'],'scope':c['scope'],'n':c['summary']['n'],'metrics':list(c['summary']['metrics']),'drill_ref':c['drill_ref']} for c in self.data['cohorts']]
        else:raise LongitudinalError('Unknown drill reference')
        available=8000-self.bytes
        output={'l5_revision':self.data['revision'],'ref':ref,'context':context,'rows':[],
                'total_rows':len(rows),'offset':offset,'omitted_rows':len(rows),'next_offset':offset}
        if size(output)>available:raise LongitudinalError('Context exceeds remaining drill budget')
        for row in rows[offset:]:
            output['rows'].append(row)
            if size(output)>available-80:output['rows'].pop();break
        if rows[offset:] and not output['rows']:raise LongitudinalError('One row exceeds remaining budget; request a narrower metric')
        output['omitted_rows']=len(rows)-len(output['rows']);output['next_offset']=offset+len(output['rows']) if offset+len(output['rows'])<len(rows) else None
        self.calls+=1;self.bytes+=size(output)
        return output

    def _identity(self, match_id: int) -> dict:
        r=self.detail['matches'][str(match_id)]
        return {'match_id':match_id,'date_utc':datetime.fromtimestamp(r['start_time'],timezone.utc).isoformat() if number(r['start_time']) else None,
                'hero_id':r['context']['hero_id'],'position':r['context']['position'],'win':r['win'],
                'signature_ref':r['id'],'signature_revision':r['revision']}
