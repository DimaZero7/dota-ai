"""Question-level acceptance checks against recorded evidence."""
from .sources import Sources
from .evidence import resolve


def evaluate_lower_levels(data: dict, sources: Sources) -> dict:
    target=next(p for p in sources.stratz['players'] if p['steamAccountId']==sources.account_id)
    slot=target['playerSlot']
    raw=target.get('playbackData') or {}
    phases=[c for c in data['registry'].values() if c['level']==3]
    match=data['registry'][data['match_finding']]
    checks=[
        ('Do both drafts retain all participants?',len(data['facts']['context']['roster'])==10),
        ('Do stages count deaths once?',sum(p['metrics']['counts'].get('death',0) or 0 for p in phases)==len(raw.get('deathEvents') or [])),
        ('Do stages preserve observed last hits?',sum(p['metrics']['counts'].get('last_hit',0) or 0 for p in phases)==len(raw.get('csEvents') or [])),
        ('Do unavailable deaths remain unknown?',bool(raw.get('deathEvents') is not None) or match['metrics']['death_journal_count'] is None),
        ('Are native clock disagreements explicit?',data['validation']['clock_check']==data['facts']['clocks']['target_kill_times']),
        ('Does every card preserve limits?',all(bool(c.get('limitations')) for c in data['registry'].values())),
        ('Is meta disabled?',not data['facts']['context']['meta_applied']),
    ]
    first=raw.get('deathEvents') or []
    if first:
        ref=sources.ref(f'stratz/playback-{slot}','/data/match/players/0/playbackData/deathEvents/0')
        checks.append(('Can the first death be verified in the raw response?',resolve(root=sources.root,ref=ref)==first[0]))
    failed=[question for question,passed in checks if not passed]
    return {'checks':[{'question':q,'passed':p} for q,p in checks], 'failed':failed,
            'model_evaluation':'Compare saved packet/review pairs with sources and user feedback; schema checks alone do not establish semantic quality.',
            'limitations':['Current-session review is not blind: the assistant has also inspected source evidence.',
                           'No quantitative claims of improved model accuracy or token savings are established by this test.']}


def verify_trace(registry: dict, start_id: str) -> dict:
    visited=set()
    def walk(node_id: str, ancestors: set) -> None:
        if node_id in ancestors:
            raise ValueError('Cyclic evidence graph')
        node=registry[node_id]
        visited.add(node_id)
        for child_id in node.get('children',[]):
            child=registry[child_id]
            if child['level']>=node['level']:
                raise ValueError('Evidence graph does not descend')
            if not set(child.get('limitations',[]))<=set(node.get('limitations',[])):
                # Source coverage cards contain general ingestion limits; these are checked separately.
                if child['level']>0:
                    raise ValueError('Child limitation lost')
            walk(child_id,ancestors|{node_id})
    walk(start_id,set())
    return {'start':start_id,'visited_nodes':len(visited),'levels':sorted({registry[k]['level'] for k in visited})}
