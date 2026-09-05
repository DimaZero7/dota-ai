"""Transactional, exact and bounded cumulative analysis on synthetic observations."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.test_longitudinal_analysis import row
from src.apps.analysis.cumulative.schemas import contract, contribution, CumulativeError
from src.apps.analysis.cumulative.services import apply_batch, snapshot, change_packet
from src.apps.analysis.cumulative.review import save_claim, plan_rebuild, reconcile_jobs, history
from src.apps.analysis.cumulative.storage import connect
from src.apps.analysis.longitudinal.schemas import signed, measure
from src.apps.analysis.longitudinal.cohorts import build_cohorts, recent_comparison
from src.apps.analysis.longitudinal.sessions import chronology
from src.apps.analysis.evidence import digest


class CumulativeTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.root=Path(self.temp.name);self.db=self.root/'store.sqlite'
        self.spec=contract(catalog={'test':1},map_version='native-1',recent_count=3)

    def tearDown(self):self.temp.cleanup()

    def put(self, rows, **kw):
        return apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(r) for r in rows],**kw)

    def test_full_and_chunked_equal_to_L5(self):
        rows=[row(i,win=i%3!=0) for i in range(12)]
        change=self.put(rows[:4]);self.put(rows[4:8]);self.put(rows[8:])
        state=snapshot(path=self.db,contract_id=change['contract_id']);groups,members=build_cohorts(rows)
        for c in groups:self.assertEqual(state['groups'][c['id']]['summary'],c['summary'])
        self.assertEqual(state['state']['chronology'],chronology(rows))
        self.assertEqual(list(state['recent'].values()),recent_comparison(rows,groups,members,recent_count=3)['matched_groups'])
        full=apply_batch(path=self.root/'full.sqlite',account_id=1,spec=self.spec,values=[contribution(r) for r in rows])
        other=snapshot(path=self.root/'full.sqlite',contract_id=full['contract_id'])
        self.assertEqual(state['groups'],other['groups']);self.assertEqual(state['state']['content_revision'],other['state']['content_revision'])

    def test_duplicate_is_zero_work_and_batch_duplicate_rejected(self):
        c=self.put([row(1)]);again=self.put([row(1)])
        self.assertTrue(again['no_op']);self.assertEqual(again['generation'],c['generation']);self.assertEqual(again['work']['timeline_rows_read'],0)
        with self.assertRaises(CumulativeError):self.put([row(2),row(2)])

    def test_replacement_corrects_quantiles_extremes_and_membership(self):
        rows=[row(i) for i in range(5)];c=self.put(rows)
        corrected=copy.deepcopy(rows[-1]);corrected['metrics']['xp_rate']['value']=-99;corrected['context']['position']='POSITION_5';corrected=signed(corrected)
        with self.assertRaises(CumulativeError):self.put([corrected])
        delta=self.put([corrected],expected_revisions={4:contribution(rows[-1])['revision']})
        groups,_=build_cohorts(rows[:-1]+[corrected]);s=snapshot(path=self.db,contract_id=c['contract_id'])
        self.assertEqual({g['id']:g['summary'] for g in groups},{k:g['summary'] for k,g in s['groups'].items()})
        self.assertEqual(delta['changes'][0]['action'],'calculation_or_spatial_revision')
        with self.assertRaises(CumulativeError):self.put([rows[-1]],expected_revisions={4:contribution(rows[-1])['revision']})

    def test_missing_improves_without_zero_observation(self):
        old=row(1);old['metrics']['xp_rate']=measure(None,unit='XP/min');old=signed(old);c=self.put([old,row(2)])
        group=next(iter(snapshot(path=self.db,contract_id=c['contract_id'])['groups'].values()))
        self.assertEqual(group['summary']['metrics']['xp_rate']['n'],1)
        new=row(1);new['source_manifest_ref']='source-more-complete';new=signed(new)
        delta=self.put([new],expected_revisions={1:contribution(old)['revision']})
        self.assertEqual(delta['changes'][0]['action'],'source_revision');self.assertIn('xp_rate',delta['changes'][0]['newly_eligible'])

    def test_late_game_relinks_sessions_and_recent_eviction(self):
        a=row(1);b=row(2);c=row(3)
        b['start_time']=a['start_time']+4000;c['start_time']=a['start_time']+8000
        a,b,c=map(signed,(a,b,c));first=self.put([a,c]);delta=self.put([b])
        s=snapshot(path=self.db,contract_id=first['contract_id'])
        self.assertEqual(s['state']['chronology'],chronology([a,b,c]));self.assertGreater(delta['work']['timeline_edges_changed'],0)
        delta=self.put([row(9)]);self.assertEqual(delta['window_exited'],[1]);self.assertEqual(delta['window_entered'],[9])

    def test_removed_match_recalculates_only_affected_groups(self):
        a=row(1);b=row(2);b['context']['hero_id']=8;b=signed(b);first=self.put([a,b])
        s=snapshot(path=self.db,contract_id=first['contract_id']);retained={k:g for k,g in s['groups'].items() if g['scope']['hero_id']==8}
        delta=self.put([],remove=[1],expected_revisions={1:contribution(a)['revision']})
        s=snapshot(path=self.db,contract_id=first['contract_id']);self.assertEqual(s['groups'],retained)
        self.assertEqual(delta['work']['member_rows_read'],0)
        with self.assertRaises(CumulativeError):self.put([a])
        self.assertEqual(self.put([a],expected_revisions={1:'removed'})['changes'][0]['action'],'restored_match')

    def test_rollback_all_stages_and_retry_once(self):
        first=self.put([row(1)]);before=snapshot(path=self.db,contract_id=first['contract_id'])
        for stage in ('after_contributions','after_groups','before_commit'):
            def fail(name):
                if name==stage:raise RuntimeError('injected')
            with self.assertRaises(RuntimeError):self.put([row(2)],failpoint=fail)
            self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id']),before)
        self.put([row(2)]);self.assertTrue(self.put([row(2)])['no_op'])

    def test_reader_never_sees_uncommitted_mixed_state(self):
        first=self.put([row(1)]);observed=[]
        def inspect(stage):
            if stage=='after_groups':observed.append(snapshot(path=self.db,contract_id=first['contract_id'])['state']['n'])
        self.put([row(2)],failpoint=inspect)
        self.assertEqual(observed,[1]);self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id'])['state']['n'],2)

    def test_process_exit_mid_transaction_recovers(self):
        first=self.put([row(1)]);before=snapshot(path=self.db,contract_id=first['contract_id'])
        spec=self.root/'spec.json';spec.write_text(json.dumps(self.spec),encoding='utf-8')
        script=self.root/'crash.py'
        script.write_text("import json,os,sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.cwd()))\nfrom tools.test_longitudinal_analysis import row\nfrom src.apps.analysis.cumulative.schemas import contribution\nfrom src.apps.analysis.cumulative.services import apply_batch\napply_batch(path=Path(sys.argv[1]),account_id=1,spec=json.loads(Path(sys.argv[2]).read_text()),values=[contribution(row(2))],failpoint=lambda stage: os._exit(17) if stage=='after_groups' else None)\n",encoding='utf-8')
        result=subprocess.run([sys.executable,str(script),str(self.db),str(spec)],capture_output=True)
        self.assertEqual(result.returncode,17,result.stderr.decode(errors='replace'))
        self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id']),before)

    def test_claims_stale_only_when_basis_changed(self):
        a=row(1);b=row(2);b['context']['hero_id']=8;b=signed(b);first=self.put([a,b]);state=snapshot(path=self.db,contract_id=first['contract_id'])
        gid=next(k for k,v in state['groups'].items() if v['scope']['hero_id']==64)
        save_claim(path=self.db,contract_id=first['contract_id'],claim_id='authored',text='Test-only authored statement',basis={gid:digest(state['groups'][gid])},expected_generation=1)
        c=row(3);c['context']['hero_id']=8;self.put([signed(c)])
        self.assertFalse(history(path=self.db,contract_id=first['contract_id'])['claims'][0]['stale'])
        self.put([row(4)]);self.assertTrue(history(path=self.db,contract_id=first['contract_id'])['claims'][0]['stale'])

    def test_new_feature_plan_and_unfinished_coverage(self):
        first=self.put([row(1),row(2)]);target=copy.deepcopy(self.spec);target['catalog_hash']='new'
        plan=plan_rebuild(path=self.db,contract_id=first['contract_id'],target_spec=target,features={'xp_gold_ratio':['xp_rate','gold_rate'],'ward_efficiency':['vision_geometry']})
        self.assertEqual({j['action'] for j in plan['jobs']},{'derive_from_compact','targeted_sources_required'})
        self.assertEqual(reconcile_jobs(path=self.db,contract_id=plan['target_contract'])['completed'],0)
        self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id'])['state']['n'],2)

    def test_compact_feature_materialization_and_stale_plan(self):
        first=self.put([row(1)]);target=copy.deepcopy(self.spec);target['catalog_hash']='extra-feature'
        plan=plan_rebuild(path=self.db,contract_id=first['contract_id'],target_spec=target,features={'ratio':['xp_rate','gold_rate']})
        r=row(1);r['metrics']['ratio']=measure(2,unit='ratio');r=signed(r)
        apply_batch(path=self.db,account_id=1,spec=target,values=[contribution(r)])
        self.assertTrue(reconcile_jobs(path=self.db,contract_id=plan['target_contract'])['coverage_complete'])
        changed=row(1);changed['source_manifest_ref']='new-source';changed=signed(changed)
        self.put([changed],expected_revisions={1:contribution(row(1))['revision']})
        self.assertFalse(reconcile_jobs(path=self.db,contract_id=plan['target_contract'])['coverage_complete'])
        self.assertEqual(history(path=self.db,contract_id=plan['target_contract'])['jobs'][0]['status'],'stale_source_plan')

    def test_metric_removal_matches_full_coverage(self):
        a=row(1);first=self.put([a]);b=copy.deepcopy(a);del b['metrics']['xp_rate'];b=signed(b)
        self.put([b],expected_revisions={1:contribution(a)['revision']})
        reference=apply_batch(path=self.root/'only.sqlite',account_id=1,spec=self.spec,values=[contribution(b)])
        self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id'])['state'],snapshot(path=self.root/'only.sqlite',contract_id=reference['contract_id'])['state'])

    def test_contract_separation_and_no_raw_history_access(self):
        first=self.put([row(1)]);new=copy.deepcopy(self.spec);new['map_version']='different'
        with patch('src.apps.analysis.sources.load_sources',side_effect=AssertionError('raw read forbidden')):
            other=apply_batch(path=self.db,account_id=1,spec=new,values=[contribution(row(1))])
        self.assertNotEqual(first['contract_id'],other['contract_id'])
        self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id'])['state']['n'],1)

    def test_spatial_replacement_removes_previous_cell_contribution(self):
        from src.apps.analysis.spatial.schemas import signed as spatial_signed, DEFAULTS, VERSION
        from src.apps.analysis.spatial.aggregation import empty_group, cell, build_match
        def envelope(a,b):
            g=empty_group(0,'near_even');g['match_ids']=[1];g['seconds']['outside_reported_death']=2400
            g['observed_seconds']['outside_reported_death']=100;g['unknown_seconds']['outside_reported_death']=2300
            for key,n in [('1,1',a),('2,1',b)]:
                if n:cell(g,key)['seconds']['outside_reported_death']=n;g['cells'][key]['match_ids']=[1]
            r=row(1);c={**r['context'],'account_id':1,'match_id':1,'patch_ids':{'stratz':182,'opendota':60}}
            p=spatial_signed({'schema_version':VERSION,'id':'1:spatial:L3','level':3,'context':c,'parameters':DEFAULTS,'groups':[g],'journal_quality':{},'dependencies':{}})
            m=build_match(p);r['dependencies'][m['id']]=m['revision']
            return contribution(signed(r),spatial=p)
        a=envelope(100,0);b=envelope(20,80)
        first=apply_batch(path=self.db,account_id=1,spec=self.spec,values=[a])
        apply_batch(path=self.db,account_id=1,spec=self.spec,values=[b],expected_revisions={1:a['revision']})
        data=snapshot(path=self.db,contract_id=first['contract_id']);g=next(v for k,v in data['groups'].items() if k.startswith('space:'))
        self.assertEqual(g['distribution']['cells']['1,1']['seconds']['outside_reported_death'],20)
        self.assertEqual(g['summary']['observed_outside_death_seconds'],100)
        self.assertEqual(data['state']['coverage']['spatial_matches'],1)

    def test_compare_and_swap_and_corrupt_group(self):
        first=self.put([row(1)])
        with self.assertRaises(CumulativeError):self.put([row(2)],expected_generation=0)
        with connect(self.db) as db:db.execute('UPDATE groups SET payload=? WHERE contract=?',('{}',first['contract_id']))
        with self.assertRaises(CumulativeError):snapshot(path=self.db,contract_id=first['contract_id'])

    def test_packet_bounds(self):
        delta=self.put([row(i) for i in range(10)])
        from src.apps.analysis.cumulative.schemas import encode
        self.assertLessEqual(len(encode(change_packet(delta,budget=2000)).encode()),2000)

    def test_sequence_statistics_reuse_and_local_correction(self):
        rows=[row(i,win=i%2==0) for i in range(8)];first=self.put(rows[:6])
        appended=self.put(rows[6:])
        self.assertEqual(appended['work']['sequence_statistics_reused'],12)
        self.assertEqual(appended['work']['sequence_statistics_rebuilt'],4)
        changed=copy.deepcopy(rows[2]);changed['metrics']['xp_rate']['value']=99;changed=signed(changed)
        delta=self.put([changed],expected_revisions={2:contribution(rows[2])['revision']})
        self.assertEqual(delta['work']['sequence_statistics_rebuilt'],2)
        self.assertEqual(delta['work']['sequence_statistics_reused'],14)
        with connect(self.db,readonly=True) as db:
            cached=json.loads(db.execute('SELECT payload FROM sequences WHERE contract=? AND id=?',(first['contract_id'],'sessions:2')).fetchone()[0])
        self.assertEqual(cached['metrics']['xp_rate']['mean'],99)
        self.assertEqual(cached['match_ids'],[2])

    def test_additive_database_upgrade_keeps_existing_contributions(self):
        first=self.put([row(1)])
        with connect(self.db) as db:
            db.execute('DROP TABLE sequences');db.execute('PRAGMA user_version=1')
        self.put([row(2)])
        with connect(self.db,readonly=True) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2)
            self.assertGreater(db.execute('SELECT COUNT(*) FROM sequences').fetchone()[0],0)
        self.assertEqual(snapshot(path=self.db,contract_id=first['contract_id'])['state']['n'],2)

    def test_cli_redirected_output_is_utf8(self):
        first=self.put([row(1)])
        gid=next(iter(snapshot(path=self.db,contract_id=first['contract_id'])['groups']))
        result=subprocess.run([sys.executable,'-m','src.apps.analysis.cumulative.cli','--db',str(self.db),
                               'read','--contract',first['contract_id'],'--group',gid],capture_output=True,
                              env={**os.environ,'PYTHONIOENCODING':'ascii'})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('gold_rate×win',json.loads(result.stdout.decode('utf-8'))['joint'])


if __name__=='__main__':unittest.main()
