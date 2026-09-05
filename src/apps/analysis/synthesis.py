"""File exchange for analyst-authored, bottom-up synthesis. No generated coaching."""
import json
import re
from pathlib import Path

from .evidence import digest, resolve

INSTRUCTIONS = (
    'You are the analyst; software only measures and traces evidence. Synthesize the '
    'immediately lower analyses into an explanation of this player, not a list of totals. '
    'Keep hero, estimated position and both drafts in scope. Compare supporting and '
    'contradicting cases. Separate observed outcomes, interpretations and hypotheses. '
    'No meta, inferred intent, unseen visibility/cooldowns, or automatic death=mistake. '
    'Cite child IDs for each claim. Explain why it matters and what would disprove it. '
    'At L6 lead with a personal working portrait and at most three practical priorities. '
    'A small sample permits a conditional portrait, not a population or psychological diagnosis.'
)
VERSION = 'authored-synthesis-1'


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def _heads(store: Path) -> dict:
    path = store/'heads.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _put(store: Path, node: dict) -> dict:
    revision = digest(node)
    _write(store/'versions'/f'{revision}.json', node)
    heads = _heads(store)
    heads[node['id']] = revision
    _write(store/'heads.json', heads)
    return {**node, 'revision': revision}


def read_analysis(*, store: Path, node_id: str, active: set | None = None) -> dict:
    """Reject stale descendants instead of quietly reusing a superseded analysis."""
    active = set() if active is None else active
    if node_id in active:
        raise ValueError('Synthesis cycle')
    revision = _heads(store).get(node_id)
    if revision is None:
        raise ValueError(f'Awaiting analyst review: {node_id}')
    node = json.loads((store/'versions'/f'{revision}.json').read_text(encoding='utf-8'))
    if digest(node) != revision:
        raise ValueError('Analysis version is corrupt')
    if node.get('version') != VERSION:
        raise ValueError('Stale synthesis rules version')
    active.add(node_id)
    for key, expected in node.get('dependencies', {}).items():
        child = read_analysis(store=store, node_id=key, active=active)
        if child['revision'] != expected:
            raise ValueError(f'Stale analysis {node_id}: changed child {key}')
    active.remove(node_id)
    return {**node, 'revision': revision}


def register_measurement(*, store: Path, node_id: str, match_id: int,
                         payload: dict, source_refs: list[dict], root: Path,
                         limitations: list[str]) -> dict:
    if not source_refs:
        raise ValueError('Source evidence required')
    for ref in source_refs:
        resolve(root=root, ref=ref)
    return _put(store, {'id': node_id, 'level': 1, 'match_ids': [match_id],
                       'payload': payload, 'source_refs': source_refs,
                       'limitations': limitations, 'dependencies': {}, 'version': VERSION})


def prepare_analysis(*, store: Path, node_id: str, level: int, child_ids: list[str],
                     question: str, budget_bytes: int = 32000) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9:_-]{1,100}', node_id) or not 2 <= level <= 6:
        raise ValueError('Invalid analysis ID or level')
    if not child_ids or len(set(child_ids)) != len(child_ids) or node_id in child_ids:
        raise ValueError('Unique children required')
    children = [read_analysis(store=store, node_id=k) for k in child_ids]
    if any(c['level'] != level-1 for c in children):
        raise ValueError('Synthesis must consume the immediately lower level')
    match_ids = sorted({mid for c in children for mid in c['match_ids']})
    if not 1 <= len(match_ids) <= 10 or (level <= 4 and len(match_ids) != 1):
        raise ValueError('Invalid match coverage')
    packet = {'id': node_id, 'level': level, 'version': VERSION,
              'instructions': INSTRUCTIONS, 'question': question, 'match_ids': match_ids,
              'children': [{'id': c['id'], 'match_ids': c['match_ids'],
                            'content': c.get('analysis', c.get('payload')),
                            'limitations': c['limitations']} for c in children],
              'dependencies': {c['id']: c['revision'] for c in children}}
    size = len(json.dumps(packet, ensure_ascii=False).encode('utf-8'))
    if size > budget_bytes:
        raise ValueError(f'Input budget exceeded ({size}>{budget_bytes}); narrow the question')
    packet['usage'] = {'input_utf8_bytes': size, 'input_limit_bytes': budget_bytes,
                       'answer_reserve_bytes': 16000, 'drill_reserve_bytes': 8000,
                       'measured_model_tokens': None}
    packet['packet_id'] = digest(packet)
    _write(store/'packets'/f"{packet['packet_id']}.json", packet)
    return packet


def accept_analysis(*, store: Path, packet: dict, response: dict) -> dict:
    """Validate provenance/shape, not the truth or usefulness of an interpretation."""
    if digest({k: v for k, v in packet.items() if k != 'packet_id'}) != packet['packet_id']:
        raise ValueError('Packet changed')
    if response.get('packet_id') != packet['packet_id'] or response.get('author') != 'current Codex':
        raise ValueError('Explicit current-Codex response for this packet required')
    for key, revision in packet['dependencies'].items():
        if read_analysis(store=store, node_id=key)['revision'] != revision:
            raise ValueError('Review input is stale')
    for field in ('summary', 'scope', 'not_established'):
        if not isinstance(response.get(field), str) or not response[field].strip():
            raise ValueError(f'Missing authored {field}')
    claims = response.get('claims')
    if not isinstance(claims, list) or not 1 <= len(claims) <= 6:
        raise ValueError('One to six interpreted claims required')
    allowed = {c['id']: set(c['match_ids']) for c in packet['children']}
    for claim in claims:
        if claim.get('kind') not in ('observation', 'interpretation', 'hypothesis'):
            raise ValueError('Explicit epistemic status required')
        for key in ('statement', 'why', 'alternative', 'check'):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError(f'Missing claim {key}')
        basis = claim.get('basis', [])
        if not basis or not set(basis) <= allowed.keys():
            raise ValueError('Claims must cite immediate children')
    priorities = response.get('priorities', [])
    if packet['level'] == 6 and not 1 <= len(priorities) <= 3:
        raise ValueError('Personal profile requires one to three priorities')
    for priority in priorities:
        if any(not priority.get(k) for k in ('action', 'reason', 'baseline', 'check', 'basis')):
            raise ValueError('Incomplete training priority')
        if not set(priority['basis']) <= allowed.keys():
            raise ValueError('Priority must cite patterns')
    if len(json.dumps(response, ensure_ascii=False).encode('utf-8')) > packet['usage']['answer_reserve_bytes']:
        raise ValueError('Answer budget exceeded')
    limits = sorted({lim for c in packet['children'] for lim in c['limitations']}
                    | {response['not_established']})
    return _put(store, {'id': packet['id'], 'level': packet['level'],
                       'match_ids': packet['match_ids'], 'analysis': response,
                       'limitations': limits, 'dependencies': packet['dependencies'],
                       'packet_id': packet['packet_id'], 'version': VERSION})


def validate_analysis(*, store: Path, node_id: str, root: Path | None = None) -> dict:
    visited = {}
    def visit(key: str) -> None:
        if key in visited:
            return
        node = read_analysis(store=store, node_id=key)
        visited[key] = node['level']
        if root is not None:
            for ref in node.get('source_refs', []):
                resolve(root=root, ref=ref)
        for child in node['dependencies']:
            visit(child)
    visit(node_id)
    return {'nodes': len(visited), 'levels': sorted(set(visited.values())),
            'match_ids': read_analysis(store=store, node_id=node_id)['match_ids'],
            'sources_verified': root is not None,
            'semantic_truth_automatically_validated': False}
