"""Synthetic edge cases, separate from the real-data acceptance run."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from src.apps.analysis.comparison import compare_matches,measure_match
from src.apps.analysis.episodes import detect_episodes,interval_metrics,timeline_coverage
from src.apps.analysis.evidence import reference,resolve
from src.apps.analysis.history import save_profile_version,profile_changes
from src.apps.analysis.patterns import build_patterns
from src.apps.analysis.pattern_review import revise_pattern
from src.apps.analysis.profile import build_profile
from src.apps.analysis.quality import verify_trace
from src.apps.analysis.storage import cache_key,save_artifact,load_artifact
from src.apps.analysis.training import plan_training,evaluate_followup
from src.apps.analysis.context import validate_response


def match(mid=1,position='POSITION_2',known=True):
    c={'hero_id':64,'hero_name':'Jakiro','position':position,'lane':'MID_LANE','game_mode':22,
       'patch_ids':{'opendota':60,'stratz':182},'target_slot':0,'duration':200,'start_time':mid*1000,
       'roster':[],'rank_context':{'average_rank':None},'journal_available':{'kill':known,'death':known,'damage':known},
       'playback_available':known}
    events=[{'id':f'{mid}:k1','kind':'kill','time':10,'slot':0,'data':{}},
            {'id':f'{mid}:k2','kind':'kill','time':20,'slot':0,'data':{}},
            {'id':f'{mid}:d','kind':'death','time':30,'slot':0,'data':{'timeDead':20}},
            {'id':f'{mid}:k3','kind':'kill','time':190,'slot':0,'data':{}}] if known else []
    card={'id':f'{mid}:match','level':4,'limitations':['visibility unknown'],'children':[],
          'account_id':2,'match_ids':[mid],'observation':'synthetic','support':'observed'}
    return {'match_id':mid,'account_id':2,'match_finding':card['id'],'registry':{card['id']:card},
            'facts':{'match_id':mid,'context':c,'events':events},
            'validation':{'journal_vs_total':{'kill':{'equal':known},'death':{'equal':known}}}}


class SeriesTests(unittest.TestCase):
    def test_correlated_windows_and_censoring(self):
        m=measure_match(match())
        self.assertEqual((m['numerator'],m['denominator'],m['censored_kills']),(2,2,1))
        self.assertEqual(len({e for w in m['windows'] for e in w['death_events']}),1)

    def test_incompatible_positions_and_unknown(self):
        c=compare_matches([match(),match(2,'POSITION_5'),match(3,None)])
        self.assertEqual(len(c['cohorts']),2)
        self.assertEqual(len(c['excluded']),1)
        with self.assertRaises(ValueError): compare_matches([match(),match()])
        with self.assertRaises(ValueError): compare_matches([match(n) for n in range(11)])

    def test_missing_is_not_zero_or_safe(self):
        data=match(known=False); facts=data['facts']
        self.assertIsNone(measure_match(data)['denominator'])
        episodes=detect_episodes(facts)
        self.assertEqual([e['kind'] for e in episodes],['unavailable'])
        self.assertIsNone(interval_metrics(facts,episodes[0])['counts']['death'])
        self.assertEqual(timeline_coverage(episodes,200)['covered_seconds'],0)

    def test_insufficient_profile_and_rejection(self):
        m=match(); c=compare_matches([m]); p=build_patterns(c,m['registry'])[0]
        self.assertEqual(p['support'],'insufficient_data')
        result=build_profile([p],account_id=2)
        self.assertEqual(result['metrics']['stable_traits'],[])
        self.assertEqual(revise_pattern(p,verdict='rejected',reason='alternative verified',evidence_ids=[p['id']])['support'],'insufficient_data')
        with self.assertRaises(ValueError): revise_pattern(p,verdict='rejected',reason='x',evidence_ids=['invented'])

    def test_followup_cannot_reuse_baseline_or_old_games(self):
        a,b=match(2),match(3); c=compare_matches([a,b]); registry={**a['registry'],**b['registry']}
        patterns=build_patterns(c,registry)
        profile=plan_training(build_profile(patterns,account_id=2),patterns)
        priority=profile['metrics']['training_priorities'][0]
        self.assertEqual(evaluate_followup(priority,[])['status'],'untested')
        with self.assertRaises(ValueError): evaluate_followup(priority,[measure_match(a)])
        with self.assertRaises(ValueError): evaluate_followup(priority,[measure_match(match(1))])
        self.assertEqual(evaluate_followup(priority,[measure_match(match(4))])['status'],'observed_followup_only')

    def test_trace_rejects_lost_limits_and_cycles(self):
        registry={'a':{'level':4,'children':['b'],'limitations':[]},'b':{'level':3,'children':[],'limitations':['unknown']}}
        with self.assertRaises(ValueError): verify_trace(registry,'a')
        registry['a']['limitations']=['unknown']; registry['b']['children']=['a']
        with self.assertRaises(ValueError): verify_trace(registry,'a')

    def test_rejects_response_inventing_evidence_or_certainty(self):
        packet={'packet_id':'p','finding':{'id':'f'},'child_index':[],'children':[],'evidence':[]}
        response={'packet_id':'p','findings':[{'support':'hypothesis','hypothesis':'test','observation':'x','limitations':[],'evidence_ids':['unknown']} ]}
        with self.assertRaises(ValueError): validate_response(packet,response)
        response['findings'][0].update(evidence_ids=['f'],support='observed')
        with self.assertRaises(ValueError): validate_response(packet,response)

    def test_history_cache_and_source_corruption(self):
        scratch=Path('.agent/tmp/tests'); scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            root=Path(folder).resolve(); source=root/'source.json'; source.write_text('{"x":1}')
            ref=reference(root=root,file=source,source='synthetic',pointer='/x')
            self.assertEqual(resolve(root=root,ref=ref),1)
            source.write_text('{"x":2}')
            with self.assertRaises(ValueError): resolve(root=root,ref=ref)
            directory=root/'cache'; save_artifact(directory,{'a':1}); self.assertEqual(load_artifact(directory),{'a':1})
            (directory/'data.json').write_text('{}')
            with self.assertRaises(ValueError): load_artifact(directory)
            self.assertNotEqual(cache_key({'sha':'a'},{}),cache_key({'sha':'b'},{}))
            p={'account_id':2,'metrics':{'conditions':[{'pattern_id':'p','numerator':2}]}}
            v1=save_profile_version(root=root,profile=p,source_version='a')
            self.assertTrue(save_profile_version(root=root,profile=p,source_version='a')['reused'])
            q=copy.deepcopy(p); q['metrics']['conditions'][0]['numerator']=0
            v2=save_profile_version(root=root,profile=q,source_version='b')
            self.assertNotEqual(v1['version'],v2['version'])
            self.assertTrue(Path(v1['path']).exists())
            self.assertEqual(len(profile_changes(p,q)['changed']),1)


if __name__=='__main__': unittest.main()
