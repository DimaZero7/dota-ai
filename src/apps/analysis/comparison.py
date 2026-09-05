"""Conditional descriptive frequencies, never an automatic rating of decisions."""
from collections import defaultdict
from .evidence import digest


def cohort_key(context: dict) -> tuple:
    patch=context['patch_ids']
    return (context['hero_id'],context['position'],context.get('lane'),context.get('game_mode'),
            patch.get('opendota'),patch.get('stratz'))


def measure_match(data: dict, *, horizon: int = 90) -> dict:
    if not 1<=horizon<=300:
        raise ValueError('Observation horizon must be 1..300 seconds')
    facts=data['facts']; c=facts['context']; slot=c['target_slot']
    validated=data['validation']['journal_vs_total']
    eligible=all(validated[k]['equal'] is True for k in ('kill','death'))
    kills=[e for e in facts['events'] if e['slot']==slot and e['kind']=='kill']
    deaths=[e for e in facts['events'] if e['slot']==slot and e['kind']=='death']
    windows=[]; censored=0
    if eligible:
        for kill in kills:
            if kill['time']<0 or kill['time']+horizon>c['duration']:
                censored+=1
                continue
            following=[d for d in deaths if kill['time']<d['time']<=kill['time']+horizon]
            anchors=[kill['id'],*[d['id'] for d in following]]
            episodes=[p['id'] for p in data['registry'].values() if p['level']==2 and set(anchors)&set(p.get('anchors',[]))]
            windows.append({'id':digest(anchors+[horizon])[:20],'match_id':data['match_id'],'start':kill['time'],
                            'end':kill['time']+horizon,'death_recorded':bool(following),
                            'kill_event':kill['id'],'death_events':[d['id'] for d in following],
                            'episode_ids':episodes})
    return {'match_id':data['match_id'],'finding_id':data['match_finding'],'context':c,
            'eligible':eligible,'exclusion':None if eligible else 'Kill/death journals absent or disagree with final totals.',
            'windows':windows,'censored_kills':censored,'numerator':sum(w['death_recorded'] for w in windows) if eligible else None,
            'denominator':len(windows) if eligible else None,'horizon_seconds':horizon}


def compare_matches(matches: list[dict], *, horizon: int = 90) -> dict:
    if not matches or len({m['match_id'] for m in matches})!=len(matches) or len(matches)>10:
        raise ValueError('Expected 1..10 distinct prototype matches')
    if len({m['account_id'] for m in matches})!=1:
        raise ValueError('Cannot mix players')
    rows=[measure_match(m,horizon=horizon) for m in matches]
    groups=defaultdict(list)
    excluded=[]
    for row in rows:
        c=row['context']
        if not row['eligible'] or c.get('position') in (None,'UNKNOWN','POSITION_UNKNOWN'):
            excluded.append({'match_id':row['match_id'],'reason':row['exclusion'] or 'Unknown position'})
        else:
            groups[cohort_key(c)].append(row)
    cohorts=[]
    for key,group in groups.items():
        n=sum(r['numerator'] for r in group); d=sum(r['denominator'] for r in group)
        cohorts.append({'id':'cohort:'+digest([key,horizon])[:16],'key':list(key),'matches':group,
                        'numerator':n,'denominator':d,'fraction':n/d if d else None,
                        'unit':'kill followed by a recorded own death within (0, horizon] seconds',
                        'independent_sample_size':len(group),'horizon_seconds':horizon})
    return {'account_id':matches[0]['account_id'],'match_ids':[m['match_id'] for m in matches],
            'cohorts':cohorts,'excluded':excluded,'meta_applied':False,
            'limitations':['This is a selected recent sample of at most ten games, not a population estimate.',
                'Overlapping post-kill windows are correlated; the denominator is eligible kills, not independent trials.',
                'Same hero/position/lane/mode/source patch IDs; both drafts are retained but matchup difficulty is not adjusted.',
                'Unknown rank stays unknown; match-average rank, when supplied, is not individual skill.',
                'No recorded death is not proof of safety or a good decision; a following death may be a reasonable trade.',
                'The 90-second default is an exploratory observation window, not a validated optimal timing.']}
