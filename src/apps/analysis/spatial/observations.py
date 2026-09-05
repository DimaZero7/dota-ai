"""Spatial L2: bounded temporal support, located events and observed transitions."""
import math
from bisect import bisect_right
from collections import Counter

from ..numeric.schemas import validate_node
from ..numeric.episodes import economic_state
from .schemas import VERSION, LAYERS, SpatialError, parameters, prepare_positions, fresh_position, interval_position, grid_cell, union_intervals, signed


def _segment_at(segments: list, times: list, time: float) -> dict | None:
    index=bisect_right(times,time)-1
    return segments[index] if index>=0 and segments[index]['start']<=time<segments[index]['end'] else None


def build_observations(facts: dict, *, overrides: dict | None = None) -> dict:
    validate_node(facts)
    if facts['level']!=1:raise SpatialError('Spatial observations require numeric L1')
    p=parameters(overrides);c=facts['context'];duration=c['duration'];slot=str(c['target_slot'])
    own=next(x for x in c['roster'] if x['playerSlot']==c['target_slot'])
    streams={s:prepare_positions(player['position'],p) for s,player in facts['players'].items()}
    stream=streams[slot];js=facts['journals']
    death_known=js['death']['quality']['eligible']
    dead=union_intervals([(max(0,e['time']),min(duration,e['time']+e['timeDead'])) for e in js['death']['events'] if e['timeDead']>=0]) if death_known else []
    def life(time: float) -> str:
        if not death_known:return 'unknown_life'
        return 'reported_dead' if any(a<=time<b for a,b in dead) else 'outside_reported_death'
    state_by_minute={t:economic_state(facts,t)['team_band'] or 'unknown' for t in range(0,duration,60)}
    def minute(time: float) -> int:return min(int(time//60)*60,((duration-1)//60)*60)
    boundaries=sorted({0,duration,*[t for t in stream['times'] if 0<t<duration],
                       *[t for interval in dead for t in interval if 0<t<duration],*range(60,duration,60)})
    segments=[]
    for start,end in zip(boundaries,boundaries[1:]):
        position=interval_position(stream,start,p['gap_seconds'])
        segments.append({'start':start,'end':end,'cell':position['cell'] if position else None,
                         'life':life(start),'phase':int(start//600)*600,'state':state_by_minute[minute(start)]})
    segment_times=[s['start'] for s in segments]
    events=[];excluded=Counter();audit_pairs={k:[] for k in ('farm','xp','kill','assist','death','wards')}
    enemies={x['heroId'] for x in c['roster'] if x['isRadiant']!=own['isRadiant']}
    for kind in (*LAYERS,'wards'):
        for e in js[kind]['events']:
            time=e['time']
            if not 0<=time<=duration:continue
            position=fresh_position(stream,time,p['event_age_seconds'])
            direct=grid_cell(e.get('positionX'),e.get('positionY'),p)
            if kind in audit_pairs and direct and position:
                audit_pairs[kind].append(math.hypot(e['positionX']-position['x'],e['positionY']-position['y']))
            if kind=='wards':continue  # Audit only: ward placement is not player presence.
            if kind=='damage' and not (e.get('attacker')==c['hero_id'] and e.get('target') in enemies and
                                      e.get('toIllusion') is False and e.get('fromIllusion') is False and e.get('fromNpc')==0):
                excluded['damage_non_original_or_unknown_actor']+=1;continue
            value=e['amount'] if kind in ('xp','gold') else e['value'] if kind=='damage' else 1
            cell=direct if kind=='death' else position['cell'] if position else None
            # A contradictory direct death location is retained as an unknown position.
            disagreement=kind=='death' and direct is not None and position is not None and (e['positionX'],e['positionY'])!=(position['x'],position['y'])
            if disagreement:cell=None
            before=math.nextafter(time,-math.inf) if kind=='death' or time==duration else time
            supported=_segment_at(segments,segment_times,before)
            rate_eligible=bool(cell is not None and supported and supported['cell']==cell and supported['life']=='outside_reported_death' and js[kind]['quality']['eligible'])
            group_time=max(0,before)
            events.append({'kind':kind,'time':time,'value':value,'cell':cell,'phase':min(int(group_time//600)*600,((duration-1)//600)*600),
                           'state':state_by_minute[minute(group_time)],'rate_eligible':rate_eligible,
                           'location_method':'direct_death' if kind=='death' else 'player_position_age_le_5s',
                           'position_age_seconds':time-position['time'] if position else None,
                           'direct_location_disagreement':disagreement,'source_index':e['_source_index']})
    transitions=[]
    for previous,current in zip(segments,segments[1:]):
        if (previous['end']==current['start'] and previous['cell'] is not None and current['cell'] is not None and
            previous['cell']!=current['cell'] and previous['life']==current['life']=='outside_reported_death'):
            transitions.append({'time':current['start'],'from':previous['cell'],'to':current['cell'],
                                'phase':current['phase'],'state':current['state']})
    isolation=[];allies=[str(x['playerSlot']) for x in c['roster'] if x['isRadiant']==own['isRadiant'] and x['playerSlot']!=c['target_slot']]
    for time in range(0,duration,5):
        support=_segment_at(segments,segment_times,time)
        target=fresh_position(stream,time,5);others=[fresh_position(streams[s],time,5) for s in allies]
        distance=min(math.hypot(target['x']-v['x'],target['y']-v['y']) for v in others) if target and all(others) and support and support['cell'] is not None and support['life']=='outside_reported_death' else None
        isolation.append({'time':time,'distance':distance,'phase':int(time//600)*600,'state':state_by_minute[minute(time)]})
    audit={'positions':{s:v['audit'] for s,v in streams.items()},
           'target_range':{axis:[min((e[axis] for e in stream['rows']),default=None),max((e[axis] for e in stream['rows']),default=None)] for axis in ('x','y')},
           'gaps_seconds':{str(k):v for k,v in sorted(Counter(b-a for a,b in zip(stream['times'],stream['times'][1:])).items())},
           'paired_event_position':{k:{'n':len(v),'exact':sum(x==0 for x in v),'within4':sum(x<=4 for x in v),'max_distance':max(v,default=None)} for k,v in audit_pairs.items()},
           'initial_observations':[{'slot':x['playerSlot'],'side':'radiant' if x['isRadiant'] else 'dire',
                                    'position':{k:streams[str(x['playerSlot'])]['rows'][0][k] for k in ('time','x','y')} if streams[str(x['playerSlot'])]['rows'] else None} for x in c['roster']],
           'world_units':'unverified; source units only','orientation':'plot convention x right/y up; no verified terrain overlay',
           'death_time':'source estimate; not independently verified alive state'}
    return signed({'schema_version':VERSION,'level':2,'id':f"{c['match_id']}:spatial:L2",'context':c,
                   'parameters':p,'source_refs':facts['sources'],'dependencies':{facts['id']:facts['revision']},
                   'segments':segments,'events':events,'transitions':transitions,'isolation':isolation,
                   'death_intervals':dead,'life_status_available':death_known,'audit':audit,'excluded':dict(excluded),
                   'journal_quality':{k:js[k]['quality'] for k in LAYERS}})


def route_after(observations: dict, *, time: float, seconds: int = 60, limit: int = 30) -> dict:
    from .schemas import validate
    validate(observations)
    if seconds<=0 or seconds>300 or not 1<=limit<=100 or not 0<=time<=observations['context']['duration']:
        raise SpatialError('Invalid route interval/limit')
    end=min(time+seconds,observations['context']['duration']);runs=[]
    for s in observations['segments']:
        a,b=max(time,s['start']),min(end,s['end'])
        if b<=a:continue
        key=(s['cell'],s['life'])
        if runs and (runs[-1]['cell'],runs[-1]['life'])==key and runs[-1]['end']==a:runs[-1]['end']=b
        else:runs.append({'start':a,'end':b,'cell':s['cell'],'life':s['life']})
    return {'start':time,'end':end,'runs':runs[:limit],'total_runs':len(runs),'omitted_runs':max(0,len(runs)-limit),
            'meaning':'observed cell sequence; gaps interrupt paths; no intent or walkable route inference'}


def compare_routes(observations: dict, *, before: float, after: float, seconds: int = 60) -> dict:
    """Compare observed cell-time distributions, not inferred travel decisions."""
    if not 0<=before<=after<=observations['context']['duration']:
        raise SpatialError('Invalid route comparison anchors')
    left=route_after(observations,time=max(0,before-seconds),seconds=max(1,min(seconds,before)),limit=100)
    right=route_after(observations,time=after,seconds=seconds,limit=100)
    # Do not include time after the anchor when the left window is clipped at zero.
    left['end']=before
    left['runs']=[{**r,'end':min(r['end'],before)} for r in left['runs'] if r['start']<before]
    if before==0:left['total_runs']=left['omitted_runs']=0
    def distribution(start: float, end: float) -> dict:
        cells={};covered=0
        for s in observations['segments']:
            dt=max(0,min(end,s['end'])-max(start,s['start']))
            if s['cell'] is not None and s['life']=='outside_reported_death':
                cells[s['cell']]=cells.get(s['cell'],0)+dt;covered+=dt
        return {'observed_seconds':covered,'window_seconds':end-start,
                'cell_shares':{k:v/covered for k,v in cells.items() if v>0} if covered else {}}
    a=distribution(left['start'],before);b=distribution(after,right['end'])
    distance=sum(abs(a['cell_shares'].get(k,0)-b['cell_shares'].get(k,0)) for k in a['cell_shares'].keys()|b['cell_shares'].keys())/2 if a['observed_seconds'] and b['observed_seconds'] else None
    return {'before':left,'after':right,'before_distribution':a,'after_distribution':b,
            'cell_distribution_total_variation':distance,
            'meaning':'0 = same observed cell-time shares; 1 = disjoint. Coverage and location change only, not action impact.'}
