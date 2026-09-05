"""Addressed retrieval with persistent per-review accounting and optional authored checks."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..cumulative.storage import connect, decode_checked
from ..cumulative.schemas import encode, contribution
from ..numeric.schemas import validate_node, measures
from ..evidence import digest
from .schemas import AnalystError, size, text, bilingual
from .storage import session, checked
from .services import group_view, evidence_revision


def identity(row: dict) -> dict:
    return {**{k:row[k] for k in ('match_id','start_time','duration','win','context')},
            'date_utc':datetime.fromtimestamp(row['start_time'],timezone.utc).isoformat() if row['start_time'] is not None else None}


def envelope(db: sqlite3.Connection, contract_id: str, match_id: int) -> dict:
    r=db.execute('SELECT r.payload FROM revisions r JOIN matches m ON m.contract=r.contract AND m.mid=r.mid AND m.revision=r.revision WHERE m.contract=? AND m.mid=?',(contract_id,match_id)).fetchone()
    if r is None:raise AnalystError('Match not in this cumulative population')
    data=json.loads(r[0])
    if data!=contribution(data['signature'],spatial=data['spatial']):raise AnalystError('Stored match contribution changed')
    return data


def numeric_node(directory: Path, level: int, signature: dict) -> tuple[dict,int]:
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    def load(lvl: int) -> dict:
        name=f'L{lvl}.json';body=(directory/name).read_bytes();expected=manifest['files'][name]
        if hashlib.sha256(body).hexdigest()!=expected['sha256'] or len(body)!=expected['bytes']:raise AnalystError('Numeric file integrity failure')
        data=json.loads(body);validate_node(data)
        if data['revision']!=expected['revision'] or data['scope']['match_id']!=signature['match_id'] or data['scope']['account_id']!=signature['account_id'] or data['source_manifest_ref']!=signature['source_manifest_ref']:
            raise AnalystError('Numeric node identity/source mismatch')
        return data
    data=load(level);read=1
    if level==2:expected=signature['dependencies'].get(data['id'])
    else:
        parent=load(4);read+=1
        if signature['dependencies'].get(parent['id'])!=parent['revision']:raise AnalystError('Numeric L4 revision differs from signature')
        expected=parent['children_manifest_ref'].get(data['id'])
    if expected!=data['revision']:raise AnalystError('Lower revision differs from imported signature')
    return data,read


def drill(*, path: Path, session_id: str, kind: str, target: str, reason: str,
          metric: str = 'death_fraction', selector: str | None = None, root: Path | None = None,
          numeric_bundles: dict[int,str] | None = None) -> dict:
    text(reason,'substantive question/reason',1000)
    if kind in ('phase','episode') and len(reason.strip())<30:raise AnalystError('Explain the contradiction or uncertainty requiring lower detail')
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE');packet,usage,evidence=session(db,session_id);limits=packet['budgets']
        if usage['drill_calls']>=limits['drill_calls']:raise AnalystError('Drill call budget exhausted')
        card_count=lower_count=0;key=packet['contract_id'];extra={};newrefs={}
        if kind=='group':
            gid=target.removeprefix('group:')
            r=db.execute('SELECT * FROM groups WHERE contract=? AND gid=?',(key,gid)).fetchone()
            if r is None or r['kind']!='numeric':raise AnalystError('Numeric group required')
            g=decode_checked(r['payload'],r['revision']);recent=json.loads(r['recent']) if r['recent'] else None
            if metric not in g['summary']['metrics']:raise AnalystError('Metric not in group')
            rows=[json.loads(v[0]) for v in db.execute('SELECT payload FROM members WHERE contract=? AND gid=? ORDER BY mid',(key,gid))]
            valid=sorted((v for v in rows if v['metrics'].get(metric,{}).get('eligible')),key=lambda v:(v['metrics'][metric]['value'],v['row']['match_id']))
            selected=[]
            for index,label in ((len(valid)//2,'median-order representative'),(0,'lower tail'),(len(valid)-1,'upper tail')):
                if valid and valid[index]['row']['match_id'] not in {v['match_id'] for v in selected}:
                    v=valid[index];selected.append({**identity(v['row']),'measure':v['metrics'][metric],'selection':label})
            card_count=len(selected);extra={'group':group_view(g,recent,[metric]),'examples':selected,
                'selection':'Deterministic median/lower/upper eligible values; tails are candidates for counterexamples, not proof. Outcome/drafts may explain differences.',
                'unexamined_eligible_cases':len(valid)-len(selected)}
            ref='group:'+gid;revision=evidence_revision(g,recent);newrefs[ref]=revision
        elif kind in ('match','phase','episode'):
            value=envelope(db,key,int(target));s=value['signature'];card_count=1
            extra={'match':identity(s),'signature_revision':s['revision'],'contribution_revision':value['revision']}
            if kind=='match':
                extra['metrics']={k:s['metrics'][k] for k in packet['metrics'] if k in s['metrics']}
                extra['phase_selectors']=[p['phase'] for p in s['phases']]
                extra['episode_selector']='longest reported death, or explicit numeric episode ID'
            else:
                if root is None or int(target) not in (numeric_bundles or {}):raise AnalystError('Explicit numeric bundle registry required')
                directory=(root/numeric_bundles[int(target)]).resolve();directory.relative_to(root.resolve())
                node,lower_count=numeric_node(directory,3 if kind=='phase' else 2,s)
                if kind=='phase':
                    selected=next((p for p in node['phases'] if p['start']==int(selector)),None)
                    if selected is None:raise AnalystError('Unknown phase')
                    fields=('id','start','end','exposure_seconds','xp','xp_rate','gold','gold_rate','death_seconds_proxy','death_fraction_proxy','counts','tower_damage','state_start','state_end','recorded_xp_team_share','recorded_xp_team_denominator','return_right_censored')
                    extra['phase']={k:selected[k] for k in fields}
                    extra['quality']={k:selected['quality'][k] for k in ('xp','gold','death')}
                else:
                    deaths=measures(node)['episodes.return_activity']['value'] or []
                    selected=max(deaths,key=lambda d:d['reported_end']-d['time'],default=None) if selector=='longest' else next((d for d in deaths if d['id']==selector),None)
                    if selected is None:raise AnalystError('Unknown episode; no observed death to inspect')
                    extra['episode']=selected
                    extra['selection']='Longest reported death interval; selected by duration, not inferred mistake' if selector=='longest' else 'Explicit episode ID'
                    extra['windows']=[{k:w[k] for k in ('id','start','end','counts','xp','gold','state_start','state_end')} for w in node['windows'] if w['start']<=selected['time']<w['end'] or w['start']<=selected['reported_end']<w['end']][:2]
                extra['node_ref']={node['id']:node['revision']};extra['source_manifest_ref']=s['source_manifest_ref']
                extra['limitations']='Anchored numeric snapshot; no re-reading all raw events. No observed intent, full vision/cooldowns or established causal error.'
            ref=f'{kind}:{target}:{selector or "whole"}';revision=digest(extra);newrefs[ref]=revision
        else:raise AnalystError('Unknown drill kind')
        result={'kind':kind,'ref':ref,'revision':revision,'reason':reason,'data':extra,'interpretation':None}
        input_revision=digest([ref,revision,reason])
        cached=db.execute('SELECT revision,payload FROM analyst_lower WHERE input_revision=? ORDER BY rowid DESC LIMIT 1',(input_revision,)).fetchone() if kind in ('phase','episode') else None
        result['interpretation_input_revision']=input_revision
        if cached:
            result['interpretation']={**checked(cached['payload'],cached['revision']),'revision':cached['revision']}
            result['data']={'match':extra['match'],'unchanged_detail_revision':revision,
                            'detail_omitted':'Already assessed unchanged lower input; original detail retained in the earlier drill journal.'}
        amount=size(result)
        if amount>limits['drill_single_bytes'] or usage['drill_bytes']+amount>limits['drill_total_bytes']:raise AnalystError('Drill response exceeds byte allowance; request narrower detail')
        usage['drill_calls']+=1;usage['drill_bytes']+=amount;usage['cards_read']+=card_count;usage['lower_nodes_read']+=lower_count
        usage['reused_lower_answers']+=bool(cached);evidence.update(newrefs)
        db.execute('INSERT INTO analyst_drills VALUES(?,?,?)',(session_id,usage['drill_calls'],encode(result)))
        db.execute('UPDATE analyst_sessions SET usage=?,evidence=? WHERE id=?',(encode(usage),encode(evidence),session_id))
        db.execute('COMMIT');return result


def accept_lower(*, path: Path, session_id: str, ref: str, response: dict) -> dict:
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE');packet,usage,evidence=session(db,session_id)
        if response.get('author')!='current Codex':raise AnalystError('Explicit current Codex authorship required')
        rows=[json.loads(r[0]) for r in db.execute('SELECT payload FROM analyst_drills WHERE session=? ORDER BY ordinal',(session_id,))]
        item=next((v for v in reversed(rows) if v['ref']==ref and v['kind'] in ('phase','episode')),None)
        if item is None or response.get('input_revision')!=item['interpretation_input_revision']:raise AnalystError('Opened lower input with matching revision required')
        for k in ('assessment','alternative','uncertainty','next_check'):bilingual(response.get(k),k)
        if response.get('kind') not in ('observation','hypothesis','interpretation') or response.get('basis')!=[ref]:raise AnalystError('Structured lower assessment must cite its addressed input')
        if size(response)>4000:raise AnalystError('Lower answer exceeds 4000 bytes')
        record={'input_revision':item['interpretation_input_revision'],'response':response,'validation':'authored assessment, not a computed coaching label'}
        revision=digest(record)
        old=db.execute('SELECT revision FROM analyst_lower WHERE input_revision=?',(record['input_revision'],)).fetchone()
        if old and old[0]!=revision:raise AnalystError('Unchanged lower input already has an accepted assessment')
        db.execute('INSERT OR IGNORE INTO analyst_lower VALUES(?,?,?)',(revision,record['input_revision'],encode(record)))
        if not old:usage['lower_model_answers']+=1
        db.execute('UPDATE analyst_sessions SET usage=? WHERE id=?',(encode(usage),session_id))
        db.execute('COMMIT');return {**record,'revision':revision}
