"""Offline ten-match equivalence and synthetic 1000+10 accumulation benchmark."""
import copy
import json
import time
import tracemalloc
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.test_longitudinal_analysis import row
from src.apps.analysis.cumulative.schemas import contract, contribution, encode
from src.apps.analysis.cumulative.services import apply_batch, snapshot, change_packet
from src.apps.analysis.cumulative.review import history
from src.apps.analysis.cumulative.storage import connect
from src.apps.analysis.longitudinal.schemas import signed
from src.apps.analysis.longitudinal.cohorts import build_cohorts
from src.apps.analysis.numeric.storage import write_json
from src.apps.analysis.evidence import digest
from src.apps.analysis.spatial.aggregation import aggregate_selection, build_match


def sequences(path: Path, key: str) -> dict:
    with connect(path,readonly=True) as db:
        return {r['id']:json.loads(r['payload']) for r in db.execute('SELECT id,payload FROM sequences WHERE contract=?',(key,))}


def run() -> dict:
    index=json.loads((ROOT/'data/analysis/longitudinal/ten/signatures.json').read_text(encoding='utf-8'))
    rows=[json.loads((ROOT/p).read_text(encoding='utf-8')) for p in index['paths']]
    approved=json.loads((ROOT/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    assert len(rows)==10 and {str(r['match_id']) for r in rows}==set(approved['lower_outputs'])
    spatial_index=json.loads((ROOT/'data/prototype/spatial-verification.json').read_text(encoding='utf-8'))
    paths={r['match_id']:r['bundle'] for r in spatial_index['matches']}
    values=[contribution(r,spatial=json.loads((ROOT/paths[r['match_id']]/'L3.json').read_text(encoding='utf-8'))) for r in rows]
    spec=contract(catalog=json.loads((ROOT/'docs/contracts/statistics-catalog.json').read_text(encoding='utf-8')),map_version='native-source-grid-1')
    scratch=ROOT/'.agent/tmp';scratch.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        folder=Path(temp);full=apply_batch(path=folder/'full.sqlite',account_id=203182675,spec=spec,values=values)
        for part in (values[:3],values[3:7],values[7:]):
            batch=apply_batch(path=folder/'batch.sqlite',account_id=203182675,spec=spec,values=part)
        a=snapshot(path=folder/'full.sqlite',contract_id=full['contract_id']);b=snapshot(path=folder/'batch.sqlite',contract_id=batch['contract_id'])
        assert a['groups']==b['groups'] and a['state']['content_revision']==b['state']['content_revision']
        assert sequences(folder/'full.sqlite',full['contract_id'])==sequences(folder/'batch.sqlite',batch['contract_id'])
        cohorts,_=build_cohorts(rows)
        assert all(a['groups'][c['id']]['summary']==c['summary'] for c in cohorts)
        # Stored JSON objects use canonical key order. Equal-exposure cells must not depend on input JSON order.
        canonical_spatial=[json.loads(encode(v['spatial'])) for v in sorted(values,key=lambda v:v['signature']['match_id'])]
        spatial_reference=aggregate_selection([(build_match(p),p) for p in canonical_spatial])
        for g in spatial_reference['groups']:
            actual_group=next(x for x in a['groups'].values() if 'distribution' in x and all(x['scope'].get(k)==v for k,v in g['context'].items()))
            assert actual_group['distribution']==g['distribution'] and actual_group['summary']==g['summary']
        # Publish an actual local store and a small change example; no source/model calls.
        output=ROOT/'data/analysis/cumulative/ten.sqlite'
        actual=apply_batch(path=output,account_id=203182675,spec=spec,values=values)
        published=history(path=output,contract_id=actual['contract_id'])['changes'][-1]
        write_json(ROOT/'data/analysis/cumulative/ten-change.json',change_packet(published))
        synthetic=[]
        for i in range(1010):
            r=row(i,x=i%37,y=i%41,day=i//5,win=i%3!=0)
            r['context']['hero_id']=i%20+1
            # Synthetic phases exercise separate conditional contributions without claiming real play.
            r['phases']=[{'phase':0,'complete_phase':True,'state':'near_even','state_basis':'phase_start','metrics':copy.deepcopy(r['metrics'])}]
            synthetic.append(contribution(signed(r)))
        bench=folder/'scale.sqlite';start=time.perf_counter()
        seed=apply_batch(path=bench,account_id=1,spec=spec,values=synthetic[:1000]);initial_seconds=time.perf_counter()-start
        tracemalloc.start();start=time.perf_counter()
        with patch('src.apps.analysis.sources.load_sources',side_effect=AssertionError('Old sources must not be loaded')),patch.object(Path,'read_text',side_effect=AssertionError('No old signature/event files may be read')),patch.object(Path,'read_bytes',side_effect=AssertionError('No raw file reads')),patch('builtins.open',side_effect=AssertionError('No Python file reads')):
            delta=apply_batch(path=bench,account_id=1,spec=spec,values=synthetic[1000:])
        seconds=time.perf_counter()-start;current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        s=snapshot(path=bench,contract_id=seed['contract_id']);assert s['state']['n']==1010
        assert apply_batch(path=bench,account_id=1,spec=spec,values=synthetic[1000:])['no_op']
        reference=apply_batch(path=folder/'scale-full.sqlite',account_id=1,spec=spec,values=synthetic)
        r=snapshot(path=folder/'scale-full.sqlite',contract_id=reference['contract_id'])
        assert s['groups']==r['groups'] and s['state']['content_revision']==r['state']['content_revision']
        assert sequences(bench,seed['contract_id'])==sequences(folder/'scale-full.sqlite',reference['contract_id'])
        assert delta['work']['sequence_statistics_reused']>0
        old=synthetic[500];fixed=copy.deepcopy(old['signature']);fixed['metrics']['xp_rate']['value']=-7
        replacement=contribution(signed(fixed));corrected=apply_batch(path=bench,account_id=1,spec=spec,values=[replacement],expected_revisions={500:old['revision']})
        expected=synthetic.copy();expected[500]=replacement
        all_corrected=apply_batch(path=folder/'corrected-full.sqlite',account_id=1,spec=spec,values=expected)
        after=snapshot(path=bench,contract_id=seed['contract_id']);expected_state=snapshot(path=folder/'corrected-full.sqlite',contract_id=all_corrected['contract_id'])
        assert after['groups']==expected_state['groups'] and after['state']['content_revision']==expected_state['state']['content_revision']
        assert sequences(bench,seed['contract_id'])==sequences(folder/'corrected-full.sqlite',all_corrected['contract_id'])
        result={'real_matches':10,'new_matches_fetched':0,'meta_applied':False,'real_groups':len(a['groups']),
                'real_spatial_groups':sum(k.startswith('space:') for k in a['groups']),
                'real_full_vs_batches_exact':True,'real_L5_distributions_equal':True,'real_spatial_L5_equal':True,
                'sequence_caches_equal':True,
                'store':output.relative_to(ROOT).as_posix(),'contract_id':actual['contract_id'],
                'synthetic':{'initial':1000,'added':10,'groups':len(s['groups']),'initial_seconds':initial_seconds,
                             'update_seconds_with_tracemalloc':seconds,'update_peak_python_bytes':peak,'database_bytes':bench.stat().st_size,
                             'work':delta['work'],'correction_work':corrected['work'],'packet_bytes':len(encode(change_packet(delta)).encode()),
                             'full_batch_and_correction_exact':True,'duplicate_no_op':True},
                'limits':['Exact quantiles rebuild affected compact groups, not constant-cost sketches.',
                          'Chronology/global series recompute compact timestamps and four metrics; no event history.',
                          'Screening and authored profile await explicit review; no stale p values advertised as current.',
                          'Python allocation peak excludes SQLite native allocations and OS cache.']}
        write_json(ROOT/'data/prototype/cumulative-verification.json',result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        return result


if __name__=='__main__':run()
