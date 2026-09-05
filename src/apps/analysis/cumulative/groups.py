"""Exact group replacement, reusable L5 distributions and paired sufficient statistics."""
from collections import defaultdict

from ..evidence import digest
from ..longitudinal.cohorts import build_cohorts, _summary
from ..longitudinal.statistics import association, distribution
from ..numeric.schemas import number
from ..spatial.aggregation import merge_groups, summarize
from ..longitudinal.relations import PAIRS


def contributions(value: dict, contract_id: str) -> list[tuple[str,str,dict,dict]]:
    row=value['signature'];cohorts,members=build_cohorts([row]);result=[]
    slim={k:row[k] for k in ('match_id','start_time','duration','win','context')}
    for c in cohorts:
        meta={k:v for k,v in c.items() if k!='summary'}
        result.append((c['id'],'numeric',meta,{'row':slim,'metrics':members[c['id']][0]['metrics']}))
    spatial=value['spatial']
    if spatial:
        for g in spatial['groups']:
            scope={k:row['context'].get(k) for k in ('hero_id','position','side','mode','stratz_version','opendota_version')}
            scope.update(phase=g['phase'],state=g['state'],spatial_parameters=spatial['parameters'],contract=contract_id)
            if scope['stratz_version'] is None:scope['unknown_version_match']=row['match_id']
            key='space:'+digest(scope)[:24]
            result.append((key,'spatial',{'scope':scope,'parameters':spatial['parameters']},g))
    return result


def paired(entries: list[dict]) -> dict:
    keys=set().union(*(e['metrics'] for e in entries));pairs=[p for p in PAIRS if set(p)<=keys]
    pairs += [(k,'win') for k in sorted(keys)]
    result={}
    for x,y in pairs:
        points=[]
        for e in entries:
            a=e['metrics'].get(x);b=e['metrics'].get(y)
            v=float(e['row']['win']) if y=='win' and type(e['row']['win']) is bool else b['value'] if b and b['eligible'] else None
            if a and a['eligible'] and number(a['value']) and number(v):points.append((a['value'],v))
        xs=[x for x,y in points];ys=[y for x,y in points]
        result[x+'×'+y]={**association(xs,ys),'sum_x':sum(xs),'sum_y':sum(ys),'sum_x2':sum(x*x for x in xs),
                         'sum_y2':sum(y*y for y in ys),'sum_xy':sum(x*y for x,y in points),
                         'missing_pairs':len(entries)-len(points),'inference':'descriptive paired match values; not a fresh significance test'}
    return result


def aggregate(kind: str, meta: dict, entries: list[dict]) -> dict:
    if kind=='spatial':
        merged=merge_groups(entries)
        return {**meta,'distribution':merged,'summary':summarize(merged,meta['parameters'])}
    return {**meta,'summary':_summary(entries),'joint':paired(entries)}


def recent_view(meta: dict, entries: list[dict], recent_ids: set[int]) -> dict | None:
    if meta['scope']['kind']!='match' or not meta['comparison_eligible']:return None
    old=[e for e in entries if e['row']['match_id'] not in recent_ids];new=[e for e in entries if e['row']['match_id'] in recent_ids]
    if not old or not new:return None
    keys=sorted(set().union(*(e['metrics'] for e in entries)));metrics={}
    for k in keys:
        a=distribution([e['metrics'].get(k) for e in old]);b=distribution([e['metrics'].get(k) for e in new])
        metrics[k]={'history':a,'recent':b,'mean_change':b['mean']-a['mean'] if a['mean'] is not None and b['mean'] is not None else None,
                    'coverage_change':b['coverage']-a['coverage']}
    return {'cohort_ref':meta['id'],'scope':meta['scope'],'history_n':len(old),'recent_n':len(new),'metrics':metrics}
