"""Spatial grid and provenance contracts."""
from bisect import bisect_right
from math import isfinite

from ..evidence import digest

VERSION = 'spatial-analysis-1'
DEFAULTS = {'cell_size': 16, 'extent': [0, 256], 'gap_seconds': 5, 'event_age_seconds': 5,
            'phase_seconds': 600, 'state_seconds': 60, 'isolation_step_seconds': 5,
            'minimum_exposure_seconds': 60, 'minimum_deaths': 3,
            'orientation': 'native x right, y up; no side mirroring', 'life_method': 'reported-death-union-1'}
LAYERS = ('farm', 'xp', 'gold', 'damage', 'kill', 'assist', 'death')


class SpatialError(ValueError):
    """Invalid spatial input or incompatible accumulation."""


def numeric(value: object) -> bool:
    return type(value) in (int, float) and isfinite(value)


def grid_cell(x: object, y: object, params: dict) -> str | None:
    lo,hi=params['extent'];size=params['cell_size']
    if not numeric(x) or not numeric(y) or not (lo<=x<hi and lo<=y<hi):return None
    return f'{int((x-lo)//size)},{int((y-lo)//size)}'


def parameters(overrides: dict | None = None) -> dict:
    p={**DEFAULTS,**(overrides or {})}
    if p['extent']!=[0,256] or p['cell_size'] not in (8,16,32) or p['gap_seconds'] not in (2,5,10):
        raise SpatialError('Supported frame: [0,256), cell 8/16/32, gap 2/5/10')
    if any(p[k]!=DEFAULTS[k] for k in DEFAULTS if k not in ('cell_size','gap_seconds')):
        raise SpatialError('Unsupported spatial parameter override')
    if set(p)!=set(DEFAULTS):raise SpatialError('Unknown spatial parameter')
    return p


def signed(data: dict) -> dict:
    return {**data,'revision':digest(data)}


def validate(data: dict) -> None:
    if data.get('schema_version')!=VERSION or data.get('revision')!=digest({k:v for k,v in data.items() if k!='revision'}):
        raise SpatialError('Spatial artifact version/integrity failure')


def prepare_positions(journal: dict, params: dict) -> dict:
    """Same-time duplicates collapse; conflicting points become barriers."""
    groups={}
    for e in journal['events']:
        groups.setdefault(e['time'],[]).append(e)
    rows=[];duplicates=conflicts=out_of_frame=0
    for time,events in sorted(groups.items()):
        coords={(e.get('x'),e.get('y')) for e in events}
        duplicates+=max(0,len(events)-1)
        cell=grid_cell(events[0].get('x'),events[0].get('y'),params) if len(coords)==1 else None
        conflicts+=len(coords)>1;out_of_frame+=len(coords)==1 and cell is None
        rows.append({'time':time,'x':events[0].get('x'),'y':events[0].get('y'),'cell':cell,
                     'source_index':events[0]['_source_index']})
    usable=journal['quality']['status']!='unavailable' and journal['quality'].get('invalid_events',0)==0
    return {'rows':rows,'times':[e['time'] for e in rows], 'usable':usable,
            'audit':{'rows':len(rows),'duplicate_timestamps':duplicates,'conflicting_timestamps':conflicts,
                     'out_of_frame':out_of_frame,'invalid_rows':journal['quality'].get('invalid_events',0)}}


def fresh_position(stream: dict, time: float, max_age: float) -> dict | None:
    if not stream['usable']:return None
    index=bisect_right(stream['times'],time)-1
    if index<0:return None
    e=stream['rows'][index]
    return e if e['cell'] is not None and time-e['time']<=max_age else None


def interval_position(stream: dict, time: float, max_gap: float) -> dict | None:
    """Only intervals bracketed by two close observations receive time."""
    if not stream['usable']:return None
    index=bisect_right(stream['times'],time)-1
    if index<0 or index+1>=len(stream['rows']):return None
    a,b=stream['rows'][index:index+2]
    return a if a['cell'] is not None and b['cell'] is not None and 0<b['time']-a['time']<=max_gap else None


def union_intervals(intervals: list[tuple]) -> list[list]:
    result=[]
    for start,end in sorted(intervals):
        if end<=start:continue
        if result and start<=result[-1][1]:result[-1][1]=max(result[-1][1],end)
        else:result.append([start,end])
    return result
