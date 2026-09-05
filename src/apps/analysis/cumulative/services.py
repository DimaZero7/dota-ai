"""Explicit transactional imports; old event files are never consulted."""
import json
import sqlite3
from pathlib import Path
from typing import Callable

from ..evidence import digest
from ..numeric.schemas import number
from ..longitudinal.sessions import chronology, sensitivity
from ..longitudinal.cohorts import composition
from .schemas import CumulativeError, encode, inventory, validate_contribution, runtime_method_hash
from .storage import connect, register, decode_checked
from .groups import contributions, aggregate, recent_view
from .sequences import update_sequences


def _timeline(row: dict) -> dict:
    return {**{k:row[k] for k in ('match_id','start_time','duration','win','context')},
            'metrics':{k:v for k,v in row['metrics'].items() if k in ('xp_rate','gold_rate','death_fraction','participation')}}


def _recent(rows: list[dict], count: int) -> set[int]:
    ordered=sorted((r for r in rows if number(r['start_time'])),key=lambda r:(r['start_time'],r['match_id']))
    return {r['match_id'] for r in ordered[-count:]}


def _brief(group: dict | None) -> dict | None:
    if group is None:return None
    s=group['summary']
    return {'n':s.get('n',s.get('match_count')),'wins':s.get('wins'),
            'metrics':{k:{a:m[a] for a in ('n','coverage','mean','median','pooled_value')} for k,m in s.get('metrics',{}).items()},
            'observed_seconds':s.get('observed_outside_death_seconds')}


def _edges(state: dict) -> dict:
    items=(state.get('chronology') or {}).get('items',[])
    return {str(b['match_id']):[a['match_id'],b['gap_seconds'],b['boundary_reason']]
            for a,b in zip(items,items[1:])}


def _components(state: dict) -> dict:
    c=state.get('chronology',{})
    return {f'{kind}:{r["match_ids"][0]}':digest(r) for kind in ('sessions','runs') for r in c.get(kind,[])}


