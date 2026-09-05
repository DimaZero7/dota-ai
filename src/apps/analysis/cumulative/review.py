"""Versioned evidence references and explicit targeted rebuild planning."""
import json
from pathlib import Path

from ..evidence import digest
from .storage import connect, register
from .schemas import CumulativeError, encode


def save_claim(*, path: Path, contract_id: str, claim_id: str, text: str,
               basis: dict[str,str], expected_generation: int) -> None:
    """Persist an existing authored interpretation; never invent or auto-refresh its text."""
    if not text.strip() or not basis:raise CumulativeError('Authored text and versioned evidence required')
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            head=db.execute('SELECT generation FROM contracts WHERE id=?',(contract_id,)).fetchone()
            if head is None or head[0]!=expected_generation:raise CumulativeError('Stale analyst generation')
            state=json.loads(db.execute('SELECT payload FROM states WHERE contract=?',(contract_id,)).fetchone()[0])
            for gid,revision in basis.items():
                if gid in ('chronology','recent','screening'):actual=state['content_revision']
                else:
                    g=db.execute('SELECT revision FROM groups WHERE contract=? AND gid=?',(contract_id,gid)).fetchone()
                    actual=g[0] if g else None
                if actual!=revision:raise CumulativeError('Stale or unknown claim basis')
            value={'id':claim_id,'text':text,'basis':basis,'generation':expected_generation}
            # Claims are append-only versions, not silently overwritten prose.
            identity=claim_id+':'+digest(value)[:16]
            db.execute('INSERT OR IGNORE INTO claims VALUES(?,?,?,0)',(contract_id,identity,encode(value)))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise


def plan_rebuild(*, path: Path, contract_id: str, target_spec: dict,
                 features: dict[str,list[str]]) -> dict:
    """Classify each requested feature using retained metadata; never fetch sources."""
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            head=db.execute('SELECT account,spec FROM contracts WHERE id=?',(contract_id,)).fetchone()
            if head is None:raise CumulativeError('Unknown source contract')
            previous=json.loads(head['spec']);target=register(db,head['account'],target_spec)
            geometry=any(previous.get(k)!=target_spec.get(k) for k in ('map_version','spatial_parameters'))
            method=any(previous.get(k)!=target_spec.get(k) for k in ('method_hash','grouping_version','signature_parameters'))
            jobs=[]
            for r in db.execute('SELECT mid,revision,inventory FROM matches WHERE contract=? ORDER BY mid',(contract_id,)).fetchall():
                inv=json.loads(r['inventory'])
                for feature,dependencies in features.items():
                    present=inv['metrics'].get(feature,{}).get('eligible',False)
                    available=bool(dependencies) and all(inv['metrics'].get(k,{}).get('eligible',False) for k in dependencies)
                    action='targeted_sources_required' if geometry or method else 'reuse_compact' if present else 'derive_from_compact' if available else 'targeted_sources_required'
                    job={'source_contract':contract_id,'target_contract':target,'match_id':r['mid'],
                         'source_contribution_revision':r['revision'],'feature':feature,'dependencies':dependencies,
                         'action':action,'status':'planned','coverage_complete':False,
                         'reason':'coordinate/method change' if geometry or method else 'retained feature available' if present else 'retained dependencies available' if available else 'required values absent/ineligible'}
                    jid=digest(job)
                    db.execute('INSERT OR IGNORE INTO jobs VALUES(?,?,?)',(target,jid,encode(job)))
                    jobs.append({'id':jid,**job})
            db.execute('COMMIT')
            return {'target_contract':target,'jobs':jobs,'required':len(jobs),'completed':0,
                    'coverage_complete':False,'network_requests':0,'note':'Planning is not materialization. Import validated recalculated contributions, then reconcile jobs.'}
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise


def reconcile_jobs(*, path: Path, contract_id: str) -> dict:
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            jobs=db.execute('SELECT id,payload FROM jobs WHERE contract=?',(contract_id,)).fetchall();complete=0
            for r in jobs:
                job=json.loads(r['payload']);current=db.execute('SELECT revision,inventory FROM matches WHERE contract=? AND mid=?',(contract_id,job['match_id'])).fetchone()
                source=db.execute('SELECT revision FROM matches WHERE contract=? AND mid=?',(job['source_contract'],job['match_id'])).fetchone()
                stale=source is None or source['revision']!=job['source_contribution_revision']
                valid=current is not None and json.loads(current['inventory'])['metrics'].get(job['feature'],{}).get('eligible',False)
                # A planned raw/method rebuild cannot be acknowledged by importing the unchanged contribution.
                if valid and job['action']=='targeted_sources_required' and current['revision']==job['source_contribution_revision']:valid=False
                if stale:valid=False
                job['status']='stale_source_plan' if stale else 'materialized' if valid else 'planned';job['coverage_complete']=valid
                complete+=valid;db.execute('UPDATE jobs SET payload=? WHERE contract=? AND id=?',(encode(job),contract_id,r['id']))
            db.execute('COMMIT');return {'required':len(jobs),'completed':complete,'coverage_complete':bool(jobs) and complete==len(jobs)}
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise


def history(*, path: Path, contract_id: str) -> dict:
    with connect(path,readonly=True) as db:
        db.execute('BEGIN')
        result={'changes':[json.loads(r[0]) for r in db.execute('SELECT payload FROM changes WHERE contract=? ORDER BY generation',(contract_id,))],
                'claims':[{**json.loads(r['payload']),'stale':bool(r['stale'])} for r in db.execute('SELECT payload,stale FROM claims WHERE contract=?',(contract_id,))],
                'jobs':[json.loads(r[0]) for r in db.execute('SELECT payload FROM jobs WHERE contract=?',(contract_id,))]}
        db.execute('COMMIT');return result
