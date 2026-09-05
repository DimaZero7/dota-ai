"""Prepare bounded L5 inputs and publish explicitly authored L6 revisions."""
import json
from pathlib import Path

from ..cumulative.storage import connect, decode_checked
from ..cumulative.schemas import encode
from ..evidence import digest
from ..longitudinal.retrieval import cohort_view
from .schemas import VERSION, DEFAULT_METRICS, DEFINITIONS, READING_RULES, AnalystError, size, text, response_shape
from .storage import initialize, latest, session, checked


def group_view(group: dict, recent: dict | None, metrics: list[str]) -> dict:
    if 'distribution' in group:
        return {'id':group['scope'],'kind':'spatial','summary':group['summary'],
                'limitation':'native grid; use task 6 map underlay for spatial interpretation, not coordinates alone'}
    view=cohort_view(group)
    view['metrics']={k:cohort_view(group,k)['metrics'][k] for k in metrics if k in group['summary']['metrics']}
    view['reading_flags']=[]
    for k in view['metrics']:
        c=group['summary']['outcome_comparisons'][k]
        view['metrics'][k]['wins_pooled']=c['wins']['pooled_value'];view['metrics'][k]['losses_pooled']=c['losses']['pooled_value']
        a=c['mean_win_minus_loss'];b=c['pooled_win_minus_loss']
        if a is not None and b is not None and a*b<0:view['reading_flags'].append(f'{k}: outcome contrast sign depends on equal-match vs pooled weighting')
    if any(not v['enough_each_outcome'] for v in view['metrics'].values()):view['reading_flags'].append('Outcome contrasts with an arm below five are descriptive only; see per-metric wins_n/losses_n.')
    view['recent']={**{k:v for k,v in recent.items() if k!='metrics'},'metrics':{k:v for k,v in recent['metrics'].items() if k in metrics}} if recent else None
    view['joint']={k:{field:v[field] for field in ('n','pearson','spearman','missing_pairs','causal')}
                   for k,v in group.get('joint',{}).items() if v['pearson'] is not None and all(x in metrics or x=='win' for x in k.split('×'))}
    return view


def evidence_revision(group: dict, recent: dict | None) -> str:
    return digest({'group':group,'recent':recent})