def apply_batch(*, path: Path, account_id: int, spec: dict, values: list[dict],
                remove: list[int] | None = None, expected_generation: int | None = None,
                expected_revisions: dict[int,str] | None = None,
                known_gaps: set[tuple[int,int]] | None = None,
                failpoint: Callable[[str],None] | None = None) -> dict:
    """All writes publish together. Corrections require optimistic per-match revisions."""
    remove=remove or [];expected_revisions=expected_revisions or {}
    if spec['method_hash']!=runtime_method_hash() or spec['grouping_version']!='longitudinal-strict-relaxed-1':
        raise CumulativeError('Runtime and calculation contract differ')
    ids=[v['signature']['match_id'] for v in values]
    if len(ids)!=len(set(ids)) or len(remove)!=len(set(remove)) or set(ids)&set(remove):raise CumulativeError('Duplicate/conflicting batch IDs')
    for value in values:validate_contribution(value,account_id,spec)
    checkpoint=failpoint or (lambda _:None)
    work={'raw_source_reads':0,'old_full_signatures_read':0,'member_rows_read':0,'member_bytes_read':0,'groups_rebuilt':0,'timeline_rows_read':0}
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            key=register(db,account_id,spec)
            generation=db.execute('SELECT generation FROM contracts WHERE id=?',(key,)).fetchone()[0]
            if expected_generation is not None and expected_generation!=generation:raise CumulativeError('Stale generation')
            records=[];touched=set();events=[];inventory_changes=[]
            for mid,value in [(v['signature']['match_id'],v) for v in values]+[(mid,None) for mid in remove]:
                old=db.execute('SELECT revision,inventory FROM matches WHERE contract=? AND mid=?',(key,mid)).fetchone()
                if value is not None and old and old['revision']==value['revision']:continue
                if old is None and value is None:continue
                retired=old is None and db.execute('SELECT 1 FROM revisions WHERE contract=? AND mid=? LIMIT 1',(key,mid)).fetchone() is not None
                if retired and expected_revisions.get(mid)!='removed':raise CumulativeError(f'Explicit restoration of removed match required: {mid}')
                if old and expected_revisions.get(mid)!=old['revision']:raise CumulativeError(f'Expected current contribution revision required for replacement/removal: {mid}')
                before=json.loads(old['inventory']) if old else None;after=inventory(value) if value else None
                inventory_changes.append((before,after))
                action='removed' if value is None else 'restored_match' if retired else 'new_match' if old is None else 'source_revision' if before['source_revision']!=after['source_revision'] else 'calculation_or_spatial_revision'
                events.append({'match_id':mid,'action':action,'old_revision':old['revision'] if old else None,
                               'new_revision':value['revision'] if value else None,
                               'newly_eligible':sorted(k for k,v in (after or {}).get('metrics',{}).items() if v['eligible'] and not (before or {}).get('metrics',{}).get(k,{}).get('eligible',False))})
                touched.update(r[0] for r in db.execute('SELECT gid FROM members WHERE contract=? AND mid=?',(key,mid)))
                records.append((mid,value))
            saved=db.execute('SELECT payload FROM states WHERE contract=?',(key,)).fetchone()
            old_state=json.loads(saved[0]) if saved else {}
            coverage=json.loads(encode(old_state.get('coverage',{'spatial_matches':0,'metrics':{}})))
            for before,after in inventory_changes:
                for inv,sign in ((before,-1),(after,1)):
                    if inv is None:continue
                    coverage['spatial_matches']+=sign*inv['spatial']
                    for metric,m in inv['metrics'].items():
                        counts=coverage['metrics'].setdefault(metric,{'present':0,'eligible':0})
                        counts['present']+=sign;counts['eligible']+=sign*m['eligible']
            coverage['metrics']={k:v for k,v in coverage['metrics'].items() if v['present']>0}
            gaps=known_gaps if known_gaps is not None else {tuple(p) for p in old_state.get('known_gaps',[])}
            if not records and sorted(gaps)==sorted(tuple(p) for p in old_state.get('known_gaps',[])):
                db.execute('COMMIT')
                return {'contract_id':key,'generation':generation,'no_op':True,'work':work}
            old_times=[json.loads(r[0]) for r in db.execute('SELECT timeline FROM matches WHERE contract=? ORDER BY mid',(key,))]
            work['timeline_rows_read']=len(old_times);old_recent=_recent(old_times,spec['recent_count'])
            for mid,value in records:
                db.execute('DELETE FROM members WHERE contract=? AND mid=?',(key,mid))
                db.execute('DELETE FROM matches WHERE contract=? AND mid=?',(key,mid))
                if value is None:continue
                row=value['signature'];payload=encode(value)
                db.execute('INSERT OR IGNORE INTO revisions VALUES(?,?,?,?)',(key,mid,value['revision'],payload))
                stored=db.execute('SELECT payload FROM revisions WHERE contract=? AND mid=? AND revision=?',(key,mid,value['revision'])).fetchone()[0]
                if stored!=payload:raise CumulativeError('Historical contribution integrity conflict')
                db.execute('INSERT INTO matches VALUES(?,?,?,?,?)',(key,mid,value['revision'],encode(inventory(value)),encode(_timeline(row))))
                for gid,kind,meta,entry in contributions(value,key):
                    touched.add(gid)
                    db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)',(key,gid,mid,kind,encode(meta),encode(entry)))
            checkpoint('after_contributions')
            times=[json.loads(r[0]) for r in db.execute('SELECT timeline FROM matches WHERE contract=? ORDER BY mid',(key,))]
            recent_ids=_recent(times,spec['recent_count']);window_changed=old_recent^recent_ids
            window_groups=set()
            for mid in window_changed:
                for r in db.execute('SELECT gid,meta FROM members WHERE contract=? AND mid=? AND kind=?',(key,mid,'numeric')):
                    meta=json.loads(r['meta'])
                    if meta['scope']['kind']=='match' and meta['comparison_eligible']:window_groups.add(r['gid'])
            deltas=[];invalidated=set()
            for gid in sorted(touched|window_groups):
                cached=db.execute('SELECT * FROM groups WHERE contract=? AND gid=?',(key,gid)).fetchone()
                before=decode_checked(cached['payload'],cached['revision']) if cached else None
                entries=[];meta=None;kind=None
                for r in db.execute('SELECT kind,meta,payload FROM members WHERE contract=? AND gid=? ORDER BY mid',(key,gid)):
                    work['member_rows_read']+=1;work['member_bytes_read']+=len(r['payload'].encode())
                    kind=r['kind'];meta=json.loads(r['meta']);entries.append(json.loads(r['payload']))
                after=(aggregate(kind,meta,entries) if entries else None) if gid in touched else before
                if gid in touched:work['groups_rebuilt']+=1
                recent=recent_view(meta,entries,recent_ids) if entries and kind=='numeric' else None
                revision=digest(after) if after is not None else None
                old_recent_view=json.loads(cached['recent']) if cached and cached['recent'] else None
                if after is None:db.execute('DELETE FROM groups WHERE contract=? AND gid=?',(key,gid))
                else:db.execute('INSERT OR REPLACE INTO groups VALUES(?,?,?,?,?,?)',(key,gid,kind,revision,encode(after),encode(recent) if recent else None))
                if before!=after or old_recent_view!=recent:
                    invalidated.add(gid)
                    deltas.append({'group_ref':gid,'kind':kind or cached['kind'],'old_revision':cached['revision'] if cached else None,
                                   'new_revision':revision,'before':_brief(before),'after':_brief(after),
                                   'recent_changed':old_recent_view!=recent})
            checkpoint('after_groups')
            current=chronology(times,known_gaps=gaps)
            sequences=update_sequences(db,key,times,current)
            work.update(sequence_statistics_rebuilt=sequences['rebuilt'],sequence_statistics_reused=sequences['reused'],sequence_statistics_removed=sequences['removed'])
            recent_rows=[r for r in times if r['match_id'] in recent_ids];history_rows=[r for r in times if r['match_id'] not in recent_ids]
            state={'n':len(times),'wins':sum(r['win'] is True for r in times),'losses':sum(r['win'] is False for r in times),
                   'coverage':coverage,
                   'sequence_refs':sequences['refs'],
                   'composition':composition(times),'chronology':current,'sensitivity':sensitivity(times,known_gaps=gaps),
                   'known_gaps':sorted(gaps),'recent_ids':sorted(recent_ids),
                   'recent_composition':composition(recent_rows),'history_composition':composition(history_rows),
                   'profile_status':'pending_analyst_review','screening_status':'stale; temporal split and multiple-comparison family require explicit refresh'}
            before_edges=_edges(old_state);after_edges=_edges(state)
            before_components=_components(old_state);after_components=_components(state)
            work['timeline_edges_changed']=sum(before_edges.get(k)!=after_edges.get(k) for k in set(before_edges)|set(after_edges))
            work['sequence_components_changed']=sum(before_components.get(k)!=after_components.get(k) for k in set(before_components)|set(after_components))
            work['timeline_rows_recomputed']=len(times)
            stale_claims=[]
            for claim in db.execute('SELECT id,payload FROM claims WHERE contract=?',(key,)).fetchall():
                refs=json.loads(claim['payload'])['basis']
                if any(gid in invalidated or gid in ('chronology','recent','screening') for gid in refs):
                    db.execute('UPDATE claims SET stale=1 WHERE contract=? AND id=?',(key,claim['id']));stale_claims.append(claim['id'])
            versions={r['gid']:r['revision'] for r in db.execute('SELECT gid,revision FROM groups WHERE contract=? ORDER BY gid',(key,))}
            state['content_revision']=digest({'state':state,'groups':versions})
            generation+=1
            change={'contract_id':key,'generation':generation,'no_op':False,'changes':events,'groups':deltas,
                    'window_entered':sorted(recent_ids-old_recent),'window_exited':sorted(old_recent-recent_ids),
                    'stale_claims':stale_claims,'profile_status':'pending_analyst_review','screening_status':state['screening_status'],
                    'content_revision':state['content_revision'],'work':work}
            db.execute('INSERT OR REPLACE INTO states VALUES(?,?)',(key,encode(state)))
            db.execute('INSERT INTO changes VALUES(?,?,?)',(key,generation,encode(change)))
            db.execute('UPDATE contracts SET generation=? WHERE id=?',(generation,key))
            checkpoint('before_commit');db.execute('COMMIT')
            return change
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise


