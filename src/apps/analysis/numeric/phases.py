"""L3 consumes L2 only; L4 consumes L3 only."""
from collections import Counter
from statistics import median

from .schemas import NumericError, divide, measurement, node, number, quality, point_quality, validate_node


def total(rows: list[dict], key: str) -> float | None:
    values=[r[key] for r in rows]
    return sum(values) if all(number(v) for v in values) else None


def sum_maps(rows: list[dict], key: str) -> dict | None:
    if any(r.get(key) is None for r in rows):return None
    result=Counter()
    for r in rows:result.update(r[key])
    return dict(sorted(result.items()))


def describe(values: list[float]) -> dict:
    return {'n':len(values),'sum':sum(values),'min':min(values,default=None),'median':median(values) if values else None,
            'max':max(values,default=None)}


def build_numeric_phases(episodes: dict) -> dict:
    validate_node(episodes)
    if episodes['level']!=2:raise NumericError('L3 needs L2')
    c,q=episodes['context'],episodes['journal_quality']
    death_rows=next(m['value'] for m in episodes['measurements'] if m['metric_id']=='episodes.return_activity') or []
    phases=[]
    prev_xp_rate=None
    for start in range(0,c['duration'],600):
        end=min(start+600,c['duration'])
        children=[w for w in episodes['windows'] if start<=w['start']<end]
        if not children or children[0]['start']!=start or children[-1]['end']!=end or any(a['end']!=b['start'] for a,b in zip(children,children[1:])):
            raise NumericError('Phase children must partition time without gaps/overlap')
        exposure=sum(w['exposure_seconds'] for w in children)
        counts={k:sum(w['counts'][k] for w in children) if all(w['counts'][k] is not None for w in children) else None for k in children[0]['counts']}
        xp,gold,dead=total(children,'xp'),total(children,'gold'),total(children,'death_seconds_proxy')
        before,after=children[0]['state_start'],children[-1]['state_end']
        xp_rate=divide(xp,exposure/60)
        state_grid=[w['state_start'] for w in children]+[after]
        transitions=sum(a['team_band']!=b['team_band'] for a,b in zip(state_grid,state_grid[1:]) if a['team_band'] is not None and b['team_band'] is not None)
        observed_pairs=sum(a['team_band'] is not None and b['team_band'] is not None for a,b in zip(state_grid,state_grid[1:]))
        net_delta=after['networth']-before['networth'] if before['networth'] is not None and after['networth'] is not None else None
        team_delta=after['team_delta']-before['team_delta'] if before['team_delta'] is not None and after['team_delta'] is not None else None
        phase={'id':f'p{start}','start':start,'end':end,'exposure_seconds':exposure,'children':[w['id'] for w in children],
               'counts':counts,'xp':xp,'xp_rate':xp_rate,'xp_rate_change':xp_rate-prev_xp_rate if xp_rate is not None and prev_xp_rate is not None else None,
               'xp_by_reason':sum_maps(children,'xp_by_reason'),'gold':gold,'gold_rate':divide(gold,exposure/60),
               'gold_by_reason_validity':sum_maps(children,'gold_by_reason_validity'),
               'farm_flags':sum_maps(children,'farm_flags'),'farm_rate':divide(counts['farm'],exposure/60),
               'death_seconds_proxy':dead,'death_fraction_proxy':divide(dead,exposure),
               'deaths_per_10min':divide(counts['death'],exposure/600),
               'recorded_kill_rate':divide(counts['kill'],exposure/60),
               'recorded_assist_rate':divide(counts['assist'],exposure/60),
               'activity_bin_seconds_proxy':total(children,'activity_bin_seconds_proxy'),
               'damage':total(children,'damage'),'healing':total(children,'healing'),
               'damage_attribution':sum_maps(children,'damage_attribution'),
               'healing_self':total(children,'healing_self'),'tower_damage':total(children,'tower_damage'),
               'state_start':before,'state_end':after,'networth_delta':net_delta,
               'team_delta_change_per_minute':divide(team_delta,exposure/60),
               'team_band_changes':transitions,'observed_state_pairs':observed_pairs,'possible_state_pairs':len(state_grid)-1,
               'minute_xp_distribution':describe([w['xp']*60/w['exposure_seconds'] for w in children if w['xp'] is not None]),
               'minute_farm_distribution':describe([w['counts']['farm']*60/w['exposure_seconds'] for w in children if w['counts']['farm'] is not None])}
        target_side=next(p['isRadiant'] for p in c['roster'] if p['playerSlot']==c['target_slot'])
        allies=[str(p['playerSlot']) for p in c['roster'] if p['isRadiant']==target_side]
        ownslot=str(c['target_slot'])
        player_xp={slot:sum(w['xp_by_player'][slot] for w in children) if all(number(w['xp_by_player'][slot]) for w in children) else None for slot in children[0]['xp_by_player']}
        allied_xp=sum(player_xp[s] for s in allies) if all(player_xp[s] is not None for s in allies) else None
        phase['recorded_xp_team_share']=divide(player_xp[ownslot],allied_xp)
        phase['recorded_xp_team_denominator']=allied_xp
        counterpart=before['counterpart_slot']
        phase['recorded_xp_counterpart_delta']=player_xp[ownslot]-player_xp[str(counterpart)] if counterpart is not None and player_xp[ownslot] is not None and player_xp[str(counterpart)] is not None else None
        clusters=episodes['combat_episodes']['clusters']
        # Each cluster is counted once, assigned by start; damage remains in disjoint windows.
        phase['combat_clusters_started']=sum(start<=x['start']<(end+1 if end==c['duration'] else end) for x in clusters)
        phase['resource_and_combat_minutes']={
            'both':sum((w['counts']['farm'] or 0)>0 and ((w['damage_attribution'] or {}).get('original_enemy_targets') or 0)>0 for w in children),
            'eligible_windows':sum(w['counts']['farm'] is not None and w['damage_attribution'] is not None for w in children),
            'definition':'recorded last hit and damage to original enemy hero within same minute; no causal interpretation'}
        owned_deaths=[d for d in death_rows if start<=d['time']<(end+1 if end==c['duration'] else end)]
        phase['death_duration_distribution']=describe([d['reported_seconds'] for d in owned_deaths])
        phase['return_delay_distribution']=describe([d['return_delay_seconds'] for d in owned_deaths if d['return_delay_seconds'] is not None])
        phase['return_right_censored']=sum(d['right_censored'] for d in owned_deaths)
        phase['quality']=q
        phases.append(phase);prev_xp_rate=xp_rate
    m=[]
    for id,key,unit,journal_name,num,den in [
        ('xp.phase_rate','xp_rate','XP/min','xp','xp','exposure_seconds'),
        ('economy.phase_flow','gold_rate','gold/min','gold','gold','exposure_seconds'),
        ('death.phase_fraction','death_fraction_proxy','fraction','death','death_seconds_proxy','exposure_seconds'),
        ('farm.phase_rate','farm_rate','last hits/min','farm',None,'exposure_seconds')]:
        m.append(measurement(id,[{'start':p['start'],'end':p['end'],'value':p[key],
                                 'numerator':p[num] if num else p['counts']['farm'],
                                 'denominator':p[den] if key=='death_fraction_proxy' else p[den]/60} for p in phases],
                             unit,q=q[journal_name],kind='proxy' if journal_name=='death' else 'derived',provenance=[episodes['id']]))
    m.append(measurement('transition.lead_change',[{'start':p['start'],'changes':p['team_band_changes'],
                         'observed_pairs':p['observed_state_pairs'],'possible_pairs':p['possible_state_pairs'],
                         'delta_per_minute':p['team_delta_change_per_minute']} for p in phases], 'count;gold/min',
                         q=point_quality(sum(p['observed_state_pairs'] for p in phases),sum(p['possible_state_pairs'] for p in phases)),provenance=[episodes['id']]))
    support=episodes['support_actions']
    support_m=measurement('support.actions',{k:support[k] if number(support[k]) else None for k in ('scan_used','ping_used','camp_stack')},
                          'source counts',kind='proxy',q=point_quality(sum(number(support[k]) for k in ('scan_used','ping_used','camp_stack')),3),
                          provenance=[episodes['id']],details={'camp_stack_reason':support['camp_stack_reason']})
    m.append(support_m)
    return node(level=3,context=c,measurements=m,source_manifest=episodes['sources'],children=[episodes],
                payload={'context':c,'sources':episodes['sources'],'phases':phases,'carry':[*episodes['measurements'],support_m],
                         'combat_clusters':episodes['combat_episodes']['clusters'],'final_conflicts':episodes['final_conflicts'],
                         'journal_quality':q})


