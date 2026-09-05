"""Optional current-Codex review of one numeric episode with dependency checks."""
import hashlib
import json
from pathlib import Path

from ..evidence import digest
from .schemas import NumericError, measures
from .storage import load_node, write_json


def _verify_sources(root: Path, sources: dict) -> None:
    for ref in sources.values():
        file=(root/ref['file']).resolve();file.relative_to(root.resolve())
        if hashlib.sha256(file.read_bytes()).hexdigest()!=ref['sha256']:
            raise NumericError('Review source revision changed')


def prepare_numeric_review(*, root: Path, directory: Path, episode_id: str, question: str,
                           store: Path, budget_bytes: int = 16000) -> dict:
    l2=load_node(directory,2)
    _verify_sources(root,l2['sources'])
    if not isinstance(question,str) or not question.strip():raise NumericError('Review question required')
    episodes=measures(l2)['episodes.return_activity']['value'] or []
    episode=next((e for e in episodes if e['id']==episode_id),None)
    if episode is None:raise NumericError('Unknown death episode; choose an explicit drill ID')
    windows=[{k:w[k] for k in ('id','start','end','counts','xp','gold','damage','state_start','state_end')}
             for w in l2['windows'] if w['start']<episode['reported_end']+60 and w['end']>episode['time']-60]
    packet={'version':'numeric-episode-review-1','question':question,'episode':episode,'context':l2['context'],
            'windows':windows,'quality':l2['journal_quality'],'dependencies':{l2['id']:l2['revision']},
            'instructions':'Current Codex: separate observation/hypothesis; cite episode or window IDs. Explain alternatives, uncertainty and next check. No inferred intent, complete cooldowns, visibility or death=error.',
            'answer_limit_bytes':8000,'input_limit_bytes':budget_bytes}
    # Budget includes the final hash field and envelope, not just the payload.
    packet['packet_id']=digest(packet)
    size=len(json.dumps(packet,ensure_ascii=False,separators=(',',':')).encode())
    if size>budget_bytes:raise NumericError(f'Review input budget exceeded: {size}>{budget_bytes}')
    write_json(store/'packets'/f"{packet['packet_id']}.json",packet)
    return packet


def accept_numeric_review(*, root: Path, directory: Path, store: Path, packet: dict, response: dict) -> dict:
    if packet.get('packet_id')!=digest({k:v for k,v in packet.items() if k!='packet_id'}):
        raise NumericError('Review packet changed')
    l2=load_node(directory,2);_verify_sources(root,l2['sources'])
    if packet['dependencies']!={l2['id']:l2['revision']}:raise NumericError('Review dependencies stale')
    if response.get('packet_id')!=packet['packet_id'] or response.get('author')!='current Codex':
        raise NumericError('Explicit current-Codex response for this packet required')
    if not isinstance(response.get('summary'),str) or not response['summary'].strip():raise NumericError('Summary required')
    claims=response.get('claims')
    if not isinstance(claims,list) or not 1<=len(claims)<=4:raise NumericError('One to four claims required')
    allowed={packet['episode']['id'],*(w['id'] for w in packet['windows'])}
    for claim in claims:
        if claim.get('kind') not in ('observation','interpretation','hypothesis'):raise NumericError('Claim kind required')
        if any(not isinstance(claim.get(k),str) or not claim[k].strip() for k in ('statement','alternative','uncertainty','check')):
            raise NumericError('Claim explanation/uncertainty required')
        if not isinstance(claim.get('basis'),list) or not claim['basis'] or not set(claim['basis'])<=allowed:
            raise NumericError('Claim must cite selected episode/windows')
    if len(json.dumps(response,ensure_ascii=False,separators=(',',':')).encode())>packet['answer_limit_bytes']:
        raise NumericError('Review answer budget exceeded')
    record={'version':packet['version'],'packet':packet,'response':response,'semantic_truth_validated':False}
    record['revision']=digest(record)
    write_json(store/'accepted'/f"{packet['packet_id']}.json",record)
    return record


def read_numeric_review(*, root: Path, directory: Path, store: Path, packet_id: str) -> dict | None:
    if len(packet_id)!=64 or any(c not in '0123456789abcdef' for c in packet_id):raise NumericError('Invalid packet ID')
    path=store/'accepted'/f'{packet_id}.json'
    if not path.exists():return None
    record=json.loads(path.read_text(encoding='utf-8'))
    if record.get('revision')!=digest({k:v for k,v in record.items() if k!='revision'}):raise NumericError('Review record changed')
    l2=load_node(directory,2);_verify_sources(root,l2['sources'])
    if record['packet']['dependencies']!={l2['id']:l2['revision']}:raise NumericError('Review dependencies stale')
    return record