def snapshot(*, path: Path, contract_id: str) -> dict:
    """A consistent read snapshot; full grids are kept outside the analyst packet."""
    with connect(path,readonly=True) as db:
        db.execute('BEGIN')
        head=db.execute('SELECT * FROM contracts WHERE id=?',(contract_id,)).fetchone()
        if head is None:raise CumulativeError('Unknown contract')
        state=db.execute('SELECT payload FROM states WHERE contract=?',(contract_id,)).fetchone()
        groups={};recent={}
        for r in db.execute('SELECT * FROM groups WHERE contract=? ORDER BY gid',(contract_id,)):
            groups[r['gid']]=decode_checked(r['payload'],r['revision'])
            if r['recent']:recent[r['gid']]=json.loads(r['recent'])
        data={'contract_id':contract_id,'generation':head['generation'],'spec':json.loads(head['spec']),
              'state':json.loads(state[0]) if state else {},'groups':groups,'recent':recent,
              'matches':{r['mid']:r['revision'] for r in db.execute('SELECT mid,revision FROM matches WHERE contract=?',(contract_id,))}}
        db.execute('COMMIT');return data


def change_packet(change: dict, *, budget: int = 32000) -> dict:
    if not 2000<=budget<=32000:raise CumulativeError('Delta budget must be 2000..32000 bytes')
    data={k:v for k,v in change.items() if k not in ('groups','changes','stale_claims','window_entered','window_exited')}
    data.update(groups=[],changed_matches=len(change.get('changes',[])),stale_claim_count=len(change.get('stale_claims',[])),
                window_entered_count=len(change.get('window_entered',[])),window_exited_count=len(change.get('window_exited',[])),
                omitted_groups=len(change.get('groups',[])),detail_ref=f"changes:{change['contract_id']}:{change['generation']}")
    for g in change.get('groups',[]):
        data['groups'].append(g);data['omitted_groups']-=1
        if len(encode(data).encode())>budget:data['groups'].pop();data['omitted_groups']+=1;break
    if len(encode(data).encode())>budget:raise CumulativeError('Mandatory delta exceeds budget')
    return data
