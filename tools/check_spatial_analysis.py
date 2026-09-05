"""Rebuild spatial examples from the ten already saved matches, without network use."""
import argparse
import json
import statistics
from pathlib import Path

from src.apps.analysis.evidence import resolve
from src.apps.analysis.numeric.storage import load_node, write_json
from src.apps.analysis.spatial.services import build_spatial_match, read_spatial
from src.apps.analysis.spatial.observations import build_observations
from src.apps.analysis.spatial.aggregation import build_phases, build_match, aggregate_selection, compact_selection
from src.apps.analysis.spatial.rendering import render_maps


def verify(root: Path) -> dict:
    selection=json.loads((root/'data/prototype/synthesis/selection.json').read_text(encoding='utf-8'))
    names=json.loads((root/'data/prototype/hero_names.json').read_text(encoding='utf-8'))['names']
    rows=[];artifacts=[];pairs=[];checks=0;examples=[];first=None
    for key in selection['lower_outputs']:
        mid=int(key);built=build_spatial_match(root=root,match_id=mid,account_id=selection['account_id'])
        obs,phases,match=built['observations'],built['phases'],built['match'];c=match['context'];s=match['summary']
        manifest=json.loads((built['directory']/'manifest.json').read_text(encoding='utf-8'))
        facts=load_node(root/manifest['numeric_bundle'],1)
        if first is None:first=(built,facts)
        artifacts.append((match,phases));pairs.append(obs['audit']['paired_event_position'])
        assert read_spatial(built['directory'],4)==match
        assert read_spatial(built['directory'],'enriched')==built['enriched']
        assert build_match(build_phases(build_observations(facts)))['revision']==match['revision']
        # Independent integer-second coverage from the source position rows.
        position=facts['journals']['position'];pb=resolve(root=root,ref=position['source_ref'])
        covered=set();ordered=sorted(pb,key=lambda e:e['time'])
        for a,b in zip(ordered,ordered[1:]):
            if 0<b['time']-a['time']<=5 and all(0<=e[k]<256 for e in (a,b) for k in ('x','y')):
                covered.update(range(max(0,a['time']),min(c['duration'],b['time'])))
        deaths=resolve(root=root,ref=facts['journals']['death']['source_ref']);dead=set()
        for e in deaths:dead.update(range(max(0,e['time']),min(c['duration'],e['time']+e['timeDead'])))
        assert s['observed_outside_death_seconds']==len(covered-dead)
        assert s['reported_dead_seconds']==len(dead)
        assert sum(v for v in match['distribution']['seconds'].values())==c['duration']
        for kind in ('farm','xp','gold','kill','assist','death'):
            source=resolve(root=root,ref=facts['journals'][kind]['source_ref'])
            events=[e for e in source if 0<=e['time']<=c['duration']]
            totals=s['events'][kind]
            assert totals['count']==len(events)
            assert totals['value']==sum(e['amount'] if kind in ('xp','gold') else 1 for e in events)
            assert totals['count']==totals['mapped_count']+totals['unmapped_count']
            assert totals['value']==totals['mapped_value']+totals['unmapped_value']
            assert totals['rate_eligible_count']<=totals['mapped_count']
            assert sum(x['events'][kind]['exposure_seconds'] for x in match['distribution']['cells'].values())==totals['eligible_exposure_seconds']
            event=next((e for e in obs['events'] if e['kind']==kind and e['cell'] is not None),None)
            if event:
                original=source[event['source_index']]
                assert original['time']==event['time'];checks+=1
                if kind=='death':
                    x,y=original['positionX'],original['positionY']
                else:
                    point=next(e for e in reversed(ordered) if e['time']<=event['time'])
                    assert event['time']-point['time']<=5
                    x,y=point['x'],point['y']
                assert event['cell']==f'{int(x//16)},{int(y//16)}'
                if mid==int(next(iter(selection['lower_outputs']))) and kind in ('death','xp','kill'):
                    examples.append({'match_id':mid,'kind':kind,'time':event['time'],'cell':event['cell'],
                                     'method':event['location_method'],'rate_eligible':event['rate_eligible'],
                                     'source_ref':{**facts['journals'][kind]['source_ref'],'pointer':facts['journals'][kind]['source_ref']['pointer']+f"/{event['source_index']}"},
                                     'direct_event_xy':[original.get('positionX'),original.get('positionY')]})
        gaps=[b['time']-a['time'] for a,b in zip(ordered,ordered[1:]) if a['time']>=0]
        target=next(p for p in c['roster'] if p['playerSlot']==c['target_slot'])
        rows.append({'match_id':mid,'hero':names.get(str(c['hero_id'])),'hero_id':c['hero_id'],'position':c['position'],
                     'side':'radiant' if target['isRadiant'] else 'dire','version':c['patch_ids'],
                     'bundle':built['directory'].relative_to(root).as_posix(),'revision':match['revision'],
                     'duration':c['duration'],'coverage':s['coverage_fraction'],'observed_seconds':s['observed_outside_death_seconds'],
                     'outside_death_seconds':s['outside_reported_death_seconds'],'death_seconds':s['reported_dead_seconds'],
                     'unknown_position_seconds':s['unknown_position_seconds'],'events':s['events'],
                     'median_gap':statistics.median(gaps),'max_gap':max(gaps),'range':obs['audit']['target_range'],
                     'initial_observations':obs['audit']['initial_observations'],'position_audit':obs['audit']['positions'],
                     'top_presence_cells':s['top_presence_cells'],'transitions':s['transition_count'],
                     'isolation':{'mean':s['mean_nearest_observed_ally_distance'],'samples':s['isolation_samples'],'missing':s['isolation_missing']}})
        print(f'Verified {mid}: coverage={s["coverage_fraction"]:.1%}, deaths eligible={s["events"]["death"]["rate_eligible_count"]}/{s["events"]["death"]["count"]}',flush=True)
    aggregate=aggregate_selection(artifacts);compact=compact_selection(aggregate)
    write_json(root/'data/analysis/spatial/L5.json',aggregate)
    write_json(root/'data/analysis/spatial/L5-compact.json',compact)
    assert len(json.dumps(compact,ensure_ascii=False,separators=(',',':')).encode())<=32000
    assert 'match_ids' not in json.dumps(compact)
    built,facts=first;sensitivity=[]
    for overrides in ({'gap_seconds':2},{'gap_seconds':5},{'gap_seconds':10},{'cell_size':8},{'cell_size':32}):
        m=build_match(build_phases(build_observations(facts,overrides=overrides)))
        sensitivity.append({'parameters':overrides,'observed_seconds':m['summary']['observed_outside_death_seconds'],
                            'coverage':m['summary']['coverage_fraction'],'visited_cells':m['summary']['visited_cells'],
                            'eligible_deaths':m['summary']['events']['death']['rate_eligible_count'],
                            'top_presence_cells':m['summary']['top_presence_cells']})
    # Largest repeated exact-context cohort, deterministic and disclosed in the report.
    repeated=sorted(aggregate['groups'],key=lambda g:(g['summary']['match_count'],g['summary']['observed_outside_death_seconds']),reverse=True)[0]
    for lang in ('ru','en'):
        directory=root/f'docs/{lang}/development/spatial-examples'
        render_maps(group=built['match']['distribution'],params=built['match']['parameters'],
                    title='Death Prophet · 8960626424 · POSITION_2 · Radiant',output=directory/'presence-deaths.svg',lang=lang,patch_id=facts['context']['patch_ids']['opendota'])
        render_maps(group=built['match']['distribution'],params=built['match']['parameters'],
                    title='Death Prophet · 8960626424 · POSITION_2 · Radiant',output=directory/'resources.svg',lang=lang,resources=True,patch_id=facts['context']['patch_ids']['opendota'])
        ctx=repeated['context'];title=f"{names[str(ctx['hero_id'])]} · {ctx['position']} · {ctx['side']} · {ctx['phase']//60}–{ctx['phase']//60+10} min · {ctx['state']} · n={repeated['summary']['match_count']}"
        render_maps(group=repeated['distribution'],params=aggregate['parameters'],title=title,output=directory/'cohort.svg',lang=lang,patch_id=facts['context']['patch_ids']['opendota'])
    return {'version':'spatial-prototype-verification-1','real_matches':len(rows),'new_matches_fetched':0,'meta_applied':False,
            'checks':{'source_hashes':True,'source_event_checks':checks,'independent_time_and_event_sums':True,
                      'deterministic_rebuild':True,'stored_dependency_chain':True,'compact_budget_bytes':32000},
            'paired_event_positions':{kind:{'n':sum(p[kind]['n'] for p in pairs),'exact':sum(p[kind]['exact'] for p in pairs),
                                            'within4':sum(p[kind]['within4'] for p in pairs),'max_distance':max(p[kind]['max_distance'] or 0 for p in pairs)} for kind in pairs[0]},
            'sensitivity_match':facts['context']['match_id'],'sensitivity':sensitivity,'source_examples':examples,
            'cohort_example':{'context':repeated['context'],'summary':repeated['summary'],'match_ids':repeated['distribution']['match_ids']},
            'compact_groups':len(compact['groups']),'total_groups':len(aggregate['groups']),'matches':rows,
            'limits':['No terrain transform or world units verified','Death intervals are estimates','Ten matches cannot establish stable spatial risks','No causal route or visibility claims']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/prototype/spatial-verification.json'))
    args=parser.parse_args();write_json(args.output,verify(Path.cwd()))
