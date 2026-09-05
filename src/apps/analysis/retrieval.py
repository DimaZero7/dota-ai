"""Explicit ID and interval retrieval with observable pagination."""
from .sources import Sources
from .facts import event_evidence
from .timebases import in_interval
from .context import input_units
from dataclasses import dataclass, field
from collections.abc import Callable


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
    documents={}
    rows=[]
    for event in page:
        ref=event_evidence(sources,event)
        key=event['document']
        documents[key]={k:v for k,v in ref.items() if k not in ('pointer','id')}
        rows.append({'id':event['id'],'time':event['time'],'kind':event['kind'],'slot':event['slot'],
                     'data':{k:v for k,v in event['data'].items() if fields is None or k in fields},
                     'evidence':{'id':ref['id'],'document':key,'pointer':ref['pointer']}})
    return {'query':{'start':start,'end':end,'slot':slot,'kinds':kinds,'fields':fields,'offset':offset},
            'total':len(matches),'events':rows,'documents':documents,
            'next_offset':offset+len(page) if offset+len(page)<len(matches) else None,
            'limitations':['Source-native clocks; pagination and filtered fields may omit relevant context.']}


def detail_reference(result: dict, event: dict) -> dict:
    ref=event['evidence']
    return {**result['documents'][ref['document']], 'id':ref['id'],'pointer':ref['pointer']}


@dataclass
class DrillSession:
    max_calls: int = 3
    max_bytes: int = 8000
    calls: int = 0
    used_bytes: int = 0
    evidence_ids: list[str] = field(default_factory=list)
    pending: list[dict] = field(default_factory=list)

    def request(self, fetch: Callable[[], dict], query: dict) -> dict:
        if self.calls>=self.max_calls or self.used_bytes>=self.max_bytes:
            self.pending.append(query)
            return {'status':'budget_exhausted','pending':query}
        self.calls+=1
        result=fetch()
        remaining=self.max_bytes-self.used_bytes
        while result.get('events') and input_units(result)>remaining:
            result['events'].pop()
            result['next_offset']=result['query']['offset']+len(result['events'])
        if input_units(result)>remaining or (not result.get('events') and result.get('total',0)>0):
            self.pending.append(query)
            return {'status':'budget_exhausted','pending':query}
        self.used_bytes+=input_units(result)
        self.evidence_ids.extend(e['evidence']['id'] for e in result.get('events',[]))
        if result.get('next_offset') is not None:
            self.pending.append({**query,'offset':result['next_offset']})
        return result
