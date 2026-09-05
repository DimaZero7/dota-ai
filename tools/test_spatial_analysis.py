"""Spatial contract tests; only synthetic inputs, no requests to providers."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.test_numeric_analysis import fixture
from src.apps.analysis.numeric.facts import build_numeric_facts
from src.apps.analysis.spatial.schemas import parameters, grid_cell, signed, validate, SpatialError
from src.apps.analysis.spatial.observations import build_observations, route_after, compare_routes
from src.apps.analysis.spatial.aggregation import build_phases, build_match, aggregate_selection, merge_groups, compact_selection
from src.apps.analysis.spatial.services import read_spatial, route_for_action
from src.apps.analysis.spatial.terrain import project, cell_rectangle, load_underlay, underlay_label
from src.apps.analysis.spatial.rendering import render_maps


class SpatialTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('.agent/tmp');scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.root=Path(self.temp.name)
        self.sources=fixture(self.root)
        for slot in range(10):
            self.playback(slot)['playerUpdatePositionEvents']=[{'time':t,'x':80+slot,'y':80} for t in range(121)]
        for e in self.playback()['deathEvents']:e.update(positionX=80,positionY=80)
        for e in self.playback()['heroDamageEvents']:e['fromNpc']=0

    def tearDown(self):self.temp.cleanup()

    def playback(self, slot=0):
        return self.sources.documents[f'stratz/playback-{slot}']['data']['match']['players'][0]['playbackData']

    def build(self, **kwargs):
        facts=build_numeric_facts(self.sources);obs=build_observations(facts,**kwargs)
        phases=build_phases(obs);return facts,obs,phases,build_match(phases)

    def test_grid_half_open_boundaries_and_no_clamping(self):
        p=parameters()
        for x,y,expected in [(0,0,'0,0'),(15.999,16,'0,1'),(16,16,'1,1'),(255.99,255,'15,15'),
                             (256,80,None),(-1,80,None),(True,80,None),(float('nan'),80,None)]:
            self.assertEqual(grid_cell(x,y,p),expected)
        with self.assertRaises(SpatialError):parameters({'cell_size':10})

    def test_underlay_projection_corners_and_cell_alignment(self):
        self.assertEqual(project(64,191,size=127),(0,0))
        self.assertEqual(project(191,64,size=127),(127,127))
        self.assertEqual(cell_rectangle('7,7',cell_size=16,plot_size=127),(48,63,16,16))
        # Outside points are not clamped into a false location on the edge.
        self.assertLess(project(62,194,size=127)[0],0)
        self.assertLess(project(62,194,size=127)[1],0)

    def test_map_embeds_verified_asset_and_discloses_version_without_changing_data(self):
        import xml.etree.ElementTree as ET
        _,_,_,match=self.build();original=copy.deepcopy(match)
        target=self.root/'map.svg'
        render_maps(group=match['distribution'],params=match['parameters'],title='Map <test>',output=target,patch_id=60)
        data=target.read_text(encoding='utf-8');ET.fromstring(data)
        self.assertIn('data:image/jpeg;base64,',data)
        self.assertIn('clip-path="url(#map-clip)"',data)
        self.assertIn('матчи 7.41',data)
        self.assertIn('подложка 7.40',data)
        self.assertEqual(match,original)
        self.assertFalse(load_underlay()['exact_patch_match'])
        self.assertIn('?',underlay_label(lang='en',patch_id=999))

    def test_time_not_point_count_and_death_union(self):
        summary=self.build()[-1]['summary']
        self.assertEqual(summary['reported_dead_seconds'],60)
        self.assertEqual(summary['observed_outside_death_seconds'],60)
        self.playback()['playerUpdatePositionEvents']=[{'time':t,'x':80,'y':80} for t in range(0,121,5)]*2
        other=self.build()[-1]['summary']
        self.assertEqual(summary['observed_outside_death_seconds'],other['observed_outside_death_seconds'])
        self.assertEqual(summary['top_presence_cells'],other['top_presence_cells'])

    def test_long_gap_unknown_and_no_final_extrapolation(self):
        self.playback()['playerUpdatePositionEvents']=[{'time':t,'x':80,'y':80} for t in (0,1,10,11)]
        summary=self.build()[-1]['summary']
        self.assertEqual(summary['observed_outside_death_seconds'],2)
        self.assertEqual(summary['unknown_position_seconds'],118)

    def test_same_time_conflict_is_barrier_and_invalid_stream_not_bridged(self):
        self.playback()['playerUpdatePositionEvents'].append({'time':10,'x':150,'y':150})
        obs=self.build()[1]
        self.assertEqual(obs['audit']['positions']['0']['conflicting_timestamps'],1)
        self.assertTrue(all(s['cell'] is None for s in obs['segments'] if s['start'] in (9,10)))
        self.playback()['playerUpdatePositionEvents'].append({'time':None,'x':90,'y':90})
        self.assertEqual(self.build()[-1]['summary']['unknown_position_seconds'],120)

    def test_missing_death_stream_does_not_mean_alive(self):
        self.playback()['deathEvents']=None
        summary=self.build()[-1]['summary']
        self.assertEqual(summary['unknown_life_seconds'],120)
        self.assertIsNone(summary['coverage_fraction'])

    def test_event_coordinates_are_not_player_coordinates(self):
        for e in self.playback()['killEvents']:e.update(positionX=180,positionY=180)
        obs=self.build()[1]
        self.assertTrue(all(e['cell']=='5,5' for e in obs['events'] if e['kind']=='kill'))
        self.playback()['deathEvents'][0]['positionX']=180
        obs=self.build()[1]
        self.assertIsNone(next(e for e in obs['events'] if e['kind']=='death')['cell'])

    def test_stale_event_location_is_unknown(self):
        self.playback()['playerUpdatePositionEvents']=[{'time':0,'x':80,'y':80},{'time':120,'x':80,'y':80}]
        obs=self.build()[1]
        self.assertTrue(all(e['cell'] is None for e in obs['events'] if e['kind']=='kill'))

    def test_rate_uses_same_support_and_quality_denominator(self):
        match=self.build()[-1];death=match['distribution']['events']['death']
        self.assertEqual(death['rate_eligible_count'],1)  # Second death inside an overlapping death interval.
        self.assertEqual(death['eligible_exposure_seconds'],60)
        self.playback()['assistEvents']=[{'time':100}]
        match=self.build()[-1];assist=match['distribution']['events']['assist']
        self.assertEqual(assist['count'],1)
        self.assertEqual(assist['eligible_exposure_seconds'],0)
        self.assertEqual(assist['rate_eligible_count'],0)

    def test_death_at_state_boundary_uses_pre_event_stratum(self):
        self.playback()['deathEvents']=[{'time':60,'timeDead':10,'positionX':80,'positionY':80},
                                        {'time':90,'timeDead':10,'positionX':80,'positionY':80}]
        obs=self.build()[1]
        event=next(e for e in obs['events'] if e['kind']=='death')
        before=next(s for s in obs['segments'] if s['end']==60)
        self.assertEqual(event['state'],before['state'])

    def test_routes_keep_gaps_and_compare_only_observed_shares(self):
        facts,obs,_,_=self.build()
        route=route_for_action(facts=facts,observations=obs,kind='death',source_index=0)['comparison']
        self.assertEqual(route['before']['end'],20)
        self.assertEqual(route['after']['start'],60)
        self.assertEqual(route['cell_distribution_total_variation'],0)
        self.assertEqual(compare_routes(obs,before=0,after=0)['before']['runs'],[])
        self.assertEqual(route_after(obs,time=110)['end'],120)
        with self.assertRaises(SpatialError):route_after(obs,time=121)
        self.playback()['playerUpdatePositionEvents']=[{'time':0,'x':80,'y':80},{'time':120,'x':160,'y':160}]
        obs=self.build()[1]
        self.assertTrue(all(r['cell'] is None for r in route_after(obs,time=0)['runs']))
        self.assertEqual(obs['transitions'],[])

    def test_isolation_needs_all_allies_and_fresh_positions(self):
        match=self.build()[-1]
        self.assertEqual(match['summary']['mean_nearest_observed_ally_distance'],1)
        self.playback(4)['playerUpdatePositionEvents']=None
        self.assertIsNone(self.build()[-1]['summary']['mean_nearest_observed_ally_distance'])

    def test_partitions_sums_versions_filters_and_duplicate_guard(self):
        _,obs,phases,match=self.build()
        self.assertEqual(sum(s['end']-s['start'] for s in obs['segments']),120)
        self.assertEqual(merge_groups(phases['groups']),match['distribution'])
        packet=aggregate_selection([(match,phases)],filters={'side':'radiant','position':'POSITION_2'})
        self.assertEqual(packet['match_count'],1)
        self.assertEqual(aggregate_selection([(match,phases)],filters={'side':'dire'})['match_count'],0)
        with self.assertRaises(SpatialError):aggregate_selection([(match,phases)]*2)
        other=copy.deepcopy(phases);other['id']='2:spatial:L3';other['context']['match_id']=2;other['context']['patch_ids']['stratz']=2
        other.pop('revision');other=signed(other);other_match=build_match(other)
        with self.assertRaises(SpatialError):aggregate_selection([(match,phases),(other_match,other)])
        self.assertEqual(packet,aggregate_selection([(match,phases)],filters={'side':'radiant','position':'POSITION_2'}))

    def test_side_is_not_mirrored_and_contexts_stay_separate(self):
        _,_,phases,match=self.build()
        other=copy.deepcopy(phases);other.pop('revision');other['id']='2:spatial:L3';other['context']['match_id']=2
        for p in other['context']['roster']:p['isRadiant']=not p['isRadiant']
        for g in other['groups']:
            g['match_ids']=[2]
            for cell in g['cells'].values():cell['match_ids']=[2]
        other=signed(other);other_match=build_match(other)
        packet=aggregate_selection([(match,phases),(other_match,other)])
        self.assertEqual({g['context']['side'] for g in packet['groups']},{'radiant','dire'})
        self.assertEqual(match['summary']['top_presence_cells'],other_match['summary']['top_presence_cells'])

    def test_roundtrip_and_changed_dependency_rejected(self):
        _,obs,phases,match=self.build()
        directory=self.root/'bundle';directory.mkdir();manifest={'files':{}}
        def write(name,data):
            body=json.dumps(data).encode();(directory/f'{name}.json').write_bytes(body)
            manifest['files'][name]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
            (directory/'manifest.json').write_text(json.dumps(manifest))
        for name,data in [('L2',obs),('L3',phases),('L4',match)]:write(name,data)
        self.assertEqual(read_spatial(directory,4),match)
        validate(json.loads(json.dumps(obs)))
        obs.pop('revision');obs['audit']['world_units']='changed';write('L2',signed(obs))
        with self.assertRaises(SpatialError):read_spatial(directory,4)

    def test_compact_budget_keeps_drilldown_reference_without_match_lists(self):
        _,_,phases,match=self.build()
        aggregate=aggregate_selection([(match,phases)])
        packet=compact_selection(aggregate,budget_bytes=1024)
        self.assertLessEqual(len(json.dumps(packet,ensure_ascii=False,separators=(',',':')).encode()),1024)
        self.assertEqual(packet['distribution_ref']['revision'],aggregate['revision'])
        self.assertEqual(packet['omitted_groups'],len(aggregate['groups']))
        self.assertNotIn('match_ids',json.dumps(packet))

    def test_cell_resolution_keeps_time_and_changes_only_spatial_partition(self):
        coarse=self.build(overrides={'cell_size':32})[-1]
        fine=self.build(overrides={'cell_size':8})[-1]
        self.assertEqual(coarse['summary']['observed_outside_death_seconds'],fine['summary']['observed_outside_death_seconds'])
        self.assertNotEqual(coarse['summary']['top_presence_cells'][0]['cell'],fine['summary']['top_presence_cells'][0]['cell'])

    def test_observed_zero_is_not_missing_event_journal(self):
        empty=self.build()[-1]['distribution']['events']['assist']
        self.assertEqual(empty['count'],0)
        self.assertEqual(empty['eligible_exposure_seconds'],60)
        self.playback()['assistEvents']=None
        missing=self.build()[-1]['distribution']['events']['assist']
        self.assertEqual(missing['eligible_exposure_seconds'],0)


if __name__=='__main__':unittest.main()
