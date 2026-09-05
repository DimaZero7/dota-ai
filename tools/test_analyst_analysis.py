"""Evidence, temporal exclusion and budget contracts; no generated coaching in production."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.test_longitudinal_analysis import row
from src.apps.analysis.longitudinal.schemas import signed
from src.apps.analysis.cumulative.schemas import contract, contribution
from src.apps.analysis.cumulative.services import apply_batch
from src.apps.analysis.analyst.schemas import AnalystError, size
from src.apps.analysis.analyst.services import prepare, accept_profile, read_profile
from src.apps.analysis.analyst.retrieval import drill, accept_lower
from src.apps.analysis.analyst.comparison import prepare_match, accept_match
from src.apps.analysis.analyst.storage import audit
from src.apps.analysis.cumulative.storage import connect
from src.apps.analysis.evidence import digest


def words(value):return {'ru':value,'en':value}


def response(packet, *, previous=None, status='testing'):
    g=next(g for g in packet['groups'] if g['data']['scope']['grouping']=='hero_position_relaxed')
    return {'author':'current Codex','session_id':packet['session_id'],'portrait':words('Synthetic fixture only'),
            'limitations':words('Fixture; no gameplay meaning'),'change_reason':words('Review synthetic values'),
            'wording':'retain' if previous else 'revise',
            'hypotheses':[{'id':'sample','status':status,'confidence':'preliminary',
                'scope':{k:g['data']['scope'][k] for k in ('hero_id','position')},'support':[g['ref']],'counterevidence':[],
                **{k:words('Synthetic test only') for k in ('statement','alternative','criterion','uncertainty','decision_reason','change')}}],
            'priorities':[{'action':words('Check fixture'),'baseline':words('Synthetic values'),'check':words('Verify changes'),'hypotheses':['sample']}]}


class AnalystTests(unittest.TestCase):
    def setUp(self):
        Path('.agent/tmp').mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir='.agent/tmp')
        self.db=Path(self.temp.name)/'store.sqlite';self.spec=contract(catalog={'test':1},map_version='native-1',recent_count=3)
        self.rows=[row(i,win=i%2==0) for i in range(8)]
        self.key=apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(r) for r in self.rows[:5]])['contract_id']

    def tearDown(self):self.temp.cleanup()
    def packet(self,question='Assess synthetic evidence'):return prepare(path=self.db,contract_id=self.key,question=question)
    def add(self):return apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(r) for r in self.rows[5:]])

    def test_main_has_definitions_conditions_no_cards_or_raw_reads(self):
        with (patch('src.apps.analysis.analyst.retrieval.envelope',side_effect=AssertionError('No cards')),
              patch('src.apps.analysis.sources.load_sources',side_effect=AssertionError('No raw'))):
            p=self.packet()
        self.assertLessEqual(size(p),32000);self.assertTrue(p['definitions']);self.assertNotIn('matches',p)
        self.assertEqual(audit(path=self.db,session_id=p['session_id'])['usage']['main_match_cards_read'],0)

    def test_initial_update_retained_wording_and_history(self):
        a=self.packet();first=accept_profile(path=self.db,session_id=a['session_id'],response=response(a))
        self.add();self.assertEqual(read_profile(path=self.db,contract_id=self.key)['freshness'],'pending_analyst_review')
        b=self.packet();self.assertEqual(b['mode'],'update');self.assertEqual(b['changes']['operations']['new_match'],3)
        second=accept_profile(path=self.db,session_id=b['session_id'],response=response(b,previous=first))
        self.assertEqual(first['portrait'],second['portrait']);self.assertEqual(second['previous_revision'],first['revision'])
        self.assertEqual(read_profile(path=self.db,contract_id=self.key,revision=first['revision'])['portrait'],first['portrait'])

    def test_stale_packet_rejected(self):
        p=self.packet();self.add()
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=p['session_id'],response=response(p))

    def test_unseen_evidence_and_scope_rejected(self):
        p=self.packet();r=response(p);r['hypotheses'][0]['support']=['unopened']
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=p['session_id'],response=r)
        r=response(p);r['hypotheses'][0]['scope']['hero_id']=999
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=p['session_id'],response=r)

    def test_repetition_cannot_upgrade_confidence(self):
        p=self.packet();first=accept_profile(path=self.db,session_id=p['session_id'],response=response(p))
        q=self.packet('Reconsider identical evidence')
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=q['session_id'],response=response(q,previous=first,status='supported'))

    def test_lifecycle_rejected_can_only_reopen_for_testing(self):
        p=self.packet();accept_profile(path=self.db,session_id=p['session_id'],response=response(p))
        q=self.packet('Review rejection');r=response(q,status='rejected');r['hypotheses'].append({**r['hypotheses'][0],'id':'other','status':'discovered'});r['priorities'][0]['hypotheses']=['other']
        accept_profile(path=self.db,session_id=q['session_id'],response=r)
        z=self.packet('Reopen without new test');r=response(z,status='supported')
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=z['session_id'],response=r)

    def test_drill_budget_persists_across_prepare_and_counts_cards(self):
        p=self.packet()
        for _ in range(4):drill(path=self.db,session_id=p['session_id'],kind='match',target='1',reason='Check synthetic case')
        self.assertEqual(self.packet()['session_id'],p['session_id'])
        with self.assertRaises(AnalystError):drill(path=self.db,session_id=p['session_id'],kind='match',target='1',reason='Another case')
        usage=audit(path=self.db,session_id=p['session_id'])['usage'];self.assertEqual(usage['cards_read'],4);self.assertLessEqual(usage['drill_bytes'],12000)

    def test_group_examples_selection_and_missingness(self):
        p=self.packet();g=next(g for g in p['groups'] if g['data']['scope']['grouping']=='hero_position_relaxed')
        d=drill(path=self.db,session_id=p['session_id'],kind='group',target=g['ref'],metric='xp_rate',reason='Check tails and typical observations')
        self.assertEqual({r['match_id'] for r in d['data']['examples']},{0,2,4})

    def test_match_baseline_excludes_target_and_future(self):
        self.add()
        past=prepare_match(path=self.db,contract_id=self.key,match_id=3,question='Compare past only')
        retrospective=prepare_match(path=self.db,contract_id=self.key,match_id=3,question='Compare retrospective',mode='retrospective')
        self.assertEqual(past['baseline']['n'],3);self.assertEqual(retrospective['baseline']['n'],7)
        self.assertEqual(past['baseline']['metrics']['xp_rate']['mean'],2)
        self.assertTrue(past['baseline']['target_excluded']);self.assertFalse(past['memory']['blind'])

    def test_historical_profile_uses_earlier_period_and_context(self):
        p=self.packet();first=accept_profile(path=self.db,session_id=p['session_id'],response=response(p));self.add()
        q=self.packet();accept_profile(path=self.db,session_id=q['session_id'],response=response(q,previous=first))
        review=prepare_match(path=self.db,contract_id=self.key,match_id=7,question='Use earlier profile')
        self.assertEqual(review['historical_profile']['revision'],first['revision'])
        self.assertIsNone(prepare_match(path=self.db,contract_id=self.key,match_id=2,question='No earlier independent profile')['historical_profile'])

    def test_forecast_hides_postgame_information_and_blocks_drill(self):
        p=prepare_match(path=self.db,contract_id=self.key,match_id=4,question='Forecast input simulation',mode='forecast')
        self.assertNotIn('win',p['target']);self.assertNotIn('duration',p['target']);self.assertNotIn('metrics',p['target'])
        self.assertNotIn('duration_band',p['target']['context'])
        with self.assertRaises(AnalystError):drill(path=self.db,session_id=p['session_id'],kind='match',target='4',reason='Would leak target outcome')

    def test_unknown_metric_and_non_substantive_lower_question(self):
        with self.assertRaises(AnalystError):prepare(path=self.db,contract_id=self.key,question='unknown',metrics=['label'])
        p=self.packet()
        with self.assertRaises(AnalystError):drill(path=self.db,session_id=p['session_id'],kind='episode',target='1',reason='look')

    def test_duplicate_accept_and_old_response_conflict(self):
        p=self.packet();r=response(p);a=accept_profile(path=self.db,session_id=p['session_id'],response=r)
        self.assertEqual(a,accept_profile(path=self.db,session_id=p['session_id'],response=r))
        r['portrait']=words('Changed')
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=p['session_id'],response=r)

    def test_changed_values_are_delivered_as_before_after(self):
        p=self.packet();accept_profile(path=self.db,session_id=p['session_id'],response=response(p));self.add()
        q=self.packet();g=next(g for g in q['groups'] if g['data']['scope']['grouping']=='hero_position_relaxed')
        self.assertEqual(g['change']['before']['n'],5);self.assertEqual(g['change']['after']['n'],8)
        self.assertIn(g['ref'],q['changes']['stale_previous_evidence'])

    def test_new_context_does_not_strengthen_unchanged_hypothesis(self):
        p=self.packet();first=accept_profile(path=self.db,session_id=p['session_id'],response=response(p))
        r=row(99);r['context']['position']='POSITION_5';r=signed(r)
        apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(r)])
        q=self.packet();self.assertEqual(q['changes']['stale_previous_evidence'],[])
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=q['session_id'],response=response(q,previous=first,status='supported'))

    def test_unknown_or_overlapping_time_excluded_from_past_baseline(self):
        other=copy.deepcopy(self.rows[1]);other['duration']=4*86400;other=signed(other)
        apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(other)],expected_revisions={1:contribution(self.rows[1])['revision']})
        p=prepare_match(path=self.db,contract_id=self.key,match_id=3,question='Exclude overlapping finish')
        self.assertEqual(p['baseline']['n'],2)

    def test_main_budget_at_one_thousand_without_full_match_reads(self):
        path=Path(self.temp.name)/'scale.sqlite';rows=[]
        for i in range(1000):
            r=row(i);r['context']['hero_id']=i%20+1;rows.append(contribution(signed(r)))
        key=apply_batch(path=path,account_id=1,spec=self.spec,values=rows)['contract_id']
        with patch('src.apps.analysis.analyst.retrieval.envelope',side_effect=AssertionError('No cards')):
            p=prepare(path=path,contract_id=key,question='Thousand-row packet budget')
        self.assertLessEqual(size(p),32000);self.assertEqual(p['summary']['n'],1000)
        self.assertEqual(audit(path=path,session_id=p['session_id'])['usage']['main_match_cards_read'],0)

    def numeric_fixture(self):
        from src.apps.analysis.numeric.schemas import VERSION, METHOD, PARAMETERS
        import hashlib
        directory=Path(self.temp.name)/'numeric';directory.mkdir()
        data={'schema_version':VERSION,'method_versions':{'numeric':METHOD},'parameter_hash':digest(PARAMETERS),
              'id':'1:1:numeric:L2','level':2,'scope':{'match_id':1,'account_id':1},'source_manifest_ref':'fixture',
              'measurements':[{'metric_id':'episodes.return_activity','value':[{'id':'death:0','time':60,'reported_end':90,'reported_seconds':30}]}],
              'windows':[]}
        data['revision']=digest(data);body=json.dumps(data).encode();(directory/'L2.json').write_bytes(body)
        (directory/'manifest.json').write_text(json.dumps({'files':{'L2.json':{'revision':data['revision'],'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}}}))
        r=row(1,win=False);r['dependencies'][data['id']]=data['revision'];r=signed(r)
        apply_batch(path=self.db,account_id=1,spec=self.spec,values=[contribution(r)],expected_revisions={1:contribution(self.rows[1])['revision']})
        return directory

    def test_lower_assessment_reused_and_corrupt_input_rejected(self):
        directory=self.numeric_fixture();p=self.packet();reason='Test whether this synthetic episode permits a causal interpretation'
        kw={'kind':'episode','target':'1','reason':reason,'selector':'longest','root':Path(self.temp.name),'numeric_bundles':{1:'numeric'}}
        d=drill(path=self.db,session_id=p['session_id'],**kw)
        authored={'author':'current Codex','kind':'hypothesis','basis':[d['ref']],'input_revision':d['interpretation_input_revision'],
                  **{k:words('Synthetic assessment only') for k in ('assessment','alternative','uncertainty','next_check')}}
        first=accept_lower(path=self.db,session_id=p['session_id'],ref=d['ref'],response=authored)
        q=self.packet('Independent review of identical input');again=drill(path=self.db,session_id=q['session_id'],**kw)
        self.assertEqual(again['interpretation']['revision'],first['revision'])
        self.assertEqual(audit(path=self.db,session_id=q['session_id'])['usage']['lower_model_answers'],0)
        (directory/'L2.json').write_text('{}')
        with self.assertRaises(AnalystError):drill(path=self.db,session_id=q['session_id'],**kw)

    def test_concurrent_profile_review_rejected_and_publication_atomic(self):
        a=self.packet('First reviewer');b=self.packet('Second reviewer')
        accept_profile(path=self.db,session_id=a['session_id'],response=response(a))
        with self.assertRaises(AnalystError):accept_profile(path=self.db,session_id=b['session_id'],response=response(b))
        with connect(self.db,readonly=True) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM analyst_profiles').fetchone()[0],1)

    def test_match_answer_requires_opened_evidence_and_is_recorded(self):
        p=prepare_match(path=self.db,contract_id=self.key,match_id=4,question='Authored synthetic review')
        r={'author':'current Codex','session_id':p['session_id'],'basis':['target','baseline'],
           **{k:words('Synthetic match review') for k in ('assessment','alternative','uncertainty','next_check')}}
        accept_match(path=self.db,session_id=p['session_id'],response=r)
        self.assertGreater(audit(path=self.db,session_id=p['session_id'])['usage']['answer_bytes'],0)


if __name__=='__main__':unittest.main()
