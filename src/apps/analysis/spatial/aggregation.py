"""Additive spatial L3–L5 distributions with explicit denominators."""
import json

from ..evidence import digest
from .schemas import VERSION, LAYERS, SpatialError, signed, validate

LIVES=('outside_reported_death','reported_dead','unknown_life')


def empty_group(phase: int | None, state: str) -> dict:
    return {'phase':phase,'state':state,'seconds':{life:0 for life in LIVES},
            'observed_seconds':{life:0 for life in LIVES},'unknown_seconds':{life:0 for life in LIVES},
            'cells':{},'events':{k:{'count':0,'value':0,'mapped_count':0,'mapped_value':0,'unmapped_count':0,'unmapped_value':0,'rate_eligible_count':0,'rate_eligible_value':0,'eligible_exposure_seconds':0} for k in LAYERS},
            'transitions':{},'isolation':{'n':0,'missing':0,'sum':0,'sum_squares':0,'min':None,'max':None},
            'match_ids':[]}


def cell(group: dict, key: str) -> dict:
    return group['cells'].setdefault(key,{'seconds':{life:0 for life in LIVES},
        'events':{k:{'count':0,'value':0,'rate_count':0,'rate_value':0,'exposure_seconds':0} for k in LAYERS},'match_ids':[]})


def build_phases(observations: dict) -> dict:
    validate(observations)
    if observations['level']!=2:raise SpatialError('Spatial L3 requires L2')
    groups={};mid=observations['context']['match_id']
    def get(phase: int, state: str) -> dict:
        key=f'{phase}:{state}'
        if key not in groups:groups[key]=empty_group(phase,state);groups[key]['match_ids']=[mid]
        return groups[key]
    for s in observations['segments']:
        g=get(s['phase'],s['state']);seconds=s['end']-s['start'];life=s['life']
        g['seconds'][life]+=seconds
        if s['cell'] is None:g['unknown_seconds'][life]+=seconds
        else:
            g['observed_seconds'][life]+=seconds
            x=cell(g,s['cell']);x['seconds'][life]+=seconds;x['match_ids']=[mid]
            if life=='outside_reported_death':
                for kind in LAYERS:
                    if observations['journal_quality'][kind]['eligible']:
                        x['events'][kind]['exposure_seconds']+=seconds
                        g['events'][kind]['eligible_exposure_seconds']+=seconds
    for e in observations['events']:
        g=get(e['phase'],e['state']);kind=e['kind'];totals=g['events'][kind]
        totals['count']+=1;totals['value']+=e['value']
        if e['cell'] is None:totals['unmapped_count']+=1;totals['unmapped_value']+=e['value'];continue
        totals['mapped_count']+=1;totals['mapped_value']+=e['value']
        x=cell(g,e['cell']);x['events'][kind]['count']+=1;x['events'][kind]['value']+=e['value'];x['match_ids']=[mid]
        if e['rate_eligible']:
            totals['rate_eligible_count']+=1;totals['rate_eligible_value']+=e['value']
            x['events'][kind]['rate_count']+=1;x['events'][kind]['rate_value']+=e['value']
    for t in observations['transitions']:
        g=get(t['phase'],t['state']);key=t['from']+'>'+t['to'];g['transitions'][key]=g['transitions'].get(key,0)+1
    for sample in observations['isolation']:
        a=get(sample['phase'],sample['state'])['isolation'];d=sample['distance']
        if d is None:a['missing']+=1
        else:
            a['n']+=1;a['sum']+=d;a['sum_squares']+=d*d
            a['min']=d if a['min'] is None else min(a['min'],d);a['max']=d if a['max'] is None else max(a['max'],d)
    return signed({'schema_version':VERSION,'id':f'{mid}:spatial:L3','level':3,'parameters':observations['parameters'],
                   'context':observations['context'],'dependencies':{observations['id']:observations['revision']},
                   'groups':list(groups.values()),'journal_quality':observations['journal_quality']})


