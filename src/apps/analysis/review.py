"""Export bounded inputs and persist actual session-authored interpretations."""
import json
from pathlib import Path

from .context import make_packet, ContextBudget, validate_response, input_units


def export_examples(data: dict, output: Path) -> dict:
    registry=data['registry']
    selected=[next(c for c in registry.values() if c['level']==i) for i in range(5)]
    selected[2]=next(c for c in registry.values() if c.get('kind')=='risk')
    exported={}
    for card in selected:
        bundle=make_packet(finding=card,question='Что подтверждают данные этого уровня, что нельзя заключить и куда углубиться? Без меты.',
                           budget=ContextBudget(),child_findings=[registry[x] for x in card.get('children',[]) if x in registry])
        path=output/f"example-L{card['level']}.packet.json"
        path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
        exported[str(card['level'])]={'path':str(path),'packet_id':bundle['packet']['packet_id'],
                                      'finding_id':card['id'],'input_utf8_bytes':bundle['usage']['input_utf8_bytes']}
    return exported


def save_review(*, packet_path: Path, response: dict, output_path: Path, extra_ids: set[str] | None = None) -> None:
    bundle=json.loads(packet_path.read_text(encoding='utf-8'))
    validate_response(bundle['packet'],response,extra_ids)
    if input_units(response)>bundle['usage']['answer_reserve']:
        raise ValueError('Model response exceeds reserved answer size')
    wrapped={'origin':'actual current Codex session interpretation; file exchange, not an automatic API call',
             'packet_file':packet_path.name,'packet_id':bundle['packet']['packet_id'],
             'response':response,'input_accounting':bundle['usage'],'response_utf8_bytes':input_units(response),
             'additional_evidence_ids':sorted(extra_ids or set()),
             'validation':'IDs/schema/budget checked; semantic truth requires source review'}
    output_path.write_text(json.dumps(wrapped,ensure_ascii=False,indent=2),encoding='utf-8')
