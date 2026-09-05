"""Known patterns, false associations, missingness and bounded L5 retrieval."""
import copy
import hashlib
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.apps.analysis.longitudinal.schemas import VERSION, PARAMETERS, LongitudinalError, measure, signed
from src.apps.analysis.longitudinal.statistics import describe, distribution, ranks, correlation, permutation_p, bonferroni
from src.apps.analysis.longitudinal.sessions import chronology, sensitivity
from src.apps.analysis.longitudinal.cohorts import build_cohorts, recent_comparison
from src.apps.analysis.longitudinal.relations import _evaluate, find_relations, split_days
from src.apps.analysis.longitudinal.services import aggregate_signatures, save_analysis, read_analysis, known_history_gaps
from src.apps.analysis.longitudinal.retrieval import compact_packet, DrillSession, size
from src.apps.analysis.longitudinal.signatures import build_signature, _contrasts
from src.apps.analysis.datasets import month_bounds, discover_month, validate_selection
from src.apps.stratz.clients import StratzClient, TransientRetryStratzClient
from src.apps.stratz.services import collect_match
from src.apps.stratz.exceptions import StratzError


def row(i: int, *, x: float | None = None, y: float | None = None, win: bool = True, day: int | None = None) -> dict:
    x=i if x is None else x;y=2*x if y is None else y
    return signed({'schema_version':VERSION,'level':4,'id':f'{i}:longitudinal:L4','match_id':i,'account_id':1,
        'start_time':1785542400+(i if day is None else day)*86400,'duration':2400,'win':win,
        'context':{'hero_id':64,'position':'POSITION_2','mode':'ALL_PICK_RANKED','side':'radiant',
                   'stratz_version':182,'opendota_version':60,'rank_band':6,'duration_band':2400,
                   'draft_allies':[1,2,3,4,64],'draft_enemies':[6,7,8,9,10]},
        'metrics':{'gold_rate':measure(x,unit='gold/min'),'xp_rate':measure(y,unit='XP/min'),
                   'death_fraction':measure(.1,unit='fraction',numerator=240,denominator=2400)},
        'phases':[],'death_states':[],'parameter_version':copy.deepcopy(PARAMETERS),'dependencies':{},'source_manifest_ref':'fixture'})


