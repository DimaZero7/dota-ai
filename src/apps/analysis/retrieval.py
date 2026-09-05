"""Explicit ID and interval retrieval with observable pagination."""
from .sources import Sources
from .facts import event_evidence
from .timebases import in_interval


def get_finding(registry: dict, finding_id: str) -> dict:
    if finding_id not in registry:
        raise ValueError('Unknown finding ID')
    return registry[finding_id]


def list_children(registry: dict, finding_id: str, *, offset: int = 0, limit: int = 20) -> dict:
    if offset<0 or not 1<=limit<=100:
        raise ValueError('Invalid page')
    ids=get_finding(registry,finding_id).get('children',[])
    return {'ids':ids[offset:offset+limit],'total':len(ids),
            'next_offset':offset+limit if offset+limit<len(ids) else None}


def query_events(*, sources: Sources, facts: dict, start: float, end: float,
                 slot: int | None = None, kinds: list[str] | None = None,
                 fields: list[str] | None = None, offset: int = 0, limit: int = 20) -> dict:
    if start>=end or offset<0 or not 1<=limit<=100:
        raise ValueError('Invalid event interval/page')
    matches=[e for e in facts['events'] if in_interval(e['time'],start,end)
             and (slot is None or e['slot']==slot) and (kinds is None or e['kind'] in kinds)]
    page=matches[offset:offset+limit]
    return {'query':{'start':start,'end':end,'slot':slot,'kinds':kinds,'fields':fields,'offset':offset},
            'total':len(matches),'events':[{'id':e['id'],'time':e['time'],'kind':e['kind'],'slot':e['slot'],
                'data':{k:v for k,v in e['data'].items() if fields is None or k in fields},
                'evidence':event_evidence(sources,e)} for e in page],
            'next_offset':offset+len(page) if offset+len(page)<len(matches) else None,
            'limitations':['Source-native clocks; pagination and filtered fields may omit relevant context.']}
