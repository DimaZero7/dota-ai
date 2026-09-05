"""Apply a profile to a separate match. This is an application, not a seventh level."""
import json
from pathlib import Path
from .evidence import digest
from .synthesis import read_analysis, INSTRUCTIONS


def prepare_match_review(*, store: Path, profile_id: str, match_id: str,
                         comparison_ids: list[str], budget_bytes: int = 32000) -> dict:
    profile = read_analysis(store=store, node_id=profile_id)
    target = read_analysis(store=store, node_id=match_id)
    if profile['level'] != 6 or target['level'] != 4:
        raise ValueError('Expected profile L6 and match analysis L4')
    if set(profile['match_ids']) & set(target['match_ids']):
        raise ValueError('Target match must be excluded from profile evidence')
    if len(comparison_ids) > 3 or len(set(comparison_ids)) != len(comparison_ids):
        raise ValueError('At most three distinct comparison matches')
    comparisons = [read_analysis(store=store, node_id=key) for key in comparison_ids]
    if any(c['level'] != 4 or not set(c['match_ids']) <= set(profile['match_ids']) for c in comparisons):
        raise ValueError('Comparisons must belong to the baseline profile')
    nodes = [profile, target, *comparisons]
    packet = {'kind':'profile_conditioned_match_review', 'instructions':INSTRUCTIONS,
              'question':'Apply the baseline profile to the target: what fits, what differs, which concrete question or error is supported? Compare supplied examples; do not label an unverified alternative as an available action.',
              'profile_id':profile_id, 'target_id':match_id, 'comparison_ids':comparison_ids,
              'baseline_match_ids':profile['match_ids'], 'target_match_ids':target['match_ids'],
              'dependencies':{n['id']:n['revision'] for n in nodes},
              'inputs':[{'id':n['id'],'analysis':n['analysis'],'limitations':n['limitations']} for n in nodes],
              'evaluation':'Retrospective application; analyst has already seen target. No blind test or prospective prediction.'}
    size = len(json.dumps(packet,ensure_ascii=False).encode())
    if size > budget_bytes:
        raise ValueError('Match-review input budget exceeded')
    packet['usage']={'input_utf8_bytes':size,'input_limit_bytes':budget_bytes,
                     'answer_reserve_bytes':16000,'measured_model_tokens':None}
    packet['packet_id']=digest(packet)
    path=store/'applications'/f"{packet['packet_id']}.packet.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return packet


def accept_match_review(*, store: Path, packet: dict, response: dict) -> dict:
    if digest({k:v for k,v in packet.items() if k!='packet_id'}) != packet['packet_id']:
        raise ValueError('Packet changed')
    for key,revision in packet['dependencies'].items():
        if read_analysis(store=store,node_id=key)['revision'] != revision:
            raise ValueError('Match review is stale')
    if response.get('author') != 'current Codex' or response.get('packet_id') != packet['packet_id']:
        raise ValueError('Authored response for this input required')
    if not response.get('summary') or not response.get('not_established'):
        raise ValueError('Assessment and limitations required')
    comparisons=response.get('comparisons',[])
    if not comparisons:
        raise ValueError('At least one explicit match comparison required')
    for row in comparisons:
        if row.get('baseline_id') not in packet['comparison_ids'] or not row.get('meaning'):
            raise ValueError('Unknown or empty comparison')
    if len(json.dumps(response,ensure_ascii=False).encode())>packet['usage']['answer_reserve_bytes']:
        raise ValueError('Match-review answer budget exceeded')
    result={'packet_id':packet['packet_id'],'dependencies':packet['dependencies'],
            'response':response,'evaluation':packet['evaluation']}
    path=store/'applications'/f'{digest(result)}.review.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