def merge_groups(groups: list[dict]) -> dict:
    result=empty_group(None,'combined')
    for g in groups:
        result['match_ids']=sorted(set(result['match_ids'])|set(g['match_ids']))
        for key in ('seconds','observed_seconds','unknown_seconds'):
            for life in LIVES:result[key][life]+=g[key][life]
        for kind in LAYERS:
            for key,value in g['events'][kind].items():result['events'][kind][key]+=value
        for key,x in g['cells'].items():
            target=cell(result,key);target['match_ids']=sorted(set(target['match_ids'])|set(x['match_ids']))
            for life in LIVES:target['seconds'][life]+=x['seconds'][life]
            for kind in LAYERS:
                for field,value in x['events'][kind].items():target['events'][kind][field]+=value
        for key,n in g['transitions'].items():result['transitions'][key]=result['transitions'].get(key,0)+n
        a,b=result['isolation'],g['isolation']
        for field in ('n','missing','sum','sum_squares'):a[field]+=b[field]
        if b['min'] is not None:a['min']=b['min'] if a['min'] is None else min(a['min'],b['min'])
        if b['max'] is not None:a['max']=b['max'] if a['max'] is None else max(a['max'],b['max'])
    return result


def summarize(group: dict, params: dict) -> dict:
    alive=group['seconds']['outside_reported_death'];observed=group['observed_seconds']['outside_reported_death']
    ranked=sorted(group['cells'].items(),key=lambda kv:kv[1]['seconds']['outside_reported_death'],reverse=True)
    rates=[]
    for key,x in ranked:
        exposure=x['events']['death']['exposure_seconds'];n=x['events']['death']['rate_count']
        rates.append({'cell':key,'exposure_seconds':exposure,'deaths':x['events']['death']['count'],'eligible_deaths':n,
                      'deaths_per_10_observed_minutes':n*600/exposure if exposure else None,
                      'small_denominator':exposure<params['minimum_exposure_seconds'],
                      'small_event_sample':n<params['minimum_deaths'],'matches':len(x['match_ids'])})
    isolation=group['isolation']
    return {'duration_seconds':sum(group['seconds'].values()),'observed_outside_death_seconds':observed,
            'outside_reported_death_seconds':alive,'coverage_fraction':observed/alive if alive else None,
            'reported_dead_seconds':group['seconds']['reported_dead'],'observed_reported_dead_seconds':group['observed_seconds']['reported_dead'],
            'unknown_life_seconds':group['seconds']['unknown_life'],'unknown_position_seconds':sum(group['unknown_seconds'].values()),
            'visited_cells':sum(x['seconds']['outside_reported_death']>0 for x in group['cells'].values()),
            'top_presence_cells':[{'cell':key,'seconds':x['seconds']['outside_reported_death'],
                                   'share':x['seconds']['outside_reported_death']/observed if observed else None} for key,x in ranked[:5]],
            'transition_count':sum(group['transitions'].values()),
            'mean_nearest_observed_ally_distance':isolation['sum']/isolation['n'] if isolation['n'] else None,
            'isolation_samples':isolation['n'],'isolation_missing':isolation['missing'],
            'death_rates':rates,'events':group['events'],'match_count':len(group['match_ids'])}


def build_match(phases: dict) -> dict:
    validate(phases)
    if phases['level']!=3:raise SpatialError('Spatial L4 requires L3')
    merged=merge_groups(phases['groups']);c=phases['context'];summary=summarize(merged,phases['parameters'])
    compact={k:v for k,v in summary.items() if k not in ('death_rates',)}
    return signed({'schema_version':VERSION,'id':f"{c['match_id']}:spatial:L4",'level':4,
                   'parameters':phases['parameters'],'context':c,'dependencies':{phases['id']:phases['revision']},
                   'distribution':merged,'summary':compact,'journal_quality':phases['journal_quality'],
                   'metrics':{'space.occupancy':{'value':compact,'unit':'seconds/fraction','kind':'proxy'},
                              'space.isolation':{'value':summary['mean_nearest_observed_ally_distance'],'unit':'source-coordinate units','kind':'proxy','coverage':{'n':summary['isolation_samples'],'missing':summary['isolation_missing']}},
                              'match.space_distribution':{'distribution_ref':'distribution','unit':'seconds','kind':'proxy'},
                              'space.semantic_regions':{'value':None,'status':'unavailable','reason':'terrain geometry/world transform not verified'},
                              'vision.effective':{'value':None,'status':'unavailable','reason':'visibility not reconstructed'}}})


