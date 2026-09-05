"""Numeric hierarchy tests with synthetic inputs; never collect real matches."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.apps.analysis.sources import Sources
from src.apps.analysis.evidence import digest
from src.apps.analysis.numeric.facts import build_numeric_facts, journal, JOURNALS
from src.apps.analysis.numeric.episodes import build_numeric_episodes, union_seconds, snapshot
from src.apps.analysis.numeric.phases import build_numeric_phases, build_numeric_match
from src.apps.analysis.numeric.schemas import NumericError, measures, validate_node
from src.apps.analysis.numeric.storage import save_bundle, load_node
from src.apps.analysis.numeric.interpretation import prepare_numeric_review, accept_numeric_review, read_numeric_review


def fixture(root: Path) -> Sources:
    players=[];od=[];documents={};refs={}
    for slot in range(10):
        playback={field:[] for field,required in JOURNALS.values()}
        playback.update(playerUpdateGoldEvents=[{'time':t,'networth':100+slot*10+t} for t in (0,60,120)],
                        playerUpdateLevelEvents=[{'time':0,'level':1},{'time':60,'level':6}],
                        playerUpdatePositionEvents=[{'time':0,'x':80,'y':80}],
                        experienceEvents=[{'time':t,'amount':10,'reason':'CREEPS'} for t in (0,60,120)])
        if slot==0:
            playback.update(csEvents=[{'time':t,'isCreep':True,'isNeutral':False,'isAncient':False} for t in (0,59,60,119,120)],
                            goldEvents=[{'time':t,'amount':10,'reason':'CREEP','isValidForStats':True} for t in (0,60,120)],
                            deathEvents=[{'time':20,'timeDead':40},{'time':50,'timeDead':30}],
                            killEvents=[{'time':t} for t in (10,15,100)],
                            assistEvents=[],
                            playerUpdateHealthEvents=[{'time':19,'hp':100,'maxHp':100,'mp':50,'maxMp':100}],
                            purchaseEvents=[{'time':-10,'itemId':42}],
                            heroDamageEvents=[{'time':t,'value':5,'attacker':1,'target':6,'fromIllusion':False,'toIllusion':False} for t in (20,23,40,100)])
        p={'playerSlot':slot,'heroId':slot+1,'steamAccountId':123 if slot==0 else 1000+slot,
           'isRadiant':slot<5,'position':'POSITION_2' if slot in (0,5) else f'POSITION_{slot+3}',
           'lane':'MID_LANE','role':'CORE','kills':3 if slot==0 else 1,'deaths':2 if slot==0 else 0,
           'assists':0,'numLastHits':5 if slot==0 else 0,'numDenies':0,'goldPerMinute':100,
           'experiencePerMinute':15,'networth':220+slot*10,'level':6,'heroDamage':20 if slot==0 else 0,
           'towerDamage':0,'heroHealing':0,'playbackData':playback,'stats':{'wards':[],'wardDestruction':[]}}
        players.append(p)
        other={'player_slot':slot,'account_id':p['steamAccountId'],'hero_id':p['heroId']}
        for a,b in [('kills','kills'),('deaths','deaths'),('assists','assists'),('last_hits','numLastHits'),
                    ('denies','numDenies'),('gold_per_min','goldPerMinute'),('xp_per_min','experiencePerMinute'),
                    ('net_worth','networth'),('hero_damage','heroDamage'),('tower_damage','towerDamage'),('hero_healing','heroHealing')]:other[a]=p[b]
        od.append(other)
        documents[f'stratz/playback-{slot}']={'data':{'match':{'id':1,'players':[copy.deepcopy(p)]}}}
    st={'id':1,'durationSeconds':120,'startDateTime':1000,'didRadiantWin':True,'gameMode':'TEST',
        'gameVersionId':1,'players':players,'towerDeaths':[]}
    documents['stratz/overview']={'data':{'match':copy.deepcopy(st)}}
    documents['stratz/stats']={'data':{'match':{'players':copy.deepcopy(players)}}}
    for key,body in documents.items():
        path=root/(key.replace('/','_')+'.json');path.write_text(json.dumps(body),encoding='utf-8')
        refs[key]={'source':'stratz','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'retrieved_at_utc':'2026-09-05'}
    return Sources(root,1,123,{'players':od,'patch':1},st,documents,refs)


def build(sources: Sources) -> list:
    a=build_numeric_facts(sources);b=build_numeric_episodes(a);c=build_numeric_phases(b);d=build_numeric_match(c)
    return [a,b,c,d]


class NumericTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch)
        self.root=Path(self.temp.name).resolve();self.sources=fixture(self.root)

    def tearDown(self):self.temp.cleanup()

    def mutate_journal(self,field,value):
        pb=self.sources.documents['stratz/playback-0']['data']['match']['players'][0]['playbackData']
        if value=='REMOVE':pb.pop(field)
        else:pb[field]=value

    def test_disjoint_windows_terminal_boundary_and_union(self):
        a,b,c,d=build(self.sources)
        self.assertEqual([w['xp'] for w in b['windows']],[10,20])
        self.assertEqual([w['counts']['farm'] for w in b['windows']],[2,3])
        self.assertEqual(sum(w['death_seconds_proxy'] for w in b['windows']),60)
        self.assertEqual(d['summary']['death_fraction_proxy'],.5)
        self.assertEqual(d['summary']['recorded_xp'],30)
        self.assertEqual(sum(p['counts']['farm'] for p in c['phases']),5)
        self.assertEqual(union_seconds([(20,60),(50,80)],0,120),60)
        self.assertEqual(union_seconds([(20,60),(50,80)],60,70),10)

    def test_missing_null_empty_and_invalid_are_distinct(self):
        for value,status in [('REMOVE','missing'),(None,'null'),([], 'empty'),({},'malformed')]:
            self.mutate_journal('experienceEvents',value)
            a,b,c,d=build(self.sources)
            self.assertEqual(a['journals']['xp']['quality']['field_state'],status)
            self.assertEqual(d['summary']['recorded_xp'],0 if value==[] else None)
        self.mutate_journal('experienceEvents',[{'time':1,'amount':True},{'time':2,'amount':None},{'time':3,'amount':0}])
        a,b,c,d=build(self.sources)
        self.assertEqual(a['journals']['xp']['quality']['invalid_events'],2)
        self.assertFalse(a['journals']['xp']['quality']['eligible'])
        self.assertEqual(d['summary']['recorded_xp'],0)

    def test_one_journal_conflict_does_not_drop_other_metrics(self):
        self.mutate_journal('assistEvents',[{'time':10}])
        a,b,c,d=build(self.sources)
        self.assertEqual(a['journals']['assist']['quality']['status'],'conflicting')
        self.assertEqual(d['summary']['recorded_xp'],30)
        self.assertAlmostEqual(measures(d)['combat.participation']['value'],3/7)
        self.assertTrue(measures(d)['combat.participation']['coverage']['eligible'])

    def test_source_final_conflict_marks_participation(self):
        self.sources.opendota['players'][0]['kills']=9
        d=build(self.sources)[-1]
        self.assertFalse(measures(d)['combat.participation']['coverage']['eligible'])
        self.assertEqual(d['summary']['recorded_xp'],30)

    def test_snapshot_staleness_and_unknown_same_position(self):
        a,b,c,d=build(self.sources)
        j=a['journals']['economy']
        self.assertIsNotNone(snapshot(j,5,('networth',)))
        self.assertIsNone(snapshot(j,6,('networth',)))
        self.assertIsNone(snapshot(j,-1,('networth',)))
        for p in self.sources.stratz['players']:p['position']=None
        b=build(self.sources)[1]
        self.assertIsNone(b['windows'][0]['state_start']['counterpart_slot'])

    def test_post_kill_followup_censoring_and_unique_deaths(self):
        m=measures(build(self.sources)[1])['episodes.post_kill_death']
        self.assertEqual((m['numerator'],m['denominator']),(2,2))
        self.assertEqual(m['details']['unique_deaths'],2)
        self.assertEqual(m['details']['right_censored_kills'],1)
        self.mutate_journal('killEvents',[{'time':10}])
        m=measures(build(self.sources)[1])['episodes.post_kill_death']
        self.assertIsNone(m['value'])

    def test_combat_is_not_full_teamfight_and_rejects_unknown_attribution(self):
        pb=self.sources.documents['stratz/playback-0']['data']['match']['players'][0]['playbackData']
        pb['heroDamageEvents'] += [{'time':50,'value':99,'attacker':1,'target':999,'fromIllusion':False,'toIllusion':False},
                                  {'time':51,'value':99,'attacker':1,'target':6,'fromIllusion':True,'toIllusion':False}]
        b=build(self.sources)[1]
        self.assertEqual(len(b['combat_episodes']['clusters']),3)
        self.assertEqual(b['combat_episodes']['matched_events'],4)
        self.assertEqual(b['combat_episodes']['unselected_events'],2)

    def test_purchase_before_zero_and_level_censoring(self):
        m=measures(build(self.sources)[-1])
        self.assertEqual(m['items.purchase_time']['value']['42']['time'],-10)
        levels=m['xp.level_time']['value']
        self.assertEqual(levels[0]['time'],60)
        self.assertTrue(levels[1]['right_censored'])
        self.assertIsNone(levels[1]['time'])

    def test_damage_partition_preserves_illusion_contribution_without_double_count(self):
        pb=self.sources.documents['stratz/playback-0']['data']['match']['players'][0]['playbackData']
        pb['heroDamageEvents'] += [{'time':50,'value':99,'attacker':1,'target':6,'fromIllusion':False,'toIllusion':True},
                                  {'time':51,'value':7,'attacker':1,'target':6,'fromIllusion':True,'toIllusion':False},
                                  {'time':52,'value':3,'attacker':1,'target':999}]
        m=measures(build(self.sources)[-1])['combat.damage'];p=m['details']['attribution']
        self.assertEqual(p,{'original_enemy_targets':27,'illusion_enemy_targets':99,'unknown_attribution':3,'own_illusion_to_original_enemy':7})
        self.assertEqual(m['value'],p['original_enemy_targets']+p['illusion_enemy_targets']+p['unknown_attribution'])

    def test_missing_opponent_xp_does_not_become_zero_delta(self):
        self.sources.documents['stratz/playback-5']['data']['match']['players'][0]['playbackData']['experienceEvents']=None
        c=build(self.sources)[2]
        self.assertIsNone(c['phases'][0]['recorded_xp_counterpart_delta'])
        self.assertAlmostEqual(c['phases'][0]['recorded_xp_team_share'],.2)

    def test_partial_snapshots_have_coverage_and_missing_death_has_no_return(self):
        self.mutate_journal('playerUpdateGoldEvents',[{'time':0,'networth':100}])
        self.mutate_journal('deathEvents',None)
        a,b,c,d=build(self.sources)
        self.assertEqual(measures(b)['economy.team_state']['quality_status'],'partial')
        self.assertIsNone(measures(d)['episodes.return_activity']['value'])
        self.assertIsNone(measures(d)['episodes.post_kill_death']['value'])

    def test_changed_child_with_updated_manifest_invalidates_parent(self):
        nodes=build(self.sources);directory=self.root/'bundle'
        save_bundle(directory,nodes,key='test',catalog_hash='test')
        nodes[0]['source_clock']='changed'
        nodes[0]['revision']=digest({k:v for k,v in nodes[0].items() if k!='revision'})
        save_bundle(directory,nodes,key='test',catalog_hash='test')
        with self.assertRaises(NumericError):load_node(directory,4)

    def test_lower_graph_no_model_and_incompatible_versions(self):
        nodes=build(self.sources)
        self.assertTrue(all(n['interpretations']==[] for n in nodes))
        for child,parent in zip(nodes,nodes[1:]):self.assertEqual(parent['children_manifest_ref'],{child['id']:child['revision']})
        with self.assertRaises(NumericError):build_numeric_match(nodes[1])
        nodes[1]['method_versions']['numeric']='old'
        with self.assertRaises(NumericError):validate_node(nodes[1])

    def test_phase_overlap_rejected(self):
        b=build(self.sources)[1]
        b['windows'][1]['start']=59
        b['revision']=digest({k:v for k,v in b.items() if k!='revision'})
        with self.assertRaises(NumericError):build_numeric_phases(b)

    def test_storage_integrity_and_repeatability(self):
        nodes=build(self.sources)
        self.assertEqual(nodes[-1]['revision'],build(self.sources)[-1]['revision'])
        directory=self.root/'bundle';save_bundle(directory,nodes,key='test',catalog_hash='test')
        self.assertEqual(load_node(directory,4),nodes[3])
        (directory/'L4.json').write_text('{}',encoding='utf-8')
        with self.assertRaises(NumericError):load_node(directory,4)

    def test_optional_review_budget_cache_and_stale_source(self):
        nodes=build(self.sources);directory=self.root/'bundle';store=self.root/'reviews'
        save_bundle(directory,nodes,key='test',catalog_hash='test')
        with self.assertRaises(NumericError):prepare_numeric_review(root=self.root,directory=directory,episode_id='death:0',question='Why?',store=store,budget_bytes=20)
        packet=prepare_numeric_review(root=self.root,directory=directory,episode_id='death:0',question='Why?',store=store)
        self.assertEqual(packet['packet_id'],prepare_numeric_review(root=self.root,directory=directory,episode_id='death:0',question='Why?',store=store)['packet_id'])
        response={'packet_id':packet['packet_id'],'author':'current Codex','summary':'A test annotation.',
                  'claims':[{'kind':'hypothesis','statement':'Recorded interval only','basis':['death:0'],
                             'alternative':'Buyback','uncertainty':'Actual absence unknown','check':'Inspect source'}]}
        accepted=accept_numeric_review(root=self.root,directory=directory,store=store,packet=packet,response=response)
        self.assertEqual(accepted,read_numeric_review(root=self.root,directory=directory,store=store,packet_id=packet['packet_id']))
        response['claims'][0]['basis']=['made_up']
        with self.assertRaises(NumericError):accept_numeric_review(root=self.root,directory=directory,store=store,packet=packet,response=response)
        (self.root/'stratz_playback-0.json').write_text('{}',encoding='utf-8')
        with self.assertRaises(NumericError):read_numeric_review(root=self.root,directory=directory,store=store,packet_id=packet['packet_id'])


if __name__=='__main__':unittest.main()
