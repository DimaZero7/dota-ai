"""L2 windows and descriptive episodes; no compulsory model interpretation."""
from bisect import bisect_left, bisect_right
from collections import Counter

from .schemas import PARAMETERS, divide, measurement, node, number, quality, point_quality, validate_node


def events_in(journal: dict, start: float, end: float) -> list:
    rows = journal['events']
    return rows[bisect_left(rows, start, key=lambda e:e['time']):bisect_left(rows, end, key=lambda e:e['time'])]


def available(journal: dict) -> bool:
    return journal['quality']['status'] != 'unavailable'


def snapshot(journal: dict, time: float, fields: tuple[str, ...]) -> dict | None:
    if not journal['quality']['eligible']:
        return None
    rows = journal['events']
    i = bisect_right(rows, time, key=lambda e:e['time']) - 1
    if i < 0 or time - rows[i]['time'] > PARAMETERS['snapshot_age_seconds']:
        return None
    row = rows[i]
    if any(not number(row.get(k)) for k in fields):
        return None
    return {'time': row['time'], 'age_seconds': time-row['time'], **{k:row[k] for k in fields},
            'source_index': row['_source_index']}


def economic_state(facts: dict, time: float) -> dict:
    context = facts['context']
    slot = str(context['target_slot'])
    target = next(p for p in context['roster'] if str(p['playerSlot']) == slot)
    values = {s: snapshot(p['economy'], time, ('networth',)) for s,p in facts['players'].items()}
    own = values[slot]
    allies = [str(p['playerSlot']) for p in context['roster'] if p['isRadiant'] == target['isRadiant']]
    enemies = [str(p['playerSlot']) for p in context['roster'] if p['isRadiant'] != target['isRadiant']]
    candidates = [p for p in context['roster'] if p['isRadiant'] != target['isRadiant'] and
                  target.get('position') is not None and p.get('position') == target['position']]
    opponent_slot = str(candidates[0]['playerSlot']) if len(candidates) == 1 else None
    opponent = values.get(opponent_slot)
    allied_sum = sum(values[s]['networth'] for s in allies) if all(values[s] is not None for s in allies) else None
    enemy_sum = sum(values[s]['networth'] for s in enemies) if all(values[s] is not None for s in enemies) else None
    diff = allied_sum - enemy_sum if allied_sum is not None and enemy_sum is not None else None
    band = None if diff is None else 'ahead' if diff > 1000 else 'behind' if diff < -1000 else 'near_even'
    return {'time': time, 'networth': own['networth'] if own else None,
            'counterpart_slot': int(opponent_slot) if opponent_slot else None,
            'counterpart_delta': own['networth']-opponent['networth'] if own and opponent else None,
            'team_delta': diff, 'team_band': band, 'ally_networth': allied_sum,
            'resource_share': divide(own['networth'] if own else None, allied_sum),
            'fresh_players': sum(v is not None for v in values.values())}


def union_seconds(intervals: list[tuple[float,float]], start: float, end: float) -> float:
    total, last = 0, start
    for a,b in sorted(intervals):
        a,b = max(start,a), min(end,b)
        if b > a:
            total += max(0,b-max(a,last))
            last = max(last,b)
    return total


def gaps(times: list[float], start: float, end: float) -> dict:
    times = sorted(set(t for t in times if start <= t <= end))
    internal = [b-a for a,b in zip(times,times[1:])]
    return {'internal_gaps_seconds': internal, 'max_internal_gap_seconds': max(internal,default=None),
            'left_boundary_seconds': times[0]-start if times else None,
            'right_boundary_seconds': end-times[-1] if times else None,
            'boundary_censored': True, 'meaning': 'gap between recorded events; not inactivity'}


def _sum_groups(rows: list, amount: str, keys: tuple[str,...]) -> dict:
    result = Counter()
    for e in rows:
        if number(e.get(amount)):
            result['|'.join(str(e.get(k, 'unknown')) for k in keys)] += e[amount]
    return dict(sorted(result.items()))