class LongitudinalTests(unittest.TestCase):
    def test_ratios_have_two_distinct_means(self):
        d=distribution([measure(.5,unit='fraction',numerator=1,denominator=2),measure(.1,unit='fraction',numerator=10,denominator=100)])
        self.assertAlmostEqual(d['mean'],.3);self.assertAlmostEqual(d['pooled_value'],11/102)
        self.assertAlmostEqual(d['median'],.3)

    def test_missing_nan_and_zero_are_distinct(self):
        d=describe([0,None,float('nan'),True,2]);self.assertEqual(d['n'],2);self.assertEqual(d['missing'],3)
        self.assertEqual(d['median'],1);self.assertEqual(d['q25'],.5)
        self.assertFalse(measure(float('nan'),unit='x')['eligible'])

    def test_incompatible_units_rejected(self):
        with self.assertRaises(ValueError):distribution([measure(1,unit='x'),measure(2,unit='y')])

    def test_ties_constant_and_permutations(self):
        self.assertEqual(ranks([2,1,2]),[2.5,1,2.5]);self.assertIsNone(correlation([1]*5,list(range(5))))
        xs=list(range(20));self.assertLessEqual(permutation_p(xs,xs,seed=1),.002)
        self.assertEqual(permutation_p(xs,xs,seed=4),permutation_p(xs,xs,seed=4))
        self.assertEqual(bonferroni(.02,20),.4);self.assertEqual(bonferroni(.2,20),1)

    def test_day_block_not_episode_or_match_inflation(self):
        points=[{'x':i,'y':i%2,'day':'2026-08-01','match_id':i} for i in range(100)]
        result=_evaluate(points,outcome=True,seed=1,enabled=True)
        self.assertEqual(result['match_effect']['n'],100);self.assertEqual(result['day_block_effect']['n'],1)
        self.assertIsNone(result['p_value'])

    def test_temporal_replication_of_known_pattern(self):
        rows=[row(i,win=i%2==0) for i in range(40)]
        cohorts,members=build_cohorts(rows);result=find_relations(rows,cohorts,members)
        pair=next(c for c in result['candidates'] if c['x']=='gold_rate' and c['y']=='xp_rate' and c['scope']['grouping']=='strict')
        self.assertEqual(pair['status'],'observational_temporal_replication')
        self.assertFalse(pair['causal']);self.assertEqual(pair['discovery']['leave_one_day_out_sign_agreement'],1)

    def test_seeded_null_has_no_replication(self):
        rng=random.Random(90210);rows=[row(i,x=rng.random(),y=rng.random(),win=rng.random()>.5) for i in range(100)]
        c,m=build_cohorts(rows);r=find_relations(rows,c,m)
        self.assertEqual(r['replicated_count'],0)

    def test_holdout_cannot_improve_discovery_rank(self):
        rows=[row(i,win=i%2==0) for i in range(40)];cohorts,members=build_cohorts(rows)
        first=find_relations(rows,cohorts,members)
        for i in range(28,40):
            rows[i]['metrics']['xp_rate']['value']=-100*i;rows[i]=signed(rows[i])
        c,m=build_cohorts(rows);second=find_relations(rows,c,m)
        self.assertEqual([(c['id'],c['priority']) for c in first['candidates']],[(c['id'],c['priority']) for c in second['candidates']])
        changed=next(c for c in second['candidates'] if c['x']=='gold_rate' and c['y']=='xp_rate' and c['scope']['grouping']=='strict')
        self.assertFalse(changed['same_direction'])

    def test_grouping_prevents_role_mixture_and_unknown_patch_pooling(self):
        rows=[row(i) for i in range(8)]
        for r in rows[4:]:r['context']['position']='POSITION_5';r['metrics']['xp_rate']['value']+=1000
        c,m=build_cohorts(rows)
        self.assertTrue(all(g['summary']['n']==4 for g in c))
        for r in rows:r['context']['stratz_version']=None
        c,m=build_cohorts(rows);self.assertTrue(all(g['summary']['n']==1 and not g['comparison_eligible'] for g in c))

    def test_session_end_to_start_and_threshold(self):
        a=row(1);b=row(2);b['start_time']=a['start_time']+a['duration']+3600
        self.assertEqual(chronology([b,a])['summary']['estimated_sessions'],1)
        b['start_time']+=1;self.assertEqual(chronology([a,b])['summary']['estimated_sessions'],2)
        self.assertEqual(sensitivity([a,b])[-1]['estimated_sessions'],1)

    def test_known_gap_breaks_series_and_behavior(self):
        rows=[row(i) for i in range(3)];c=chronology(rows,known_gaps={(0,1)})
        self.assertEqual(c['summary']['max_observed_win_run'],2);self.assertEqual(len(c['transitions']),1)
        self.assertFalse(c['summary']['history_complete'])

    def test_overlap_unknown_time_and_duplicates(self):
        a=row(1);b=row(2);b['start_time']=a['start_time']+1
        self.assertEqual(chronology([a,b])['items'][1]['boundary_reason'],'overlapping_match_times')
        b['start_time']=None;self.assertEqual(len(chronology([a,b])['transitions']),0)
        with self.assertRaises(LongitudinalError):chronology([a,a])

    def test_after_result_behavior_requires_same_duration_context(self):
        a=row(1);b=row(2);b['context']['duration_band']=3000
        c=chronology([a,b]);self.assertIsNone(c['transitions'][0]['behavior_changes']['xp_rate'])

    def test_recent_has_disjoint_periods_and_composition(self):
        rows=[row(i) for i in range(10)];rows[-1]['metrics']['xp_rate']['eligible']=False
        c,m=build_cohorts(rows);r=recent_comparison(rows,c,m,recent_count=3)
        self.assertEqual((r['history_n'],r['recent_n']),(7,3));self.assertEqual(r['matched_group_count'],1)
        metric=r['matched_groups'][0]['metrics']['xp_rate'];self.assertAlmostEqual(metric['coverage_change'],-1/3)

    def test_provenance_duplicates_mixed_accounts_and_parameters(self):
        a=row(1);bad=copy.deepcopy(a);bad['win']=False
        with self.assertRaises(LongitudinalError):aggregate_signatures([bad])
        with self.assertRaises(LongitudinalError):aggregate_signatures([a,a])
        b=row(2);b['account_id']=9
        with self.assertRaises(LongitudinalError):aggregate_signatures([a,signed(b)])
        b=row(2);b['parameter_version']['minimum_days']=2
        with self.assertRaises(LongitudinalError):aggregate_signatures([a,signed(b)])

    def test_packet_and_drill_have_real_budgets_and_countercases(self):
        data,detail=aggregate_signatures([row(i) for i in range(10)])
        packet=compact_packet(data);self.assertLessEqual(size(packet),32000)
        self.assertNotIn('matches',packet);self.assertIn('omitted',packet)
        drill=DrillSession(data,detail);cohort=next(c for c in data['cohorts'] if c['scope']['grouping']=='strict')
        out=drill.query(cohort['drill_ref'],metric='xp_rate')
        self.assertEqual(out['rows'][0]['measure']['value'],0);self.assertEqual(out['rows'][1]['measure']['value'],18)
        self.assertIn('date_utc',out['rows'][0]);self.assertLessEqual(drill.bytes,8000)
        with self.assertRaises(LongitudinalError):drill.query('cohort:missing')
        drill.calls=3
        with self.assertRaises(LongitudinalError):drill.query('index')

    def test_1000_signatures_fit_without_raw_history(self):
        # Few day blocks intentionally prevent expensive/invalid repeated-game inference.
        rows=[row(i,x=i%19,y=i%23,day=i//200) for i in range(1000)]
        data,detail=aggregate_signatures(rows);packet=compact_packet(data)
        self.assertEqual(data['n'],1000);self.assertLessEqual(size(packet),32000)
        self.assertEqual(data['relations']['replicated_count'],0)

    def test_storage_rejects_changed_detail(self):
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            data,detail=aggregate_signatures([row(1),row(2)]);p=Path(tmp);save_analysis(p,data,detail)
            self.assertEqual(read_analysis(p)[0]['revision'],data['revision'])
            detail['l5_revision']='wrong';(p/'detail.json').write_text(json.dumps(signed(detail)),encoding='utf-8')
            with self.assertRaises(LongitudinalError):read_analysis(p)

    def test_known_nonranked_or_missing_match_breaks_link(self):
        rows=[row(1),row(3)];dataset={'visible_history':[{'start_time':row(2)['start_time']}]}
        self.assertEqual(known_history_gaps(rows,dataset),{(1,3)})

    def test_history_keeps_games_without_playback_and_marks_unknown_role(self):
        from src.apps.analysis.longitudinal.services import chronology_rows
        from src.apps.analysis.datasets import validate_selection
        a=row(1);b=row(2)
        history=[{'match_id':r['match_id'],'start_time':r['start_time'],'duration':r['duration'],
                  'hero_id':64,'lobby_type':7,'player_slot':0,'radiant_win':True} for r in (a,b)]
        dataset={'version':'ranked-month-1','account_id':1,'year':2026,'month':8,'matches':history,'visible_history':history}
        validate_selection(dataset,account_id=1)
        rows=chronology_rows([a],dataset);self.assertEqual(len(rows),2)
        summary=chronology(rows)['summary'];self.assertEqual(summary['after_result']['win']['role_change_unknown'],1)
        data,_=aggregate_signatures([a],dataset=dataset)
        self.assertEqual(data['sessions']['n'],2);self.assertEqual(data['n'],1)
        bad=copy.deepcopy(dataset);bad['account_id']=2
        with self.assertRaises(ValueError):aggregate_signatures([a],dataset=bad)

    def test_large_family_gets_declared_permutation_resolution(self):
        rows=[row(i) for i in range(10)]
        for r in rows:
            for i in range(40):r['metrics'][f'feature_{i}']=measure(1,unit='x')
        c,m=build_cohorts(rows);result=find_relations(rows,c,m)
        self.assertGreater(result['planned_permutations'],999)
        self.assertLessEqual(result['smallest_possible_adjusted_p'],.05)

    def test_controlled_contrasts_and_unavailable_journal(self):
        windows=[]
        for i,(damage,xp) in enumerate([(10,100),(0,110),(10,200),(0,120)]):
            windows.append({'id':str(i),'start':i*60,'end':i*60+60,'exposure_seconds':60,
                'state_start':{'team_band':'near_even'},'xp':xp,'damage_attribution':{'original_enemy_targets':damage},
                'counts':{'purchase':0,'death':0}})
        quality={k:{'eligible':True} for k in ('damage','xp','purchase','death')}
        result,details=_contrasts(windows,quality)
        # Combat cases deltas +10/-80 vs noncombat control +90 => -125.
        self.assertEqual(result['post_combat_xp_change']['value'],-125)
        quality['xp']['eligible']=False;self.assertFalse(_contrasts(windows,quality)[0]['post_combat_xp_change']['eligible'])


class DatasetTests(unittest.TestCase):
    def test_query_resume_verifies_bytes_and_refetches_corruption(self):
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        players=[{'playerSlot':i,'steamAccountId':i+1,'heroId':i+10} for i in range(10)]
        match={'id':42,'startDateTime':1000,'durationSeconds':120,'didRadiantWin':True,'players':players}
        selection={'account_id':1,'match_id':42,'hero_id':10,'duration_seconds':120,'selected_history_entry':{'start_time':1000,'radiant_win':True}}
        class Client:
            fail=True
            calls=0
            def query(self,query,variables):
                self.calls+=1;status=200
                if query=='query overview':payload={'data':{'match':match}}
                elif query=='query stats':payload={'data':{'match':{'id':42,'players':[{**p,'stats':{}} for p in players]}}}
                elif query=='query playback':
                    if variables['account']==6 and self.fail:status=503;payload={}
                    else:payload={'data':{'match':{'id':42,'players':[{**players[variables['account']-1],'playbackData':{}}]}}}
                else:payload={}
                body=json.dumps(payload).encode()
                return body,{'status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'retrieved_at_utc':'2026-09-05'}
        with tempfile.TemporaryDirectory(dir=scratch) as tmp,patch('src.apps.stratz.services.build_queries',return_value=({'overview':'query overview','stats':'query stats','playback':'query playback'},[])):
            root=Path(tmp);p=root/'selection.json';p.write_text(json.dumps(selection),encoding='utf-8');client=Client()
            with self.assertRaises(StratzError):collect_match(selection_path=p,account_id=1,output_root=root/'matches',client=client,pause=lambda _:None)
            old=next((root/'matches/42/stratz').iterdir())
            target=old/'playback-0/match.json';target.write_bytes(target.read_bytes()+b' ')
            (old/'playback-1/match.json').unlink()  # ignored raw files may be absent after cloning
            client.fail=False;client.calls=0
            new=collect_match(selection_path=p,account_id=1,output_root=root/'matches',client=client,pause=lambda _:None,reuse_verified_queries=True)
            self.assertEqual(client.calls,7)  # corrupt 0, absent 1, previously failed/unread players 5..9
            meta=json.loads((new/'metadata.json').read_text());self.assertEqual(meta['status'],'complete')
            self.assertEqual(len(meta['requests']),13);self.assertTrue(any(r.get('reused_from') for r in meta['requests']))

    def test_month_moscow_boundaries_and_ranked_filter(self):
        begin,end=month_bounds(2026,8);self.assertEqual(end-begin,31*86400)
        page=[{'match_id':1,'start_time':end,'duration':100,'radiant_win':True,'lobby_type':7},
              {'match_id':2,'start_time':begin+1,'duration':100,'radiant_win':True,'lobby_type':0},
              {'match_id':3,'start_time':begin,'duration':100,'radiant_win':False,'lobby_type':7},
              {'match_id':4,'start_time':begin-1,'duration':100,'radiant_win':False,'lobby_type':7}]
        class Client:
            def fetch(self,path):return json.dumps(page).encode(),{'url':path}
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            data=discover_month(directory=Path(tmp),account_id=1,year=2026,month=8,client=Client())
            self.assertEqual([r['match_id'] for r in data['matches']],[3]);self.assertEqual(len(data['visible_history']),2)
            self.assertFalse(data['history_complete'])
            with self.assertRaises(ValueError):validate_selection(data,account_id=1,match_id=2)

    def test_transport_retry_bounded_and_no_quota_retry(self):
        client=TransientRetryStratzClient(token='test')
        with patch.object(StratzClient,'query',side_effect=[(b'bad',{'status':503}),(b'ok',{'status':200})]) as request,patch('src.apps.stratz.clients.time.sleep'):
            body,meta=client.query('query {}',{});self.assertEqual(body,b'ok');self.assertEqual(request.call_count,2)
            self.assertEqual(len(meta['attempts']),2)
        with patch.object(StratzClient,'query',return_value=(b'quota',{'status':429})) as request:
            self.assertEqual(client.query('query {}',{})[1]['status'],429);self.assertEqual(request.call_count,1)


if __name__=='__main__':unittest.main()
