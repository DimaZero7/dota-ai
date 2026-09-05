"""One SQLite transaction publishes contributions, caches, history and review state."""
import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from collections.abc import Iterator

from ..evidence import digest
from .schemas import encode, VERSION, CumulativeError

DDL='''
CREATE TABLE IF NOT EXISTS contracts(id TEXT PRIMARY KEY, account INTEGER NOT NULL, spec TEXT NOT NULL, generation INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS matches(contract TEXT, mid INTEGER, revision TEXT NOT NULL, inventory TEXT NOT NULL, timeline TEXT NOT NULL, PRIMARY KEY(contract,mid));
CREATE TABLE IF NOT EXISTS revisions(contract TEXT, mid INTEGER, revision TEXT, payload TEXT NOT NULL, PRIMARY KEY(contract,mid,revision));
CREATE TABLE IF NOT EXISTS members(contract TEXT, gid TEXT, mid INTEGER, kind TEXT NOT NULL, meta TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(contract,gid,mid));
CREATE INDEX IF NOT EXISTS members_match ON members(contract,mid);
CREATE TABLE IF NOT EXISTS groups(contract TEXT, gid TEXT, kind TEXT NOT NULL, revision TEXT NOT NULL, payload TEXT NOT NULL, recent TEXT, PRIMARY KEY(contract,gid));
CREATE TABLE IF NOT EXISTS states(contract TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS changes(contract TEXT, generation INTEGER, payload TEXT NOT NULL, PRIMARY KEY(contract,generation));
CREATE TABLE IF NOT EXISTS claims(contract TEXT, id TEXT, payload TEXT NOT NULL, stale INTEGER NOT NULL, PRIMARY KEY(contract,id));
CREATE TABLE IF NOT EXISTS jobs(contract TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(contract,id));
CREATE TABLE IF NOT EXISTS sequences(contract TEXT, id TEXT, input_revision TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(contract,id));
'''


@contextmanager
def connect(path: Path, *, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    if not readonly:path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro' if readonly else path,
                       uri=readonly,timeout=30,isolation_level=None)
    try:
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0,1,2):raise CumulativeError('Unsupported database schema')
        if version<2 and not readonly:
            db.executescript(DDL);db.execute('PRAGMA user_version=2')
        if version==0 and readonly:raise CumulativeError('Uninitialized database')
        yield db
    finally:db.close()


def register(db: sqlite3.Connection, account: int, spec: dict) -> str:
    if spec.get('schema')!=VERSION:raise CumulativeError('Unsupported contract')
    key=digest([account,spec]);serialized=encode(spec)
    db.execute('INSERT OR IGNORE INTO contracts(id,account,spec) VALUES(?,?,?)',(key,account,serialized))
    saved=db.execute('SELECT account,spec FROM contracts WHERE id=?',(key,)).fetchone()
    if saved['account']!=account or saved['spec']!=serialized:raise CumulativeError('Contract identity collision')
    return key


def decode_checked(payload: str, revision: str) -> dict:
    data=json.loads(payload)
    if digest(data)!=revision:raise CumulativeError('Stored aggregate integrity failure')
    return data
