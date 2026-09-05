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