def prepare(*, path: Path, contract_id: str, question: str, metrics: list[str] | None = None,
            budget: int = 32000, previously_seen: bool = True) -> dict:
    text(question,'question',1000)
    metrics=list(dict.fromkeys(metrics or DEFAULT_METRICS))
    if not metrics or not set(metrics)<=DEFINITIONS.keys():raise AnalystError('Request metrics with declared reading definitions')
    if not 8000<=budget<=32000:raise AnalystError('Main packet budget must be 8000..32000 bytes')
    initialize(path)
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        head=db.execute('SELECT * FROM contracts WHERE id=?',(contract_id,)).fetchone()
        saved=db.execute('SELECT payload FROM states WHERE contract=?',(contract_id,)).fetchone()
        if not head or not saved:raise AnalystError('Populated cumulative contract required')
        state=json.loads(saved[0]);previous=latest(db,contract_id);spec=json.loads(head['spec'])
        prev_compact={k:previous[k] for k in ('revision','portrait','hypotheses','priorities','generation')} if previous else None
        changes=db.execute('SELECT generation,payload FROM changes WHERE contract=? AND generation>? ORDER BY generation',
                           (contract_id,previous['generation'] if previous else head['generation'])).fetchall()
        changed_groups=set();actions={};stale=[];numerical_changes={}
        for r in changes:
            d=json.loads(r['payload']);changed_groups.update(g['group_ref'] for g in d['groups'])
            for g in d['groups']:
                first=numerical_changes.get(g['group_ref'],{})
                numerical_changes[g['group_ref']]={'before':first.get('before',g['before']),'after':g['after']}
            for v in d['changes']:actions[v['action']]=actions.get(v['action'],0)+1
        cited={ref for h in (previous or {}).get('hypotheses',[]) for ref in h['support']+h['counterevidence']}
        previous_evidence={k:v for k,v in (previous or {}).get('evidence',{}).items() if k in cited}
        groups=[];refs={}
        for r in db.execute('SELECT * FROM groups WHERE contract=? ORDER BY gid',(contract_id,)):
            g=decode_checked(r['payload'],r['revision']);recent=json.loads(r['recent']) if r['recent'] else None
            ref='group:'+r['gid'];revision=evidence_revision(g,recent);refs[ref]=revision
            if ref in previous_evidence and previous_evidence[ref]!=revision:stale.append(ref)
            if r['kind']=='numeric':groups.append((r['gid'],g,recent,revision))
        stale+=sorted(k for k in previous_evidence if k.startswith('group:') and k not in refs)
        composition={}
        for k,counts in state['composition'].items():
            ranked=sorted(counts.items(),key=lambda x:(-x[1],x[0]));composition[k]={'counts':dict(ranked[:12]),'omitted_observations':sum(v for _,v in ranked[12:])}
        summary=state['chronology']['summary']
        packet={'version':VERSION,'contract_id':contract_id,'generation':head['generation'],'content_revision':state['content_revision'],
                'mode':'update' if previous else 'initial','question':question,'metrics':metrics,
                'previous_profile':prev_compact,'summary':{'n':state['n'],'wins':state['wins'],'losses':state['losses'],
                    'composition':composition,'coverage':{k:v for k,v in state['coverage']['metrics'].items() if k in metrics},
                    'spatial_matches':state['coverage']['spatial_matches'],
                    'sessions':{k:summary[k] for k in ('estimated_sessions','max_observed_win_run','max_observed_loss_run','history_complete')}},
                'changes':{'since_generation':previous['generation'] if previous else None,'operations':actions,
                    'affected_groups':len(changed_groups),'stale_previous_evidence':stale,
                    'meaning':'operations may revise the same match; counts are not independent observations'},
                'definitions':{k:dict(zip(('unit','formula','reading'),DEFINITIONS[k])) for k in metrics},
                'reading_rules':READING_RULES,'screening_status':state['screening_status'],
                'groups':[],'omitted_groups':len(groups),'selection':'prior cited and changed groups; whole-match hero/position descriptions; largest eligible groups; question metrics only',
                'budgets':{'main_bytes':budget,'drill_calls':4,'drill_total_bytes':12000,'drill_single_bytes':5000,'answer_bytes':24000},
                'memory':{'previously_seen':previously_seen,'blind':False,'isolated':False,'exact_tokens':None},
                'instructions':'Current Codex authors L6. Review alternatives and counterexamples. Retain wording if meaning is unchanged. Hypotheses need hero/position scope, test criteria, versioned group support and uncertainty. Do not interpret every match.'}
        ordering=sorted(groups,key=lambda x:(('group:'+x[0]) not in previous_evidence,x[0] not in changed_groups,
                        x[1]['scope']['kind']!='match',x[1]['scope']['grouping']=='strict',-x[1]['summary']['n'],x[0]))
        evidence={}
        for gid,g,recent,revision in ordering:
            if not any(g['summary']['metrics'].get(k,{}).get('n',0)>0 for k in metrics):continue
            item={'ref':'group:'+gid,'revision':revision,'data':group_view(g,recent,metrics)}
            if gid in numerical_changes:
                item['change']={arm:None if value is None else {**{k:v for k,v in value.items() if k!='metrics'},
                    'metrics':{k:v for k,v in value.get('metrics',{}).items() if k in metrics}}
                    for arm,value in numerical_changes[gid].items()}
            packet['groups'].append(item);packet['omitted_groups']-=1
            if size(packet)>budget-160:packet['groups'].pop();packet['omitted_groups']+=1;continue
            evidence[item['ref']]=revision
        packet['session_id']=digest(packet)
        if size(packet)>budget or not packet['groups']:raise AnalystError('Mandatory context exceeds budget; narrow question/metrics')
        usage={'main_bytes':size(packet),'drill_calls':0,'drill_bytes':0,'cards_read':0,'lower_nodes_read':0,
               'group_aggregates_read':len(groups),'main_match_cards_read':0,'lower_model_answers':0,'reused_lower_answers':0,'answer_bytes':0}
        db.execute('INSERT OR IGNORE INTO analyst_sessions VALUES(?,?,?,?,?,?,0)',
                   (packet['session_id'],contract_id,head['generation'],encode(packet),encode(usage),encode(evidence)))
        db.execute('COMMIT');return packet


