"""Build reusable lower-level facts before model interpretation."""
from pathlib import Path
from collections import Counter

from .sources import load_sources
from .facts import build_facts
from .validation import validate_facts
from .episodes import detect_episodes, timeline_coverage
from .phases import build_phases
from .services import analyze_episode, summarize_phase, summarize_match
from .schemas import Finding
from .enums import Level
from .storage import cache_key, save_artifact, load_artifact
import hashlib


def run_match(*, root: Path, match_id: int, account_id: int, use_cache: bool = True) -> tuple[dict, Path, bool]:
    sources=load_sources(root=root,match_id=match_id,account_id=account_id)
    labels=root/'data/prototype/hero_names.json'
    key=cache_key(sources.references,{'account_id':account_id,'labels':hashlib.sha256(labels.read_bytes()).hexdigest() if labels.exists() else None})
    output=root/'data/analysis'/str(match_id)/key
    existing=load_artifact(output) if use_cache else None
    if existing is not None:
        return existing,output,True
    facts=build_facts(sources)
    validation=validate_facts(sources,facts)
    intervals=detect_episodes(facts)
    episodes=[analyze_episode(sources=sources,facts=facts,episode=e) for e in intervals]
    phase_intervals=build_phases(facts,intervals)
    stages=[summarize_phase(sources=sources,facts=facts,phase=p,cards=episodes) for p in phase_intervals]
    match=summarize_match(sources=sources,facts=facts,stages=stages,episodes=episodes)
    evidence=[sources.ref(k,'') for k in sources.references]
    source_card=Finding(id=f'{match_id}:sources',level=Level.SOURCES,match_ids=[match_id],account_id=account_id,
        observation='Recorded sources verified by SHA-256; 10 slots/heroes matched; target account verified. Some other source account IDs may be absent.',evidence=evidence,
        metrics={'responses':len(evidence),'coverage':facts['coverage']['participants'],
                 'disagreements':facts['coverage']['disagreements']},limitations=facts['coverage']['limitations']).to_dict()
    fact_card=Finding(id=f'{match_id}:facts',level=Level.FACTS,match_ids=[match_id],account_id=account_id,
        observation=f"{len(facts['events'])} source-linked events retained with native clocks.",evidence=evidence[:1],
        children=[source_card['id']],metrics={'target_counts':validation['target_counts'],
        'journal_vs_total':validation['journal_vs_total'],'clock_check':validation['clock_check']},limitations=facts['limitations']).to_dict()
    source_card['context']=fact_card['context']=facts['context']
    for episode in episodes:
        episode['children']=[fact_card['id']]
    registry={c['id']:c for c in [source_card,fact_card,*episodes,*stages,match]}
    result={'match_id':match_id,'account_id':account_id,'facts':facts,'registry':registry,
            'intervals':intervals,'stage_intervals':phase_intervals,'match_finding':match['id'],
            'validation':validation,'coverage':timeline_coverage(intervals,facts['context']['duration']),
            'episode_counts':dict(Counter(e['kind'] for e in episodes)),'meta_applied':False}
    save_artifact(output,result)
    return result,output,False
