"""Observed objective milestones, not assumed strategic phase transitions."""
from .evidence import digest
from .episodes import interval_metrics


def build_phases(facts: dict, episodes: list[dict]) -> list[dict]:
    duration = facts['context']['duration']
    boundaries = [(0,'match start',None)]
    for marker in ('TOWER_KILL','BARRACKS_KILL'):
        candidates = [e for e in facts['events'] if e['kind']=='objective' and marker in str(e['data'].get('type'))
                      and 0<e['time']<duration]
        if candidates:
            event=min(candidates,key=lambda e:e['time'])
            boundaries.append((event['time'],f'first recorded {marker}',event['id']))
    boundaries.append((duration+1,'end of match',None))
    boundaries=sorted({b[0]:b for b in boundaries}.values())
    phases=[]
    for start,end in zip(boundaries,boundaries[1:]):
        phase={'id':f"{facts['match_id']}:phase:{digest([start[0],end[0]])[:16]}",
               'start':start[0],'end':end[0],'boundary_reason':[start[1],end[1]],
               'anchors':[v for v in (start[2],end[2]) if v],
               'children':[e['id'] for e in episodes if e['start']<end[0] and e['end']>start[0]]}
        phase['metrics']=interval_metrics(facts,phase)
        phase['limitations']=['Objective milestones are descriptive boundaries, not proof that the laning phase ended.',
                              'Cross-boundary episodes may appear in multiple stages; metrics are recalculated from unique raw events.']
        phases.append(phase)
    return phases
