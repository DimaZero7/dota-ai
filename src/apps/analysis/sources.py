"""Load verified local snapshots; never fetch on import or analysis."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .evidence import digest


@dataclass
class Sources:
    root: Path
    match_id: int
    account_id: int
    opendota: dict
    stratz: dict
    documents: dict
    references: dict

    def ref(self, key: str, pointer: str) -> dict:
        base = self.references[key]
        return {**base, 'pointer': pointer, 'id': digest([base['sha256'], pointer, base['file']])[:24]}


def load_sources(*, root: Path, match_id: int, account_id: int) -> Sources:
    documents, refs = {}, {}
    for source in ('opendota', 'stratz'):
        candidates = sorted((root / 'data/matches' / str(match_id) / source).glob('*/metadata.json'))
        selected = None
        for path in reversed(candidates):
            metadata = json.loads(path.read_text(encoding='utf-8'))
            allowed=('complete','needs_parse_review') if source=='opendota' else ('complete',)
            if metadata.get('status') in allowed and metadata.get('match_id') == match_id:
                selected = (path.parent, metadata)
                break
        if selected is None:
            raise ValueError(f'No complete local {source} snapshot for {match_id}')
        directory, metadata = selected
        for request in metadata['requests']:
            file = (directory / request['file']).resolve()
            file.relative_to(directory.resolve())
            body = file.read_bytes()
            if len(body) != request['bytes'] or hashlib.sha256(body).hexdigest() != request['sha256']:
                raise ValueError(f'Source integrity failure: {source}/{request["file"]}')
            key = source if source == 'opendota' else 'stratz/' + request['file'].split('/')[0]
            if 'schema' in request['file']:
                continue
            documents[key] = json.loads(body)
            refs[key] = {'source': source, 'file': file.relative_to(root.resolve()).as_posix(),
                         'sha256': request['sha256'], 'retrieved_at_utc': request['retrieved_at_utc']}
    od = documents['opendota']
    st = json.loads(json.dumps(documents['stratz/overview']['data']['match']))
    if od['match_id'] != match_id or st['id'] != match_id:
        raise ValueError('Wrong source match')
    for left,right in [('start_time','startDateTime'),('duration','durationSeconds'),('radiant_win','didRadiantWin')]:
        if od.get(left) != st.get(right):
            raise ValueError(f'Conflicting match identity: {left}')
    players = {p['playerSlot']:p for p in st['players']}
    if len(players) != 10 or len(od['players']) != 10:
        raise ValueError('Expected ten unique participants')
    for key,payload in documents.items():
        if key.startswith('stratz/') and key != 'stratz/overview':
            fragment = (payload.get('data') or {}).get('match')
            if not fragment or fragment['id'] != match_id or payload.get('errors'):
                raise ValueError('Incomplete STRATZ fragment')
            for player in fragment['players']:
                original = players[player['playerSlot']]
                if any(original.get(k) != player.get(k) for k in ('steamAccountId','heroId')):
                    raise ValueError('Fragment participant mismatch')
                original.update({k:player[k] for k in ('stats','playbackData') if k in player})
    od_players = {p['player_slot']:p for p in od['players']}
    for slot, player in players.items():
        if slot not in od_players or any(od_players[slot].get(a) != player.get(b) for a,b in [('account_id','steamAccountId'),('hero_id','heroId')]):
            raise ValueError('Participant disagreement between sources')
    if sum(p.get('steamAccountId') == account_id for p in players.values()) != 1:
        raise ValueError('Target participant missing')
    return Sources(root, match_id, account_id, od, st, documents, refs)
