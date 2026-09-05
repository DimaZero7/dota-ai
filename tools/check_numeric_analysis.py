"""Verify numeric L1–L4 on the ten approved local snapshots and export small results."""
import json
from pathlib import Path

from src.apps.analysis.sources import load_sources
from src.apps.analysis.evidence import resolve
from src.apps.analysis.numeric.services import build_numeric_match_from_sources
from src.apps.analysis.numeric.storage import load_node, write_json
from src.apps.analysis.numeric.schemas import measures


def verify(root: Path) -> dict:
    selection=json.loads((root/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    names=json.loads((root/'data/prototype/hero_names.json').read_text(encoding='utf-8'))['names']
    result=[];pointer_checks=0
    for key in selection['lower_outputs']:
        mid=int(key);built=build_numeric_match_from_sources(root=root,match_id=mid,account_id=selection['account_id'])
        directory=Path(built['directory']);nodes=[load_node(directory,level) for level in range(1,5)]
        l1,l2,l3,l4=nodes;m=measures(l4);c=l4['context'];duration=c['duration']
        sources=load_sources(root=root,match_id=mid,account_id=selection['account_id'])
        p=next(p for p in sources.stratz['players'] if p['steamAccountId']==selection['account_id']);pb=p['playbackData']
        xp=sum(e['amount'] for e in pb['experienceEvents'] if 0<=e['time']<=duration)
        gold=sum(e['amount'] for e in pb['goldEvents'] if 0<=e['time']<=duration)
        assert l4['summary']['recorded_xp']==xp
        assert l4['summary']['recorded_gold']==gold
        assert sum(ph['xp'] for ph in l3['phases'])==xp
        assert sum(w['xp'] for w in l2['windows'])==xp
        assert sum(w['exposure_seconds'] for w in l2['windows'])==duration
        # Independent discrete-time union, valid for these integer-second journals.
        dead_seconds=set()
        for e in pb['deathEvents']:
            assert type(e['time']) is int and type(e['timeDead']) is int
            dead_seconds.update(range(max(0,e['time']),min(duration,e['time']+e['timeDead'])))
        assert l4['summary']['death_seconds_proxy']==len(dead_seconds)
        target_od=next(x for x in sources.opendota['players'] if x.get('account_id')==selection['account_id'])
        ally_kills=sum(x['kills'] for x in sources.opendota['players'] if (x['player_slot']<128)==p['isRadiant'])
        assert m['combat.participation']['value']==(target_od['kills']+target_od['assists'])/ally_kills
        assert sum(ph['counts']['farm'] for ph in l3['phases'])==len([e for e in pb['csEvents'] if 0<=e['time']<=duration])
        assert sum(ph['combat_clusters_started'] for ph in l3['phases'])==l4['summary']['combat_clusters']
        for journal in l1['journals'].values():
            if journal['events']:
                event=journal['events'][0]
                original=resolve(root=root,ref={**journal['source_ref'],'pointer':journal['source_ref']['pointer']+f"/{event['_source_index']}"})
                assert original=={k:v for k,v in event.items() if k!='_source_index'}
                pointer_checks+=1
        for child,parent in zip(nodes,nodes[1:]):assert parent['children_manifest_ref']=={child['id']:child['revision']}
        assert all(n['interpretations']==[] for n in nodes)
        # Exact re-run of computation verifies determinism, independent of the cache path.
        rebuilt=build_numeric_match_from_sources(root=root,match_id=mid,account_id=selection['account_id'],
                                                output_root=root/'.agent/tmp/numeric-verify-rebuild',use_cache=False)
        assert rebuilt['match']['revision']==l4['revision']
        cached=build_numeric_match_from_sources(root=root,match_id=mid,account_id=selection['account_id'])
        assert cached['cache_hit'] and cached['match']['revision']==l4['revision']
        phases=m['match.trajectory']['value']
        row={'match_id':mid,'hero':names.get(str(c['hero_id']),str(c['hero_id'])),'hero_id':c['hero_id'],
             'position':c['position'],'win':c['win'],'duration':duration,'bundle':directory.relative_to(root).as_posix(),
             'level_revisions':{f'L{n["level"]}':n['revision'] for n in nodes},
             'level_bytes':{f'L{n["level"]}':(directory/f'L{n["level"]}.json').stat().st_size for n in nodes},
             'xp_first_600s':sum(e['amount'] for e in pb['experienceEvents'] if 0<=e['time']<600),
             'recorded_xp':xp,'recorded_xp_per_minute':l4['summary']['recorded_xp_per_minute'],'source_xpm':p['experiencePerMinute'],
             'xp_residual':m['xp.gain']['details']['residual_vs_reported_xpm'],
             'recorded_gold':gold,'source_gpm':p['goldPerMinute'],'xp_by_reason':m['xp.gain']['value'],
             'gold_by_reason_validity':m['economy.gold_flow']['value'],
             'level_times':m['xp.level_time']['value'],
             'last_hits_journal':m['farm.last_hits']['value'],'last_hits_final':p['numLastHits'],
             'farm_flags':m['farm.last_hits']['details']['flags'],
             'max_internal_farm_gap_seconds':m['farm.last_hits']['details']['event_gaps']['max_internal_gap_seconds'],
             'max_internal_xp_gap_seconds':m['xp.gain']['details']['event_gaps']['max_internal_gap_seconds'],
             'death_seconds_proxy':len(dead_seconds),'death_fraction_proxy':len(dead_seconds)/duration,
             'return_delay_seconds':m['episodes.return_activity']['value'],
             'return_right_censored':m['episodes.return_activity']['details']['right_censored'],
             'activity_bin_seconds_proxy':l4['summary']['activity_bin_seconds_proxy'],
             'kill_participation_final':m['combat.participation']['value'],
             'combat_clusters':l4['summary']['combat_clusters'],
             'damage_raw':m['combat.damage']['value'],'damage_final':p['heroDamage'],
             'damage_partition':m['combat.damage']['details']['attribution'],
             'damage_original_residual':m['combat.damage']['details']['original_enemy_minus_final'],
             'healing_raw':m['support.healing']['value'],'healing_self':m['support.healing']['details']['self'],'healing_final':p['heroHealing'],
             'item_uses':m['items.use_count']['value'],'ability_uses':m['abilities.use_count']['value'],
             'wards_by_native_type':m['vision.placements']['value'],
             'phase_xp_team_share':[ph['recorded_xp_team_share'] for ph in phases],
             'phase_team_band_changes':[ph['team_band_changes'] for ph in phases],
             'journal_quality':{k:v['status'] for k,v in l4['summary']['quality'].items()},
             'deferred':{id:x['coverage']['reason'] for id,x in m.items() if x['quality_status']=='unavailable'}}
        result.append(row)
    return {'version':'numeric-prototype-verification-1','real_matches':len(result),'new_matches_fetched':0,
            'meta_applied':False,'mandatory_model_responses':0,'checks':{'source_identity_and_hashes':True,
            'source_pointer_spot_checks':pointer_checks,'independent_xp_gold_death_union_and_final_kp':True,
            'phase_additivity_and_dependency_graph':True,'deterministic_rebuild':True,'cache_reuse':True},
            'semantic_truth_or_statistical_stability_proven':False,'matches':result}


def main() -> None:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=verify(Path.cwd());write_json(args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k!='matches'}))


if __name__=='__main__':main()
