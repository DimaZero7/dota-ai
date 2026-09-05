"""Reuse unchanged session/run statistics; rescan only compact boundary metadata."""
import sqlite3

from ..evidence import digest
from ..longitudinal.statistics import distribution
from .schemas import encode


def update_sequences(db: sqlite3.Connection, contract_id: str, rows: list[dict], chronology: dict) -> dict:
    by_id={r['match_id']:r for r in rows};fingerprints={mid:digest(r) for mid,r in by_id.items()}
    existing={r['id']:r['input_revision'] for r in db.execute('SELECT id,input_revision FROM sequences WHERE contract=?',(contract_id,))}
    current={};rebuilt=0
    for kind in ('sessions','runs'):
        for component in chronology[kind]:
            ids=component['match_ids'];key=f'{kind}:{ids[0]}'
            revision=digest([component,[fingerprints[mid] for mid in ids],chronology['gap_minutes'],chronology['rule_version']])
            current[key]=revision
            if existing.get(key)==revision:continue
            subset=[by_id[mid] for mid in ids]
            result={'id':key,'kind':kind,'input_revision':revision,'match_ids':ids,'n':len(ids),
                    'wins':sum(r['win'] is True for r in subset),'losses':sum(r['win'] is False for r in subset),
                    'metrics':{k:distribution([r['metrics'].get(k) for r in subset]) for k in ('xp_rate','gold_rate','death_fraction','participation')},
                    'interpretation':'mixed-context description of an estimated sequence, not a session effect'}
            db.execute('INSERT OR REPLACE INTO sequences VALUES(?,?,?,?)',(contract_id,key,revision,encode(result)));rebuilt+=1
    removed=set(existing)-set(current)
    for key in removed:db.execute('DELETE FROM sequences WHERE contract=? AND id=?',(contract_id,key))
    return {'refs':current,'rebuilt':rebuilt,'reused':len(current)-rebuilt,'removed':len(removed)}
