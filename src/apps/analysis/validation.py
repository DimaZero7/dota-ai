"""Reproducible factual checks, not model answers used as ground truth."""
from collections import Counter
import math

from .sources import Sources
from .facts import event_evidence
from .evidence import resolve


def validate_facts(sources: Sources, facts: dict) -> dict:
    events = facts['events']
    if len({e['id'] for e in events}) != len(events):
        raise ValueError('Duplicate normalized event IDs')
    if any(not math.isfinite(e['time']) for e in events):
        raise ValueError('Invalid event time')
    slot = facts['context']['target_slot']
    target = next(p for p in facts['context']['roster'] if p['playerSlot']==slot)
    counts = Counter(e['kind'] for e in events if e['slot']==slot)
    samples = {}
    for event in events:
        if event['kind'] not in samples:
            raw = resolve(root=sources.root,ref=event_evidence(sources,event))
            if any(raw.get(k) != v for k,v in event['data'].items()):
                raise ValueError('Normalized event differs from source')
            samples[event['kind']] = event['id']
    return {'status':'checked','event_count':len(events),'sampled_kinds':len(samples),
            'target_counts':dict(counts),
            'journal_vs_total':{kind:{'journal':counts[kind] if facts['context']['journal_available'][kind] else None,'total':target[field],
                                     'equal':counts[kind]==target[field] if facts['context']['journal_available'][kind] else None}
                                for kind,field in [('kill','kills'),('death','deaths'),('assist','assists'),('last_hit','numLastHits')]},
            'clock_check':facts['clocks']['target_kill_times'],
            'limitations':['Source pointer tests sample one event per kind; they do not validate every source event semantically.',
                           'Journal-total disagreement is reported, not repaired by fabricated events.']}