def build_numeric_match(phases_node: dict) -> dict:
    validate_node(phases_node)
    if phases_node['level']!=3:raise NumericError('L4 needs L3')
    c,ps=phases_node['context'],phases_node['phases']
    carry={m['metric_id']:m for m in phases_node['carry']}
    q=phases_node['journal_quality']
    target=next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
    allykills=[p.get('kills') for p in c['roster'] if p['isRadiant']==target['isRadiant']]
    denominator=sum(allykills) if all(number(v) for v in allykills) else None
    numerator=target['kills']+target['assists'] if number(target.get('kills')) and number(target.get('assists')) else None
    final_conflicts=phases_node['final_conflicts']
    participation_conflicts=[x for x in final_conflicts if (x['field']=='kills' and any(p['playerSlot']==x['slot'] and p['isRadiant']==target['isRadiant'] for p in c['roster'])) or (x['slot']==c['target_slot'] and x['field']=='assists')]
    participation=divide(numerator,denominator)
    pq=quality(conflict=bool(participation_conflicts) or (participation is not None and not 0<=participation<=1),reason='final-source disagreement' if participation_conflicts else None)
    if numerator is None or denominator is None:pq=quality(state='missing',reason='missing final totals')
    duration=c['duration'];dead=total(ps,'death_seconds_proxy');xp=total(ps,'xp');gold=total(ps,'gold')
    compact_keys=('start','end','exposure_seconds','xp','xp_rate','xp_rate_change','gold','gold_rate','farm_rate',
                  'death_seconds_proxy','death_fraction_proxy','damage','healing','tower_damage','networth_delta',
                  'team_band_changes','observed_state_pairs','possible_state_pairs','recorded_xp_team_share',
                  'recorded_xp_counterpart_delta','combat_clusters_started')
    retained_phase_features=('damage_attribution','xp_by_reason','gold_by_reason_validity','farm_flags',
                             'recorded_xp_team_denominator','activity_bin_seconds_proxy','resource_and_combat_minutes',
                             'minute_xp_distribution','minute_farm_distribution','death_duration_distribution',
                             'return_delay_distribution','return_right_censored')
    trajectory=[{**{k:p[k] for k in (*compact_keys,*retained_phase_features)},'last_hits':p['counts']['farm'],'deaths':p['counts']['death'],
                 'state_start':p['state_start'],'state_end':p['state_end']} for p in ps]
    ms=[measurement('match.trajectory',trajectory,'record',provenance=[phases_node['id']],details={'field_quality':q}),
        measurement('combat.participation',participation,'fraction',q=pq,numerator=numerator,denominator=denominator,
                    provenance=[phases_node['id']],details={'source':'final totals; independent of assist journal','conflicts':participation_conflicts}),
        measurement('match.resource_share',[{'time':p['end'],'numerator':p['state_end']['networth'],
                     'denominator':p['state_end']['ally_networth'],'value':p['state_end']['resource_share'],
                     'fresh_players':p['state_end']['fresh_players']} for p in ps], 'fraction',
                     q=point_quality(sum(p['state_end']['resource_share'] is not None for p in ps),len(ps)),provenance=[phases_node['id']])]
    # Bounded fields, not all episode event lists, reach the match representation.
    for id in ('economy.gold_flow','xp.gain','xp.level_time','farm.last_hits','death.count','death.reported_time',
               'items.purchase_time','items.use_count','abilities.use_count','combat.damage','support.healing',
               'vision.placements','vision.destructions','objectives.destroyed','episodes.post_kill_death','support.actions'):
        original=carry[id]
        details=dict(original['details'])
        for key in ('event_gaps','spacing'):
            if key in details:details[key]={k:v for k,v in details[key].items() if k!='internal_gaps_seconds'}
        ms.append({**original,'provenance_ref':[phases_node['id']],'details':details})
    deaths=carry['episodes.return_activity']['value'] or []
    returns=[d['return_delay_seconds'] for d in deaths if d['return_delay_seconds'] is not None]
    ms.append(measurement('episodes.return_activity',describe(returns) if carry['episodes.return_activity']['value'] is not None else None,'seconds',kind='proxy',q=carry['episodes.return_activity']['coverage'],provenance=[phases_node['id']],
                          details={'right_censored':sum(d['right_censored'] for d in deaths),'buybacks_in_death_intervals':sum(d['buyback_in_interval'] for d in deaths),
                                   'drill_ids':[d['id'] for d in deaths],
                                   'action_journals_eligible':all(d['action_journals_eligible'] for d in deaths)}))
    for id,reason in [('sessions.match_context','chronological adjacency not verified; session derivation belongs to task 7'),
                      ('space.occupancy','task 6 spatial temporal-coverage validation'),
                      ('space.isolation','task 6 spatial validation'),
                      ('match.space_distribution','task 6 spatial validation'),
                      ('match.conversion','object attribution/clock semantics not validated'),
                      ('abilities.opportunity','complete availability state missing'),
                      ('vision.effective','effective visibility unavailable'),
                      ('space.semantic_regions','map transform/regions unvalidated')]:
        ms.append(measurement(id,None,'not available',q=quality(state='deferred',reason=reason),provenance=[phases_node['id']]))
    summary={'recorded_xp':xp,'recorded_xp_per_minute':divide(xp,duration/60),'recorded_gold':gold,
             'recorded_gold_per_minute':divide(gold,duration/60),'death_seconds_proxy':dead,'death_fraction_proxy':divide(dead,duration),
             'activity_bin_seconds_proxy':total(ps,'activity_bin_seconds_proxy'),
             'combat_clusters':len(phases_node['combat_clusters']),
             'combat_span_distribution':describe([x['span_seconds'] for x in phases_node['combat_clusters']]),
             'quality':q}
    return node(level=4,context=c,measurements=ms,source_manifest=phases_node['sources'],children=[phases_node],
                payload={'context':c,'summary':summary,'final_source_conflicts':final_conflicts})
