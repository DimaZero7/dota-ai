"""Check native coordinate agreement using saved cross-provider ward placements."""
import json
import math
import statistics
from pathlib import Path

from src.apps.analysis.numeric.storage import load_node, write_json
from src.apps.analysis.evidence import resolve
from src.apps.analysis.spatial.terrain import load_underlay


def verify(root: Path) -> dict:
    report=json.loads((root/'data/prototype/spatial-verification.json').read_text(encoding='utf-8'))
    pairs=[];unmatched=0;refs={}
    for row in report['matches']:
        directory=root/row['bundle']
        manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        facts=load_node(root/manifest['numeric_bundle'],1)
        od_ref={**facts['sources']['opendota'],'pointer':''}
        original=resolve(root=root,ref=od_ref)
        player=next(x for x in original['players'] if x.get('account_id')==facts['context']['account_id'])
        journal=facts['journals']['wards'];resolve(root=root,ref=journal['source_ref'])
        refs[str(row['match_id'])]={'opendota':od_ref,'stratz':journal['source_ref']}
        used=set()
        for event in journal['events']:
            kind={0:'obs_log',1:'sen_log'}.get(event['type'])
            if kind is None:continue
            candidates=[(i,p) for i,p in enumerate(player.get(kind,[]))
                        if abs(event['time']-p['time'])<=2 and (kind,i) not in used]
            if len(candidates)!=1:unmatched+=1;continue
            i,p=candidates[0];used.add((kind,i))
            distance=math.hypot(p['x']-event['positionX'],p['y']-event['positionY'])
            pairs.append({'match_id':row['match_id'],'kind':kind,'stratz_index':event['_source_index'],
                          'opendota_index':i,'stratz_time':event['time'],'opendota_time':p['time'],
                          'stratz_xy':[event['positionX'],event['positionY']],
                          'opendota_xy':[p['x'],p['y']],'distance':distance})
    terrain=load_underlay();terrain.pop('data_uri')
    return {'method':'unique same-type ward pairs within 2 seconds, without reuse',
            'source_refs':refs,'pairs':pairs,'unmatched_or_ambiguous':unmatched,'n':len(pairs),
            'maximum_distance':max((p['distance'] for p in pairs),default=None),
            'median_distance':statistics.median(p['distance'] for p in pairs) if pairs else None,
            'underlay':terrain,'projection':'u=(x-64)/127; v=(191-y)/127',
            'interpretation':'Agreement of observed native frames, not validation of exact 7.41 terrain.'}


if __name__=='__main__':
    result=verify(Path.cwd());write_json(Path('data/prototype/map-calibration.json'),result)
    print(json.dumps({k:result[k] for k in ('n','unmatched_or_ambiguous','maximum_distance','median_distance')}))
