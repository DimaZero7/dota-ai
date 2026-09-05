"""Offline staged real review of seven saved matches, then the remaining three."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.apps.analysis.cumulative.schemas import contract, contribution
from src.apps.analysis.cumulative.services import apply_batch
from src.apps.analysis.cumulative.storage import connect
from src.apps.analysis.numeric.storage import write_json
from src.apps.analysis.analyst.services import prepare, read_profile
from src.apps.analysis.analyst.storage import audit, checked
from src.apps.analysis.analyst.comparison import prepare_match
from src.apps.analysis.analyst.schemas import size

OUTPUT=ROOT/'data/analysis/analyst'
DB=OUTPUT/'prototype.sqlite'
QUESTION='Describe personal hero/position patterns, alternatives and testable growth priorities; review deaths together with XP and participation. No meta; this previously seen sample is retrospective.'
METRICS=['xp_rate','gold_rate','death_fraction','participation','repeat_death_fraction','tower_damage_rate','post_combat_xp_change']


def inputs() -> tuple[list[dict],dict]:
    index=json.loads((ROOT/'data/analysis/longitudinal/ten/signatures.json').read_text(encoding='utf-8'))
    signatures=[json.loads((ROOT/p).read_text(encoding='utf-8')) for p in index['paths']]
    approved=json.loads((ROOT/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    assert len(signatures)==10 and {str(r['match_id']) for r in signatures}==set(approved['lower_outputs'])
    spatial=json.loads((ROOT/'data/prototype/spatial-verification.json').read_text(encoding='utf-8'))
    bundles={r['match_id']:r['bundle'] for r in spatial['matches']}
    values=[contribution(r,spatial=json.loads((ROOT/bundles[r['match_id']]/'L3.json').read_text(encoding='utf-8')))
            for r in sorted(signatures,key=lambda r:(r['start_time'],r['match_id']))]
    spec=contract(catalog=json.loads((ROOT/'docs/contracts/statistics-catalog.json').read_text(encoding='utf-8')),
                  map_version='native-source-grid-1',recent_count=3)
    return values,spec


def run(stage: str) -> dict:
    if stage=='historical':
        values,spec=inputs();past_db=OUTPUT/'historical.sqlite'
        delta=apply_batch(path=past_db,account_id=203182675,spec=spec,values=values[:6])
        packet=prepare(path=past_db,contract_id=delta['contract_id'],
                       question='Build a provisional Jakiro-mid profile strictly on this earlier six-game population for a retrospective chronological replay.',
                       metrics=['xp_rate','death_fraction','participation','repeat_death_fraction'],budget=16000)
        write_json(OUTPUT/'historical.json',packet)
        return {'packet':'data/analysis/analyst/historical.json','session_id':packet['session_id'],'n':packet['summary']['n']}
    if stage=='historical-match':
        values,spec=inputs();past_db=OUTPUT/'historical.sqlite'
        current=json.loads((OUTPUT/'historical.json').read_text(encoding='utf-8'))
        read_profile(path=past_db,contract_id=current['contract_id'])
        apply_batch(path=past_db,account_id=203182675,spec=spec,values=[values[6]])
        packet=prepare_match(path=past_db,contract_id=current['contract_id'],match_id=values[6]['signature']['match_id'],
                            question='Review this later Jakiro-mid match against the independent earlier profile; test the re-entry hypothesis without treating differences as causal effects.')
        write_json(OUTPUT/'historical-match.json',packet)
        return {'packet':'data/analysis/analyst/historical-match.json','session_id':packet['session_id'],'baseline_n':packet['baseline']['n']}
    if stage in ('initial','update'):
        values,spec=inputs();part=values[:7] if stage=='initial' else values[7:]
        if stage=='update':
            state=json.loads((OUTPUT/'initial.json').read_text(encoding='utf-8'))
            read_profile(path=DB,contract_id=state['contract_id'])
        delta=apply_batch(path=DB,account_id=203182675,spec=spec,values=part)
        packet=prepare(path=DB,contract_id=delta['contract_id'],question=QUESTION,metrics=METRICS)
        if packet['mode']!=('initial' if stage=='initial' else 'update'):raise ValueError('This stage already advanced; use a new explicit review instead of resetting history')
        write_json(OUTPUT/f'{stage}.json',packet)
        registry=json.loads((ROOT/'data/prototype/numeric-verification.json').read_text(encoding='utf-8'))
        write_json(OUTPUT/'numeric-bundles.json',{str(r['match_id']):r['bundle'] for r in registry['matches']})
        return {'stage':stage,'packet':f'data/analysis/analyst/{stage}.json','session_id':packet['session_id'],'n':packet['summary']['n'],'bytes':size(packet)}
    if stage=='match':
        values,_=inputs();current=json.loads((OUTPUT/'update.json').read_text(encoding='utf-8'))
        target=values[-1]['signature']['match_id']
        packet=prepare_match(path=DB,contract_id=current['contract_id'],match_id=target,
                             question='Compare this match with independent earlier hero/position evidence and the earlier profile; distinguish a deviation from a proven error.',mode='past_only')
        write_json(OUTPUT/'match.json',packet)
        return {'stage':stage,'packet':'data/analysis/analyst/match.json','session_id':packet['session_id'],'baseline_n':packet['baseline']['n']}
    packets={name:json.loads((OUTPUT/f'{name}.json').read_text(encoding='utf-8')) for name in ('initial','update','match')}
    audits={k:audit(path=DB,session_id=p['session_id']) for k,p in packets.items()}
    assert packets['initial']['summary']['n']==7 and packets['update']['summary']['n']==10
    assert all(a['usage']['drill_calls']<=4 and a['usage']['drill_bytes']<=12000 for a in audits.values())
    assert all(size(p)<=32000 for p in packets.values())
    assert all(audits[k]['usage']['main_match_cards_read']==0 for k in ('initial','update'))
    assert packets['match']['baseline']['target_excluded'] and packets['match']['baseline']['future_excluded']
    with connect(DB,readonly=True) as db:
        profiles=[{**checked(r['payload'],r['revision']),'revision':r['revision']} for r in db.execute('SELECT revision,payload FROM analyst_profiles WHERE contract=? ORDER BY rowid',(packets['initial']['contract_id'],))]
        lower=db.execute('SELECT COUNT(*) FROM analyst_lower').fetchone()[0]
        matches=db.execute('SELECT COUNT(*) FROM analyst_match_reviews').fetchone()[0]
    assert len(profiles)>=2 and profiles[-1]['previous_revision']==profiles[-2]['revision']
    assert profiles[-1]['generation']==packets['update']['generation'] and lower>=1 and matches>=1
    historical=json.loads((OUTPUT/'historical-match.json').read_text(encoding='utf-8'))
    assert historical['historical_profile'] is not None and historical['baseline']['n']==3
    with connect(OUTPUT/'historical.sqlite',readonly=True) as db:
        assert db.execute('SELECT COUNT(*) FROM analyst_match_reviews').fetchone()[0]>=1
    historical_packet=json.loads((OUTPUT/'historical.json').read_text(encoding='utf-8'))
    result={'version':'analyst-verification-1','real_matches':10,'new_matches_fetched':0,'meta_applied':False,
            'initial_matches':7,'added_matches':3,'blind':False,'memory_isolated':False,
            'profile_revisions':[p['revision'] for p in profiles],
            'usage':{k:a['usage'] for k,a in audits.items()},'lower_authored_assessments':lower,
            'match_target':packets['match']['target']['match_id'],'independent_baseline_n':packets['match']['baseline']['n'],
            'prior_profile_available':packets['match']['historical_profile'] is not None,
            'historical_example':{'match_id':historical['target']['match_id'],'baseline_n':3,'prior_profile_available':True,
                'profile_usage':audit(path=OUTPUT/'historical.sqlite',session_id=historical_packet['session_id'])['usage'],
                'match_usage':audit(path=OUTPUT/'historical.sqlite',session_id=historical['session_id'])['usage']},
            'limits':['Same Codex conversation had previously seen this material; chronological replay is retrospective.',
                      'Byte limits measure delivered local packets, not exact tokens or isolated model memory.',
                      'Structural validation cannot prove semantic truth, coaching usefulness or causal interpretations.']}
    write_json(ROOT/'data/prototype/analyst-verification.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['initial','update','match','historical','historical-match','verify'])
    print(json.dumps(run(p.parse_args().stage),ensure_ascii=True))
