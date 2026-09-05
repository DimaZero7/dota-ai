"""Real-data acceptance: python -m tools.check_analysis (no network or model API)."""
import json
from pathlib import Path
from src.settings import BASE_DIR,config_toml
from src.apps.analysis.series import run_series
from src.apps.analysis.pipeline import run_match
from src.apps.analysis.sources import load_sources
from src.apps.analysis.quality import evaluate_lower_levels,verify_trace
from src.apps.analysis.review import export_examples
from src.apps.analysis.context import make_packet,ContextBudget
from src.apps.analysis.retrieval import DrillSession,query_events,detail_reference
from src.apps.analysis.pattern_review import review_cases
from src.apps.analysis.evidence import resolve
from src.apps.analysis.sampling import save


def main() -> None:
    root=BASE_DIR.parent; account=config_toml['player']['account_id']
    series,output=run_series(root=root,account_id=account)
    repeat,_=run_series(root=root,account_id=account)
    assert repeat['profile_version']['reused']
    report={'real_matches':[],'series_output':output.relative_to(root).as_posix(),'trace':series['trace'],
            'synthetic_only':['missing playback','corrupt sources and cache','unknown role exclusions',
                              'changed/contradictory profile history','prospective follow-up validation'],
            'model_limitations':['Session interpretations are not blind evaluations.',
                                 'UTF-8 packet sizes are measured; exact model token usage is unavailable.'],
            'meta_applied':False,'repeat_profile_reused':True}
    for mid in series['match_ids']:
        data,path,hit=run_match(root=root,match_id=mid,account_id=account)
        assert hit
        sources=load_sources(root=root,match_id=mid,account_id=account)
        quality=evaluate_lower_levels(data,sources)
        assert not quality['failed'],quality
        report['real_matches'].append({'match_id':mid,'passed_checks':len(quality['checks']),
                                       'trace':verify_trace(data['registry'],data['match_finding']),
                                       'events':len(data['facts']['events']),'output':path.relative_to(root).as_posix()})
        if mid==series['match_ids'][0]:
            report['examples']=export_examples(data,path)
    pattern=max((series['registry'][x] for x in series['pattern_ids']),key=lambda c:c.get('metrics',{}).get('match_count',0))
    profile=series['registry'][series['profile_id']]
    for card in (pattern,profile):
        bundle=make_packet(finding=card,question='Оцени данные, альтернативы и полезность следующего шага. Подробно только Jakiro POSITION_2, без меты.',
                           budget=ContextBudget(),focus_match_ids=pattern['match_ids'] if card['level']==6 else None)
        path=output/f"example-L{card['level']}.packet.json"; save(path,bundle)
        report['examples'][str(card['level'])]={'path':str(path),'packet_id':bundle['packet']['packet_id'],
            'finding_id':card['id'],'input_utf8_bytes':bundle['usage']['input_utf8_bytes']}
    drill=DrillSession(); details={}
    for name,case in review_cases(pattern).items():
        if name=='limitations' or case is None: continue
        data,_,_=run_match(root=root,match_id=case['match_id'],account_id=account)
        sources=load_sources(root=root,match_id=case['match_id'],account_id=account)
        query={'start':case['start']-15,'end':case['end']+1,'slot':data['facts']['context']['target_slot'],
               'kinds':['kill','death','buyback'],'fields':['time','attacker','target','timeDead']}
        detail=drill.request(lambda:query_events(sources=sources,facts=data['facts'],**query),query)
        for event in detail.get('events',[]):
            raw=resolve(root=root,ref=detail_reference(detail,event))
            assert all(raw.get(k)==v for k,v in event['data'].items())
        details[name]=detail
    save(output/'pattern-drill.json',details)
    report['drill']={'calls':drill.calls,'used_bytes':drill.used_bytes,'pending':drill.pending}
    for example in report['examples'].values():
        example['path']=Path(example['path']).relative_to(root).as_posix()
    save(root/'data/prototype/end-to-end.json',report)
    print(json.dumps({'matches':len(report['real_matches']),'trace':report['trace'],
                      'input_bytes':{k:v['input_utf8_bytes'] for k,v in report['examples'].items()},
                      'drill':report['drill'],'series_output':report['series_output']},ensure_ascii=False))


if __name__=='__main__': main()