def accept_profile(*, path: Path, session_id: str, response: dict) -> dict:
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT revision,payload FROM analyst_profiles WHERE session=?',(session_id,)).fetchone()
        if existing:
            saved=checked(existing['payload'],existing['revision'])
            if saved['response']!=response:raise AnalystError('Session already published with a different response')
            db.execute('COMMIT');return {**saved,'revision':existing['revision']}
        packet,usage,evidence=session(db,session_id)
        if response.get('session_id')!=session_id:raise AnalystError('Response belongs to a different review')
        previous=latest(db,packet['contract_id'])
        if (previous or {}).get('revision')!=(packet['previous_profile'] or {}).get('revision'):raise AnalystError('Another profile was published; prepare against its version')
        response_shape(response,previous,evidence)
        for h in response['hypotheses']:
            group_refs=[r for r in h['support'] if r.startswith('group:')]
            if not group_refs:raise AnalystError('L6 support needs a numerical group, not only lower anecdotes')
            for ref in group_refs:
                r=db.execute('SELECT payload FROM groups WHERE contract=? AND gid=?',(packet['contract_id'],ref[6:])).fetchone()
                scope=json.loads(r[0])['scope']
                if any(h['scope'].get(k)!=scope.get(k) for k in ('hero_id','position')):raise AnalystError('Claim scope differs from supporting group')
        population=[];ends=[]
        for r in db.execute('SELECT mid,timeline FROM matches WHERE contract=?',(packet['contract_id'],)):
            population.append(r['mid']);t=json.loads(r['timeline'])
            if isinstance(t['start_time'],(int,float)) and isinstance(t['duration'],(int,float)):ends.append(t['start_time']+t['duration'])
        data_end=max(ends) if len(ends)==len(population) and ends else None
        authored={k:response[k] for k in ('portrait','hypotheses','priorities','limitations','change_reason','wording')}
        cited={ref for h in response['hypotheses'] for ref in h['support']+h['counterevidence']}
        profile={**authored,'version':VERSION,'generation':packet['generation'],'contract_id':packet['contract_id'],
                 'session_id':session_id,'previous_revision':(previous or {}).get('revision'),'evidence':{k:v for k,v in evidence.items() if k in cited},
                 'data_end':data_end,'population_count':len(population),'response':response,
                 'validation':'structure, provenance and version checks only; semantic validity reviewed by the analyst',
                 'memory':packet['memory']}
        revision=digest(profile);usage['answer_bytes']=size(response)
        db.execute('INSERT INTO analyst_profiles VALUES(?,?,?,?,?,?,?)',(revision,packet['contract_id'],packet['generation'],session_id,encode(profile),encode(sorted(population)),data_end))
        db.execute('UPDATE analyst_sessions SET usage=?,closed=1 WHERE id=?',(encode(usage),session_id))
        db.execute('COMMIT');return {**profile,'revision':revision}


def read_profile(*, path: Path, contract_id: str, revision: str | None = None) -> dict:
    with connect(path,readonly=True) as db:
        db.execute('BEGIN')
        r=db.execute('SELECT revision,payload FROM analyst_profiles WHERE contract=? AND revision=?',(contract_id,revision)).fetchone() if revision else None
        value={**checked(r['payload'],r['revision']),'revision':r['revision']} if r else latest(db,contract_id) if revision is None else None
        if value is None:raise AnalystError('Unknown profile')
        head=db.execute('SELECT generation FROM contracts WHERE id=?',(contract_id,)).fetchone()[0]
        result={**value,'freshness':'current' if head==value['generation'] else 'pending_analyst_review'}
        db.execute('COMMIT');return result
