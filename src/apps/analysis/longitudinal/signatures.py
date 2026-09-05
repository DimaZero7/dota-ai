"""Create small L4 extensions once; L5 subsequently consumes only these rows."""
from collections import defaultdict

from ..numeric.schemas import validate_node, measures, number, divide
from ..spatial.schemas import validate as validate_spatial
from .schemas import VERSION, PARAMETERS, LongitudinalError, measure, signed


def _ratio(num: float | None, den: float | None, unit: str, *, scale: float = 1, eligible: bool = True) -> dict:
    value=divide(num,den)
    return measure(value*scale if value is not None else None,unit=unit,numerator=num,denominator=den,
                   scale=scale,eligible=eligible,reason=None if eligible else 'source journal ineligible')


def _contrasts(windows: list[dict], quality: dict) -> tuple[dict,list]:
    """Next-minute changes against same-match, same-phase/pre-state control minutes."""
    outputs={};detail=[]
    for name,condition,target in [('post_combat_xp_change','damage','xp'),
                                   ('purchase_damage_change','purchase','damage')]:
        required=(condition,target,'death');eligible=all(quality[k]['eligible'] for k in required)
        strata=defaultdict(lambda:{True:[],False:[]})
        if eligible:
            for current,nxt in zip(windows,windows[1:]):
                if current['end']!=nxt['start'] or current['exposure_seconds']!=60 or nxt['exposure_seconds']!=60:continue
                state=current['state_start']['team_band']
                if state is None:continue
                # For combat, the validated target partition is used; no damage is an observation, not inactivity.
                a=current['xp'] if target=='xp' else (current['damage_attribution'] or {}).get('original_enemy_targets')
                b=nxt['xp'] if target=='xp' else (nxt['damage_attribution'] or {}).get('original_enemy_targets')
                trigger=(current['damage_attribution'] or {}).get('original_enemy_targets') if condition=='damage' else current['counts']['purchase']
                if not all(number(v) for v in (a,b,trigger)):continue
                width=PARAMETERS['contrast_xp_band' if target=='xp' else 'contrast_damage_band']
                key=(current['start']//600*600,state,bool(current['counts']['death']),int(a//width)*width)
                strata[key][trigger>0].append({'delta':b-a,'window':current['id'],'next_window':nxt['id']})
        weighted=cases=controls=matched_strata=0
        for (phase,state,death,baseline_band),arms in strata.items():
            if not arms[True] or not arms[False]:continue
            baseline=sum(x['delta'] for x in arms[False])/len(arms[False])
            for case in arms[True]:weighted+=case['delta']-baseline
            cases+=len(arms[True]);controls+=len(arms[False]);matched_strata+=1
            detail.append({'feature':name,'phase':phase,'state_before':state,'death_in_window':death,
                           'baseline_target_band':baseline_band,
                           'cases':arms[True],'controls':arms[False],
                           'difference':sum(x['delta'] for x in arms[True])/len(arms[True])-baseline})
        outputs[name]=_ratio(weighted,cases,'XP/min change' if target=='xp' else 'damage/min change',eligible=eligible)
        outputs[name].update(case_windows=cases,control_windows=controls,matched_strata=matched_strata,
                             definition=f'next minus current minute {target}; {condition}>0 vs ==0, same phase/pre-state/death-presence/baseline-target band',
                             limitation='overlapping pairs; reused controls; coarse baseline matching does not eliminate regression to mean or unmeasured confounding; not action effects')
    return outputs,detail


def build_signature(numeric: dict, episodes: dict, spatial: dict, routes: dict | None = None) -> tuple[dict,dict]:
    validate_node(numeric);validate_node(episodes);validate_spatial(spatial)
    if numeric['level']!=4 or episodes['level']!=2 or spatial['level']!=4 or not numeric['context']==episodes['context']==spatial['context']:
        raise LongitudinalError('Matched numeric L4/L2 and spatial L4 required')
    if numeric['source_manifest_ref']!=episodes['source_manifest_ref']:
        raise LongitudinalError('Numeric source revisions differ')
    c=numeric['context'];m=measures(numeric);q=numeric['summary']['quality'];duration=c['duration']
    target=next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
    rank=c['rank'].get('stratz')
    context={'hero_id':c['hero_id'],'position':c['position'],'mode':c['mode'],
             'side':'radiant' if target['isRadiant'] else 'dire','stratz_version':c['patch_ids'].get('stratz'),
             'opendota_version':c['patch_ids'].get('opendota'),'rank_band':int(rank//10) if number(rank) else None,
             'duration_band':int(duration//600)*600,'lane':c['lane'],'rank':c['rank'],
             'draft_allies':sorted(p['heroId'] for p in c['roster'] if p['isRadiant']==target['isRadiant']),
             'draft_enemies':sorted(p['heroId'] for p in c['roster'] if p['isRadiant']!=target['isRadiant'])}
    values={}
    for name,value,journal,unit in [('xp_rate',numeric['summary']['recorded_xp'],'xp','XP/min'),
                                    ('gold_rate',numeric['summary']['recorded_gold'],'gold','gold/min'),
                                    ('farm_rate',m['farm.last_hits']['value'],'farm','last hits/min')]:
        values[name]=_ratio(value,duration,unit,scale=60,eligible=q[journal]['eligible'])
    values['death_fraction']=_ratio(numeric['summary']['death_seconds_proxy'],duration,'fraction',eligible=q['death']['eligible'])
    values['deaths_per_10min']=_ratio(m['death.count']['value'],duration,'deaths/10min',scale=600,eligible=q['death']['eligible'])
    participation=m['combat.participation']
    values['participation']=_ratio(participation['numerator'],participation['denominator'],'fraction',eligible=participation['coverage']['eligible'])
    trajectory=m['match.trajectory']['value']
    values['tower_damage_rate']=_ratio(sum(p['tower_damage'] or 0 for p in trajectory),duration,'tower damage/min',scale=60,eligible=q['tower_damage']['eligible'])
    returns=m['episodes.return_activity']['value']
    values['return_delay']=_ratio(returns['sum'] if returns else None,returns['n'] if returns else None,'seconds',eligible=m['episodes.return_activity']['coverage']['eligible'])
    ss=spatial['summary'];exposure=ss['observed_outside_death_seconds']
    coverage=divide(exposure,ss['outside_reported_death_seconds'])
    spatial_eligible=coverage is not None and coverage>=PARAMETERS['minimum_spatial_coverage'] and exposure>=PARAMETERS['minimum_spatial_seconds']
    top=ss['top_presence_cells'];values['space_concentration']=_ratio(top[0]['seconds'] if top else None,exposure,'fraction',eligible=spatial_eligible)
    values['spatial_coverage']=_ratio(exposure,ss['outside_reported_death_seconds'],'fraction')
    values['transitions_per_min']=_ratio(ss['transition_count'],exposure,'transitions/min',scale=60,eligible=spatial_eligible)
    isolation=spatial['distribution']['isolation'];values['ally_distance']=_ratio(isolation['sum'],isolation['n'],'source units',eligible=spatial_eligible)
    contrast,contrast_detail=_contrasts(episodes['windows'],q);values.update(contrast)
    deaths=measures(episodes)['episodes.return_activity']['value'] or []
    repeated=[]
    for previous,current in zip(deaths,deaths[1:]):
        gap=current['time']-previous['reported_end']
        if 0<=gap<=PARAMETERS['repeat_death_seconds']:
            repeated.append(current['id'])
    values['repeat_death_fraction']=_ratio(len(repeated),len(deaths),'fraction',eligible=q['death']['eligible'])
    route_values=[]
    if routes:
        validate_spatial(routes)
        if set(routes.get('dependencies',{}))!={f"{c['match_id']}:spatial:L2"}:raise LongitudinalError('Route match mismatch')
        for row in routes['routes']:
            comparison=row['comparison'];a=comparison['before_distribution'];b=comparison['after_distribution']
            if row['anchor']['kind']=='purchase' and a['window_seconds']==b['window_seconds']==60 and a['observed_seconds']>=48 and b['observed_seconds']>=48:
                value=comparison['cell_distribution_total_variation']
                if number(value):route_values.append(value)
    values['purchase_route_change']=_ratio(sum(route_values),len(route_values),'total variation')
    phase_rows=[]
    for p in trajectory:
        seconds=p['exposure_seconds'];pm={}
        for name,key,journal,unit,scale in [('xp_rate','xp','xp','XP/min',60),('gold_rate','gold','gold','gold/min',60),
                  ('death_fraction','death_seconds_proxy','death','fraction',1),('deaths_per_10min','deaths','death','deaths/10min',600),
                  ('farm_rate','last_hits','farm','last hits/min',60),('tower_damage_rate','tower_damage','tower_damage','tower damage/min',60)]:
            pm[name]=_ratio(p[key],seconds,unit,scale=scale,eligible=q[journal]['eligible'])
        pm['xp_team_share']=_ratio(p['xp'],p['recorded_xp_team_denominator'],'fraction',eligible=q['xp']['eligible'])
        phase_rows.append({'phase':p['start'],'complete_phase':seconds==600,'state':p['state_start']['team_band'],
                           'state_basis':'phase_start','metrics':pm,'seconds':seconds})
    state_rows=[]
    for p in trajectory:
        ds=[d for d in deaths if p['start']<=d['time']<(p['end']+1 if p['end']==duration else p['end'])]
        for state in ('ahead','behind','near_even','unknown'):
            selected=[d for d in ds if (d['state_before']['team_band'] or 'unknown')==state]
            state_rows.append({'phase':p['start'],'complete_phase':p['exposure_seconds']==600,'state':state,
                               'state_basis':'snapshot_before_death','metrics':{
                'death_state_share':_ratio(len(selected),len(ds),'fraction',eligible=q['death']['eligible']),
                'repeat_death_fraction':_ratio(sum(d['id'] in repeated for d in selected),len(selected),'fraction',eligible=q['death']['eligible'])}})
    dependencies={x['id']:x['revision'] for x in (numeric,episodes,spatial)}
    if routes:dependencies['spatial_routes']=routes['revision']
    signature=signed({'schema_version':VERSION,'level':4,'id':f"{c['match_id']}:longitudinal:L4",'match_id':c['match_id'],
                      'account_id':c['account_id'],'start_time':c['start_time'],'duration':duration,'win':c['win'],
                      'context':context,'metrics':values,'phases':phase_rows,'death_states':state_rows,
                      'dependencies':dependencies,'parameter_version':PARAMETERS,'source_manifest_ref':numeric['source_manifest_ref'],
                      'limitations':['rank is a source estimate','drafts retained, not mechanically encoded','source journals may be incomplete',
                                     'return estimates and overlapping controls are not independent','purchase is not delivery or usage']})
    detail={'match_id':c['match_id'],'signature_revision':signature['revision'],'contrasts':contrast_detail,
            'repeated_death_ids':repeated,'death_events':[{k:d[k] for k in ('id','time','reported_end','state_before')} for d in deaths],
            'numeric_drill_ref':numeric['drill_index_ref'],'spatial_drill_ref':spatial['id']}
    return signature,detail