def aggregate_selection(artifacts: list[tuple[dict,dict]], *, filters: dict | None = None) -> dict:
    """Consume L4 and addressable L3 strata; duplicates/unknown versions never silently merge."""
    filters=filters or {}
    if not set(filters)<=set(('hero_id','position','side','phase','state','mode')):raise SpatialError('Unknown spatial filter')
    seen=set();selected=[];dependencies={};compatibilities=set();params=None
    for match,phases in artifacts:
        validate(match);validate(phases)
        if match['level']!=4 or phases['level']!=3 or match['dependencies']!={phases['id']:phases['revision']}:
            raise SpatialError('L5 requires matched L4/L3 revisions')
        c=match['context'];mid=c['match_id']
        if mid in seen:raise SpatialError('Duplicate match would double-count exposure')
        seen.add(mid)
        side='radiant' if next(p['isRadiant'] for p in c['roster'] if p['playerSlot']==c['target_slot']) else 'dire'
        ctx={k:c[k] for k in ('hero_id','position','mode')};ctx['side']=side
        if any(ctx[k]!=v for k,v in filters.items() if k in ctx):continue
        version=c['patch_ids'].get('stratz')
        compatibility=digest({'source':'stratz','game_version':version if version is not None else f'unknown:{mid}',
                              'parameters':match['parameters'],'account':c['account_id']})
        relevant=[g for g in phases['groups'] if all(g[k]==v for k,v in filters.items() if k in ('phase','state'))]
        if not relevant:continue
        compatibilities.add(compatibility);params=match['parameters'];dependencies[match['id']]=match['revision']
        for g in relevant:selected.append((ctx,g))
    if len(compatibilities)>1:raise SpatialError('Incompatible coordinate/map/parameter/account versions')
    # Unspecified conditions stay split, rather than pooling heroes/roles/sides/state by default.
    groups={}
    for ctx,g in selected:
        scope={**ctx,'phase':g['phase'],'state':g['state']};key=digest(scope)[:16]
        if key not in groups:groups[key]={'context':scope,'children':[]}
        groups[key]['children'].append(g)
    outputs=[]
    for key,entry in groups.items():
        merged=merge_groups(entry['children'])
        outputs.append({'id':key,'context':entry['context'],'distribution':merged,'summary':summarize(merged,params)})
    return signed({'schema_version':VERSION,'id':'spatial:L5:'+digest([filters,dependencies])[:16],'level':5,
                   'parameters':params,'filters':filters,'groups':outputs,'dependencies':dependencies,
                   'match_count':len(dependencies),'aggregation':'pooled numerators / pooled observed time; conditions remain separate',
                   'causal_or_population_claims':False})


def compact_selection(aggregate: dict, *, budget_bytes: int = 32000) -> dict:
    """A bounded analyst view; full grids, per-match IDs and routes are drill-down only."""
    validate(aggregate)
    if aggregate.get('level')!=5 or not 1024<=budget_bytes<=100000:
        raise SpatialError('A spatial L5 and a 1024..100000 byte budget are required')
    packet={'schema_version':VERSION,'level':5,'id':aggregate['id']+':compact',
            'distribution_ref':{'id':aggregate['id'],'revision':aggregate['revision']},
            'match_count':aggregate['match_count'],'filters':aggregate['filters'],
            'groups':[],'total_groups':len(aggregate['groups']),'omitted_groups':len(aggregate['groups']),
            'order':'observed time descending; omitted contexts remain available by filter',
            'limits':'Source grid only; estimated death intervals; intensity is not effectiveness or causation.'}
    for group in sorted(aggregate['groups'],key=lambda g:g['summary']['observed_outside_death_seconds'],reverse=True):
        summary={k:v for k,v in group['summary'].items() if k not in ('death_rates',)}
        entry={'distribution_group_ref':group['id'],'context':group['context'],'summary':summary}
        packet['groups'].append(entry);packet['omitted_groups']-=1
        if len(json.dumps(signed(packet),ensure_ascii=False,separators=(',',':')).encode('utf-8'))>budget_bytes:
            packet['groups'].pop();packet['omitted_groups']+=1;break
    return signed(packet)
