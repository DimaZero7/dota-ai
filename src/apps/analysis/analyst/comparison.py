"""Match review with target exclusion, temporal guards and explicit hindsight."""
import json
from pathlib import Path

from ..cumulative.storage import connect
from ..cumulative.schemas import encode
from ..longitudinal.cohorts import _summary
from ..longitudinal.retrieval import short_distribution
from ..numeric.schemas import number
from ..evidence import digest
from .schemas import VERSION, DEFAULT_METRICS, DEFINITIONS, READING_RULES, AnalystError, size, text, bilingual
from .storage import initialize, session, checked
from .retrieval import envelope, identity


def prepare_match(*, path: Path, contract_id: str, match_id: int, question: str,
                  mode: str = 'past_only', previously_seen: bool = True) -> dict:
    text(question,'match question',1000)
    if mode not in ('past_only','retrospective','forecast'):raise AnalystError('Explicit comparison mode required')
    initialize(path)
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE');target=envelope(db,contract_id,match_id)['signature'];context=target['context']
        entries=[];excluded=0
        # One broad whole-match group per match; do not condition a forecast on final duration/rank/side effects.
        selected=None
        for r in db.execute('SELECT gid,meta FROM members WHERE contract=? AND mid=? AND kind=?',(contract_id,match_id,'numeric')):
            meta=json.loads(r['meta'])
            if meta['scope']['kind']=='match' and meta['scope']['grouping']=='hero_position_relaxed':selected=(r['gid'],meta);break
        if selected is None:raise AnalystError('No context-matched whole-match group')
        for r in db.execute('SELECT mid,payload FROM members WHERE contract=? AND gid=? ORDER BY mid',(contract_id,selected[0])):
            item=json.loads(r['payload']);row=item['row']
            if r['mid']==match_id:excluded+=1;continue
            if mode!='retrospective' and (not all(number(v) for v in (row['start_time'],row['duration'],target['start_time'])) or row['start_time']+row['duration']>=target['start_time']):excluded+=1;continue
            entries.append(item)
        summary=_summary(entries) if entries else None
        profile=None
        for r in db.execute('SELECT * FROM analyst_profiles WHERE contract=? ORDER BY rowid DESC',(contract_id,)):
            population=json.loads(r['population']);value=checked(r['payload'],r['revision'])
            if match_id in population:continue
            if mode!='retrospective' and (r['data_end'] is None or not number(target['start_time']) or r['data_end']>=target['start_time']):continue
            matching=[h for h in value['hypotheses'] if all(h['scope'].get(k)==context.get(k) for k in ('hero_id','position')) and h['status']!='rejected']
            if matching:
                profile={'revision':r['revision'],'data_end':r['data_end'],'portrait':value['portrait'],'hypotheses':matching,
                         'meaning':'historical authored version; not silently reinterpreted using later profile text'};break
        baseline={'scope':selected[1]['scope'],'n':len(entries),'excluded':excluded,
                  'metrics':{k:short_distribution(v) for k,v in (summary or {}).get('metrics',{}).items() if k in DEFAULT_METRICS},
                  'matched_by':['hero_id','position','mode','stratz_version','opendota_version'],
                  'uncontrolled':['drafts','side','rank','duration','team decisions'],'comparison_eligible':False,
                  'population_revision':digest([(e['row']['match_id'],e['metrics']) for e in entries]),
                  'target_excluded':True,'future_excluded':mode!='retrospective'}
        visible_target=identity(target)
        if mode=='forecast':
            visible_target={k:visible_target[k] for k in ('match_id','start_time','date_utc')}
            visible_target['context']={k:context.get(k) for k in ('hero_id','position','mode','stratz_version','opendota_version','draft_allies','draft_enemies')}
        else:visible_target['metrics']={k:v for k,v in target['metrics'].items() if k in DEFAULT_METRICS}
        generation=db.execute('SELECT generation FROM contracts WHERE id=?',(contract_id,)).fetchone()[0]
        packet={'version':VERSION,'contract_id':contract_id,'generation':generation,'mode':'match','comparison_mode':mode,
                'question':question,'target':visible_target,'baseline':baseline,'historical_profile':profile,
                'profile_absence_reason':None if profile else 'No independent profile with compatible hero/position and required period',
                'definitions':{k:dict(zip(('unit','formula','reading'),DEFINITIONS[k])) for k in DEFAULT_METRICS},
                'reading_rules':READING_RULES,'metrics':list(DEFAULT_METRICS),
                'memory':{'previously_seen':previously_seen,'blind':False,'isolated':False,'exact_tokens':None},
                'evaluation':'hindsight review' if mode!='forecast' else 'past-only input simulation; no established blind prediction performance',
                'budgets':{'main_bytes':32000,'drill_calls':0 if mode=='forecast' else 4,'drill_total_bytes':12000,'drill_single_bytes':5000,'answer_bytes':12000}}
        packet['session_id']=digest(packet)
        if size(packet)>32000:raise AnalystError('Match packet exceeds budget')
        evidence={'baseline':digest(baseline),'target':digest(visible_target)}
        if profile:evidence['historical_profile']=profile['revision']
        usage={'main_bytes':size(packet),'drill_calls':0,'drill_bytes':0,'cards_read':1,'lower_nodes_read':0,'main_match_cards_read':1,
               'lower_model_answers':0,'reused_lower_answers':0,'answer_bytes':0}
        db.execute('INSERT OR IGNORE INTO analyst_sessions VALUES(?,?,?,?,?,?,0)',(packet['session_id'],contract_id,generation,encode(packet),encode(usage),encode(evidence)))
        db.execute('COMMIT');return packet


def accept_match(*, path: Path, session_id: str, response: dict) -> dict:
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE');packet,usage,evidence=session(db,session_id)
        if packet['mode']!='match' or response.get('author')!='current Codex' or response.get('session_id')!=session_id:raise AnalystError('Explicit matching authored match response required')
        for k in ('assessment','alternative','uncertainty','next_check'):bilingual(response.get(k),k)
        if not response.get('basis') or not set(response['basis'])<=evidence.keys():raise AnalystError('Unknown match-review evidence')
        if size(response)>12000:raise AnalystError('Match answer exceeds budget')
        record={'packet':packet,'response':response,'validation':'authored retrospective explanation; numerical deviation is not proof of an error'}
        revision=digest(record);usage['answer_bytes']=size(response)
        db.execute('INSERT INTO analyst_match_reviews VALUES(?,?,?)',(revision,session_id,encode(record)))
        db.execute('UPDATE analyst_sessions SET usage=?,closed=1 WHERE id=?',(encode(usage),session_id))
        db.execute('COMMIT');return {**record,'revision':revision}
