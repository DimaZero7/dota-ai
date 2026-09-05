"""Event-anchored intervals with explicit context and expandable boundaries."""
from collections import Counter

from .evidence import digest
from .timebases import in_interval


def detect_episodes(facts: dict) -> list[dict]:
    slot = facts['context']['target_slot']
    duration = facts['context']['duration']
    intervals = []

    def add(kind: str, start: float, end: float, anchors: list[str], reason: str) -> None:
        start,end = max(-120,start), min(duration+1,end)
        intervals.append({'id':f"{facts['match_id']}:episode:{digest([kind,start,end,anchors])[:16]}",
                          'kind':kind,'start':start,'end':end,'anchors':anchors,'boundary_reason':reason})

    for event in facts['events']:
        t = event['time']
        if event['slot']==slot and event['kind']=='death':
            add('risk',t-60,t+max(30,event['data'].get('timeDead') or 0)+1,[event['id']],'death plus preparation and recorded respawn duration')
        elif event['kind']=='fight':
            add('fight',t-30,event['data'].get('end',t)+31,[event['id']],'OpenDota fight grouping with surrounding context')
        elif event['slot']==slot and event['kind']=='purchase':
            add('items',t-30,t+91,[event['id']],'recorded STRATZ purchase and following actions')
        elif event['kind']=='objective':
            add('objectives',t-30,t+61,[event['id']],'recorded objective event and surrounding team actions')
    hits = [e for e in facts['events'] if e['slot']==slot and e['kind']=='last_hit']
    group = []
    for event in hits:
        if group and (event['time']-group[-1]['time']>45 or event['time']-group[0]['time']>180):
            add('farm',group[0]['time']-15,group[-1]['time']+16,[group[0]['id'],group[-1]['id']],
                'observed last-hit sequence; split by a gap or bounded observation length')
            group = []
        group.append(event)
    if group:
        add('farm',group[0]['time']-15,group[-1]['time']+16,[group[0]['id'],group[-1]['id']],'observed last-hit sequence')
    for event in facts['events']:
        if event['slot']==slot and event['kind']=='kill':
            add('positive_outcome',event['time']-30,event['time']+31,[event['id']],
                'target kill: favorable local outcome, not proof of a good decision')
    combat = sorted({0,duration,*[e['time'] for e in facts['events'] if e['slot']==slot
                    and e['kind'] in ('kill','death','damage') and 0<=e['time']<=duration]})
    quiet = sorted([(a,b) for a,b in zip(combat,combat[1:]) if b-a>=45],key=lambda v:v[1]-v[0],reverse=True)[:3]
    for a,b in quiet:
        anchors = [e['id'] for e in facts['events'] if e['slot']==slot and a<e['time']<b][:1]
        add('control',a+0.001,b,anchors,'long gap without target recorded kills/deaths/dealt damage; other threats may exist')
    return sorted(intervals,key=lambda e:(e['start'],e['end'],e['id']))


def interval_metrics(facts: dict, episode: dict) -> dict:
    slot = facts['context']['target_slot']
    target = [e for e in facts['events'] if e['slot']==slot and in_interval(e['time'],episode['start'],episode['end'])]
    return {'counts':dict(Counter(e['kind'] for e in target)),
            'interval_seconds':episode['end']-episode['start'],
            'count_method':'target slot; source-native clocks; half-open interval; event IDs unique',
            'participants_with_recorded_combat':sorted({e['slot'] for e in facts['events']
                if e['slot'] is not None and e['kind'] in ('kill','death','damage','heal')
                and in_interval(e['time'],episode['start'],episode['end'])}),
            'participation_note':'same time interval does not prove same location or same fight'}


def timeline_coverage(episodes: list[dict], duration: float) -> dict:
    end = 0
    uncovered = []
    for episode in sorted(episodes,key=lambda e:e['start']):
        a,b = max(0,episode['start']),min(duration,episode['end'])
        if a>end:
            uncovered.append([end,a])
        end=max(end,b)
    if end<duration:
        uncovered.append([end,duration])
    return {'duration':duration,'uncovered_intervals':uncovered,
            'covered_seconds':duration-sum(b-a for a,b in uncovered),
            'note':'coverage means selected intervals, not verified model interpretation'}
