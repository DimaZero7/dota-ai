"""Append-only authored profiles and persistent review budgets beside cumulative data."""
import json
import sqlite3
from pathlib import Path
from ..cumulative.storage import connect
from ..cumulative.schemas import encode
from ..evidence import digest
from .schemas import AnalystError

DDL='''
CREATE TABLE IF NOT EXISTS analyst_sessions(id TEXT PRIMARY KEY, contract TEXT, generation INTEGER, packet TEXT, usage TEXT, evidence TEXT, closed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS analyst_drills(session TEXT, ordinal INTEGER, payload TEXT, PRIMARY KEY(session,ordinal));
CREATE TABLE IF NOT EXISTS analyst_profiles(revision TEXT PRIMARY KEY, contract TEXT, generation INTEGER, session TEXT UNIQUE, payload TEXT, population TEXT, data_end REAL);
CREATE TABLE IF NOT EXISTS analyst_lower(revision TEXT PRIMARY KEY, input_revision TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS analyst_match_reviews(revision TEXT PRIMARY KEY, session TEXT, payload TEXT);
'''


def initialize(path: Path) -> None:
    with connect(path) as db:db.executescript(DDL)


def checked(payload: str, revision: str) -> dict:
    data=json.loads(payload)
    if digest(data)!=revision:raise AnalystError('Authored storage integrity failure')
    return data


def latest(db: sqlite3.Connection, contract_id: str) -> dict | None:
    r=db.execute('SELECT revision,payload FROM analyst_profiles WHERE contract=? ORDER BY rowid DESC LIMIT 1',(contract_id,)).fetchone()
    return {**checked(r['payload'],r['revision']),'revision':r['revision']} if r else None


def session(db: sqlite3.Connection, session_id: str, *, live: bool = True) -> tuple[dict,dict,dict]:
    row=db.execute('SELECT * FROM analyst_sessions WHERE id=?',(session_id,)).fetchone()
    if row is None:raise AnalystError('Unknown review session')
    packet=json.loads(row['packet'])
    if digest({k:v for k,v in packet.items() if k!='session_id'})!=session_id:raise AnalystError('Review packet integrity failure')
    if live:
        head=db.execute('SELECT generation FROM contracts WHERE id=?',(row['contract'],)).fetchone()
        if row['closed'] or head is None or head[0]!=row['generation']:raise AnalystError('Closed or stale review; prepare a new review')
    return packet,json.loads(row['usage']),json.loads(row['evidence'])


def audit(*, path: Path, session_id: str) -> dict:
    with connect(path,readonly=True) as db:
        packet,usage,evidence=session(db,session_id,live=False)
        return {'session_id':session_id,'usage':usage,'evidence_refs':evidence,
                'drills':[json.loads(r[0]) for r in db.execute('SELECT payload FROM analyst_drills WHERE session=? ORDER BY ordinal',(session_id,))],
                'memory_isolated':False,'measured_model_tokens':None}
