"""Chronology of the observed sample; session boundaries are an explicit proxy."""
from collections import Counter
from datetime import datetime, timezone

from ..numeric.schemas import number
from .schemas import CORE_CONTEXT, LongitudinalError
from .statistics import describe


def chronology(rows: list[dict], *, gap_minutes: int = 60, known_gaps: set[tuple[int,int]] | None = None) -> dict:
    if gap_minutes not in (30,60,90):raise LongitudinalError('Session threshold must be 30, 60 or 90 minutes')
    known_gaps=known_gaps or set();ids=[r['match_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise LongitudinalError('Duplicate match in chronology')
    ordered=sorted(rows,key=lambda r:(not number(r['start_time']),r['start_time'] if number(r['start_time']) else 0,r['match_id']))
    sessions=[];items=[];transitions=[];runs=[];previous=None;ordinal=0
    for row in ordered:
        time=row['start_time'];gap=None;reason='sample_start'
        if previous:
            if not number(time) or not number(previous['start_time']):reason='unknown_clock'
            else:
                gap=time-previous['start_time']-previous['duration']
                reason='overlapping_match_times' if gap<0 else 'known_missing_history' if (previous['match_id'],row['match_id']) in known_gaps else 'break_threshold' if gap>gap_minutes*60 else 'within_threshold'
        if not previous or reason!='within_threshold':
            ordinal=0;sessions.append({'id':f"session:{row['match_id']}",'match_ids':[],'boundary_reason':reason})
        ordinal+=1;session=sessions[-1];session['match_ids'].append(row['match_id'])
        item={'match_id':row['match_id'],'start_time':time,'gap_seconds':gap,'session_id':session['id'],
              'observed_ordinal':ordinal,'boundary_reason':reason,'actual_continuity_verified':False,
              'utc_day':datetime.fromtimestamp(time,timezone.utc).date().isoformat() if number(time) else None}
        items.append(item)
        linked=previous is not None and reason not in ('unknown_clock','known_missing_history','overlapping_match_times')
        if linked and type(row['win']) is bool and type(previous['win']) is bool:
            same=all(row['context'].get(k) is not None and row['context'].get(k)==previous['context'].get(k) for k in (*CORE_CONTEXT,'duration_band'))
            changes={}
            for key in ('xp_rate','gold_rate','death_fraction','participation'):
                a=previous['metrics'].get(key);b=row['metrics'].get(key)
                changes[key]=b['value']-a['value'] if same and a and b and a['eligible'] and b['eligible'] else None
            transitions.append({'previous':previous['match_id'],'current':row['match_id'],'after_win':previous['win'],'win':row['win'],
                                'within_estimated_session':reason=='within_threshold','same_comparison_context':same,
                                'hero_changed':row['context'].get('hero_id')!=previous['context'].get('hero_id'),
                                'role_changed':row['context'].get('position')!=previous['context'].get('position') if row['context'].get('position') is not None and previous['context'].get('position') is not None else None,
                                'behavior_changes':changes,'gap_seconds':gap})
        if type(row['win']) is bool:
            if linked and runs and runs[-1]['win']==row['win']:runs[-1]['match_ids'].append(row['match_id'])
            else:runs.append({'win':row['win'],'match_ids':[row['match_id']],'start_observed':True})
        else:runs.append({'win':None,'match_ids':[row['match_id']],'start_observed':True})
        previous=row
    after={}
    for outcome in (True,False):
        subset=[t for t in transitions if t['after_win']==outcome]
        after['win' if outcome else 'loss']={'n':len(subset),'wins':sum(t['win'] for t in subset),
                'win_fraction':sum(t['win'] for t in subset)/len(subset) if subset else None,
                'within_session_n':sum(t['within_estimated_session'] for t in subset),
                'hero_changes':sum(t['hero_changed'] for t in subset),'role_changes':sum(t['role_changed'] is True for t in subset),
                'role_change_unknown':sum(t['role_changed'] is None for t in subset),
                'behavior_changes':{key:describe([t['behavior_changes'][key] for t in subset]) for key in ('xp_rate','gold_rate','death_fraction','participation')}}
    by_id={r['match_id']:r for r in rows};by_order={}
    for order in sorted({i['observed_ordinal'] for i in items}):
        group=[by_id[i['match_id']] for i in items if i['observed_ordinal']==order]
        by_order[str(order)]={'n':len(group),'wins':sum(r['win'] is True for r in group),
            'metrics':{k:describe([r['metrics'][k]['value'] if r['metrics'].get(k) and r['metrics'][k]['eligible'] else None for r in group]) for k in ('xp_rate','gold_rate','death_fraction','participation')},
            'comparison':'mixed-context description; not an ordinal/session effect'}
    summary={'estimated_sessions':len(sessions),'session_sizes':dict(sorted(Counter(str(len(s['match_ids'])) for s in sessions).items())),
             'by_observed_order':by_order,
             'observed_order_counts':dict(sorted(Counter(str(i['observed_ordinal']) for i in items).items())),
             'max_observed_win_run':max((len(r['match_ids']) for r in runs if r['win'] is True),default=0),
             'max_observed_loss_run':max((len(r['match_ids']) for r in runs if r['win'] is False),default=0),
             'run_lengths':{'win':describe([len(r['match_ids']) for r in runs if r['win'] is True]),
                            'loss':describe([len(r['match_ids']) for r in runs if r['win'] is False])},
             'after_result':after,'history_complete':False,'left_censored':True,'right_censored':True,
             'limitations':['selected-history adjacency only; missing games may break every link',
                            'session threshold is not factual uninterrupted play','no fatigue or tilt inference',
                            'behavior deltas require the same comparison context; outcome alone is not behavior']}
    return {'rule_version':'end-to-start-gap-1','gap_minutes':gap_minutes,'summary':summary,
            'items':items,'sessions':sessions,'transitions':transitions,'runs':runs}


def sensitivity(rows: list[dict], *, known_gaps: set[tuple[int,int]] | None = None) -> list[dict]:
    return [{'gap_minutes':gap,**chronology(rows,gap_minutes=gap,known_gaps=known_gaps)['summary']} for gap in (30,60,90)]