def _counts(rows: list, field: str) -> dict:
    return dict(sorted(Counter(str(e.get(field, 'unknown')) for e in rows).items()))


def _sum_if(j: dict, rows: list, field: str) -> float | None:
    return sum(e[field] for e in rows) if available(j) else None


def damage_partition(facts: dict, rows: list) -> dict:
    c=facts['context'];own=next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
    enemies={p['heroId'] for p in c['roster'] if p['isRadiant']!=own['isRadiant']}
    result={'original_enemy_targets':0,'illusion_enemy_targets':0,'unknown_attribution':0,'own_illusion_to_original_enemy':0}
    for e in rows:
        if e.get('attacker')!=c['hero_id'] or e.get('target') not in enemies:
            result['unknown_attribution']+=e['value']
        elif e.get('toIllusion') is False:
            result['original_enemy_targets']+=e['value']
            if e.get('fromIllusion') is True:result['own_illusion_to_original_enemy']+=e['value']
        elif e.get('toIllusion') is True:result['illusion_enemy_targets']+=e['value']
        else:result['unknown_attribution']+=e['value']
    return result


def numeric_windows(facts: dict) -> list[dict]:
    context, js = facts['context'], facts['journals']
    duration = context['duration']
    death_intervals = [(e['time'],e['time']+e['timeDead']) for e in js['death']['events'] if e['timeDead'] >= 0]
    windows = []
    for start in range(0, duration, 60):
        end = min(start+60,duration)
        event_end = end+1 if end == duration else end
        rows = {k:events_in(j,start,event_end) for k,j in js.items()}
        activity_times = [e['time'] for k in ('farm','damage','tower_damage') for e in rows[k] if e['time'] < end]
        occupied = {int((t-start)//10) for t in activity_times}
        activity_seconds = sum(min(10,end-start-bin*10) for bin in occupied)
        activity_available = all(available(js[k]) for k in ('farm','damage','tower_damage'))
        row = {'id': f"w{start}", 'start': start, 'end': end, 'exposure_seconds': end-start,
               'counts': {k:len(v) if available(js[k]) else None for k,v in rows.items()},
               'xp': _sum_if(js['xp'],rows['xp'],'amount'), 'xp_by_reason': _sum_groups(rows['xp'],'amount',('reason',)) if available(js['xp']) else None,
               'gold': _sum_if(js['gold'],rows['gold'],'amount'), 'gold_by_reason_validity': _sum_groups(rows['gold'],'amount',('reason','isValidForStats')) if available(js['gold']) else None,
               'farm_flags': {k:sum(e.get(k) is True for e in rows['farm']) for k in ('isCreep','isNeutral','isAncient')} if available(js['farm']) else None,
               'damage': _sum_if(js['damage'],rows['damage'],'value'),
               'damage_attribution': damage_partition(facts,rows['damage']) if available(js['damage']) else None,
               'healing': _sum_if(js['heal'],rows['heal'],'value'),
               'healing_self': sum(e['value'] for e in rows['heal'] if e.get('target') == context['hero_id']) if available(js['heal']) else None,
               'healing_other_known': sum(e['value'] for e in rows['heal'] if e.get('target') in {p['heroId'] for p in context['roster']} and e.get('target') != context['hero_id']) if available(js['heal']) else None,
               'tower_damage': _sum_if(js['tower_damage'],rows['tower_damage'],'damage'),
               'death_seconds_proxy': union_seconds(death_intervals,start,end) if available(js['death']) else None,
               'activity_bin_seconds_proxy': activity_seconds if activity_available else None,
               'state_start': economic_state(facts,start), 'state_end': economic_state(facts,end),
               'xp_by_player': {slot: None for slot in facts['players']},
               'provenance': {'node': facts['id'], 'window': [start,event_end], 'clock': 'STRATZ'}}
        # XP journals for all players are optional in older snapshots, never inferred from net worth.
        for slot,player in facts['players'].items():
            if 'xp' in player and player['xp']['quality']['eligible']:
                row['xp_by_player'][slot] = sum(e['amount'] for e in events_in(player['xp'],start,event_end))
        windows.append(row)
    return windows


def death_episodes(facts: dict) -> list[dict]:
    js, c = facts['journals'], facts['context']
    deaths = [e for e in js['death']['events'] if 0 <= e['time'] <= c['duration']]
    actions = sorted([(e['time'],kind,e['_source_index']) for kind in ('farm','damage','tower_damage')
                      for e in js[kind]['events'] if 0 <= e['time'] <= c['duration']])
    result=[]
    for i,e in enumerate(deaths):
        end = min(c['duration'],e['time']+max(0,e['timeDead']))
        next_death = deaths[i+1]['time'] if i+1<len(deaths) else c['duration']
        action_index = bisect_left(actions,(end,''))
        action = actions[action_index] if action_index<len(actions) and actions[action_index][0]<next_death else None
        before = economic_state(facts,max(0,e['time']-1))
        after = economic_state(facts,action[0] if action else end)
        health = snapshot(js['health'],e['time']-1,('hp','maxHp','mp','maxMp'))
        result.append({'id':f"death:{e['_source_index']}", 'time':e['time'], 'reported_end':end,
                       'reported_seconds':e['timeDead'], 'next_death_time':next_death,
                       'return_delay_seconds': action[0]-end if action else None,
                       'return_action': {'time':action[0],'kind':action[1],'source_index':action[2]} if action else None,
                       'right_censored': action is None, 'followup_seconds':max(0,next_death-end),
                       'action_journals_eligible': all(js[k]['quality']['eligible'] for k in ('farm','damage','tower_damage')),
                       'buyback_in_interval': any(e['time'] <= b['time'] <= end for b in js['buyback']['events']),
                       'health_before':health,
                       'health_before_return_action':snapshot(js['health'],action[0]-1,('hp','maxHp','mp','maxMp')) if action else None,
                       'state_before':before,'state_after':after,
                       'networth_change': after['networth']-before['networth'] if after['networth'] is not None and before['networth'] is not None else None,
                       'team_delta_change': after['team_delta']-before['team_delta'] if after['team_delta'] is not None and before['team_delta'] is not None else None,
                       'evidence': {'journal':'death','source_index':e['_source_index']},
                       'interpretation':None})
    return result


def combat_episodes(facts: dict) -> dict:
    js, c = facts['journals'],facts['context']
    own = next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
    enemies = {p['heroId'] for p in c['roster'] if p['isRadiant'] != own['isRadiant']}
    # Only target-dealt damage to roster enemies with explicit non-illusion attribution.
    rows = [e for e in js['damage']['events'] if 0<=e['time']<=c['duration'] and e['value']>0
            and e.get('attacker')==c['hero_id'] and e.get('target') in enemies
            and e.get('fromIllusion') is False and e.get('toIllusion') is False]
    clusters=[]
    for e in rows:
        if not clusters or e['time']-clusters[-1]['end']>15:
            clusters.append({'id':f"combat:{len(clusters)}",'start':e['time'],'end':e['time'],'events':0,'damage':0,'targets':set()})
        x=clusters[-1];x['end']=e['time'];x['events']+=1;x['damage']+=e['value'];x['targets'].add(e['target'])
    for x in clusters:
        x['targets']=sorted(x['targets']);x['span_seconds']=x['end']-x['start']
    return {'rule':'target-dealt non-illusion enemy damage; gap<=15s; not a complete teamfight detector',
            'quality':js['damage']['quality'], 'matched_events':len(rows),
            'unselected_events':sum(0<=e['time']<=c['duration'] for e in js['damage']['events'])-len(rows), 'clusters':clusters}


def build_numeric_episodes(facts: dict) -> dict:
    validate_node(facts)
    js,c = facts['journals'],facts['context']
    duration=c['duration'];windows=numeric_windows(facts)
    whole={k:events_in(j,0,duration+1) for k,j in js.items()}
    target=next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
    deaths=death_episodes(facts);combat=combat_episodes(facts)
    summaries=[]
    def add(id: str, value: object, unit: str, journal_name: str, **kwargs: object) -> None:
        summaries.append(measurement(id,value,unit,q=js[journal_name]['quality'],provenance=[js[journal_name]['source_ref']],**kwargs))
    gold=_sum_if(js['gold'],whole['gold'],'amount');xp=_sum_if(js['xp'],whole['xp'],'amount')
    add('economy.gold_flow',_sum_groups(whole['gold'],'amount',('reason','isValidForStats')) if gold is not None else None,'gold','gold',numerator=gold,denominator=1,
        details={'recorded_total':gold,'reported_gpm':target.get('goldPerMinute'),'not_equal_to_networth':True})
    add('xp.gain',_sum_groups(whole['xp'],'amount',('reason',)) if xp is not None else None,'XP','xp',numerator=xp,denominator=1,
        details={'recorded_total':xp,'reported_xpm':target.get('experiencePerMinute'),
                 'residual_vs_reported_xpm':xp-target['experiencePerMinute']*duration/60 if xp is not None and number(target.get('experiencePerMinute')) else None,
                 'event_gaps':gaps([e['time'] for e in whole['xp'] if e['amount']>0],0,duration)})
    levels=[]
    for k in PARAMETERS['level_targets']:
        event=next((e for e in js['level']['events'] if 0<=e['time']<=duration and e['level']>=k),None)
        levels.append({'level':k,'time':event['time'] if event else None,'right_censored':event is None,
                       'source_index':event['_source_index'] if event else None})
    add('xp.level_time',levels if available(js['level']) else None,'seconds','level',kind='source_observation',
        details={'monotone':all(b['level']>=a['level'] for a,b in zip(js['level']['events'],js['level']['events'][1:])),
                 'final_reported':target.get('level'),'last_observed':js['level']['events'][-1]['level'] if js['level']['events'] else None})
    add('farm.last_hits',len(whole['farm']) if available(js['farm']) else None,'count','farm',
        details={'reconciliation':js['farm'].get('reconciliation'),
                 'flags':{k:sum(e.get(k) is True for e in whole['farm']) for k in ('isCreep','isNeutral','isAncient')},
                 'event_gaps':gaps([e['time'] for e in whole['farm']],0,duration),
                 'activity_bin_seconds_proxy':sum(w['activity_bin_seconds_proxy'] for w in windows) if all(w['activity_bin_seconds_proxy'] is not None for w in windows) else None})
    add('death.count',len(whole['death']) if available(js['death']) else None,'count','death',
        details={'spacing':gaps([e['time'] for e in whole['death']],0,duration),'reconciliation':js['death'].get('reconciliation')})
    dead=sum(w['death_seconds_proxy'] for w in windows) if available(js['death']) else None
    add('death.reported_time',dead,'seconds','death',kind='proxy',numerator=dead,denominator=1,
        details={'sum_reported':sum(e['timeDead'] for e in whole['death']), 'buybacks':len(whole['buyback']) if available(js['buyback']) else None})
    add('episodes.return_activity',deaths if available(js['death']) else None,'seconds','death',kind='proxy')
    if any(not js[k]['quality']['eligible'] for k in ('farm','damage','tower_damage')):
        summaries[-1]['coverage'].update(status='conflicting',eligible=False,reason='return-activity journals incomplete/conflicting')
        summaries[-1]['quality_status']='conflicting'
    state_points=[w['state_start'] for w in windows]+[windows[-1]['state_end']]
    summaries.append(measurement('economy.team_state',state_points,
                                 'gold',q=point_quality(sum(p['team_delta'] is not None for p in state_points),len(state_points)),
                                 provenance=[facts['id']],details={'requires_fresh_players':10}))
    eligible=[e for e in whole['kill'] if e['time']+90<=duration]
    followed=[e for e in eligible if any(e['time']<d['time']<=e['time']+90 for d in whole['death'])]
    unique_deaths={d['_source_index'] for d in whole['death'] if any(e['time']<d['time']<=e['time']+90 for e in eligible)}
    add('episodes.post_kill_death',divide(len(followed),len(eligible)) if js['kill']['quality']['eligible'] and js['death']['quality']['eligible'] else None,
        'fraction','kill',numerator=len(followed),denominator=len(eligible),
        details={'unique_deaths':len(unique_deaths),'right_censored_kills':len(whole['kill'])-len(eligible),
                 'death_journal_quality':js['death']['quality'],'dependent_windows':True})
    if not js['death']['quality']['eligible']:
        summaries[-1]['coverage'].update(status=js['death']['quality']['status'],eligible=False,reason='required death journal unavailable/conflicting')
        summaries[-1]['quality_status']=js['death']['quality']['status']
    for id,kind,field,unit in [('combat.damage','damage','value','damage'),('support.healing','heal','value','healing')]:
        total=_sum_if(js[kind],whole[kind],field)
        details={'by_recipient':_sum_groups(whole[kind],field,('target',)), 'final_reported':target.get('heroDamage' if kind=='damage' else 'heroHealing')}
        if kind=='damage':
            details['cluster_summary']={k:v for k,v in combat.items() if k!='clusters'}
            details['attribution']=damage_partition(facts,whole['damage']) if total is not None else None
            details['original_enemy_minus_final']=details['attribution']['original_enemy_targets']-details['final_reported'] if total is not None and number(details['final_reported']) else None
        else: details['self']=sum(w['healing_self'] for w in windows) if total is not None else None
        details['raw_sum_minus_final']=total-details['final_reported'] if total is not None and number(details['final_reported']) else None
        details['reconciliation']='different source scopes possible; residual is not repaired'
        add(id,total,unit,kind,numerator=total,denominator=1,details=details)
    purchases={}
    for e in js['purchase']['events']:
        if e['time']<=duration:purchases.setdefault(str(e['itemId']),{'time':e['time'],'source_index':e['_source_index']})
    add('items.purchase_time',purchases if available(js['purchase']) else None,'seconds','purchase',kind='source_observation')
    for id,kind,field in [('items.use_count','item','itemId'),('abilities.use_count','ability','abilityId'),('vision.placements','wards','type'),('vision.destructions','ward_destruction','isWard'),('objectives.destroyed','objects','npcId')]:
        add(id,_counts(whole[kind],field) if available(js[kind]) else None,'count',kind,
            details={'native_codes':True,'pregame_count':sum(e['time']<0 for e in js[kind]['events'])})
    for id,reason in [('abilities.opportunity','complete cooldown/visibility/inventory state unavailable'),
                      ('vision.effective','visibility, terrain and ward lifetime unavailable'),
                      ('match.conversion','object-side/type attribution not independently validated'),
                      ('space.semantic_regions','map semantics deferred to task 6')]:
        summaries.append(measurement(id,None,'not available',q=quality(state='deferred',reason=reason)))
    # Downstream levels receive this compact carry, never a Sources object or raw journals.
    return node(level=2,context=c,measurements=summaries,source_manifest=facts['sources'],children=[facts],
                payload={'context':c,'sources':facts['sources'],'windows':windows,'combat_episodes':combat,
                         'journal_quality':{k:j['quality'] for k,j in js.items()},
                         'support_actions':facts['support_actions'],
                         'final_conflicts':facts['final_conflicts'], 'finals':c['roster']})
