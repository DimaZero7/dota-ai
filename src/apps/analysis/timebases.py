"""Explicit clock contracts; no undocumented coordinate conversion."""
from .sources import Sources


def clock_report(sources: Sources) -> dict:
    target_od = next(p for p in sources.opendota['players'] if p.get('account_id') == sources.account_id)
    target_st = next(p for p in sources.stratz['players'] if p.get('steamAccountId') == sources.account_id)
    od_kills = [e['time'] for e in target_od.get('kills_log', [])]
    st_kills = [e['time'] for e in (target_st.get('playbackData') or {}).get('killEvents', [])]
    times = target_od.get('times', [])
    return {'event_time_unit':'seconds_from_match_start', 'pregame_retained':True,
            'duration':sources.stratz['durationSeconds'],
            'target_kill_times':{'opendota':od_kills,'stratz':st_kills,
                                 'exact_multiset_match':sorted(od_kills)==sorted(st_kills),
                                 'paired_offsets_seconds': [a-b for a,b in zip(sorted(od_kills),sorted(st_kills))] if len(od_kills)==len(st_kills) else None},
            'opendota_series':{'times':times,'gold_t':'source cumulative series, not net worth',
                               'xp_t':'source cumulative series', 'net_worth':'final snapshot'},
            'stratz_series':'Preserve field/index; do not align implicitly with OpenDota times.',
            'coordinates':{'stratz':'native x/y units; world-unit conversion not established',
                           'opendota':'native lane_pos histogram; not a movement timeline'},
            'limitations':['Event clock alignment checked on target kill events only.',
                           'Coordinate labels and regions are not treated as validated map semantics.']}


def in_interval(time: float, start: float, end: float) -> bool:
    """Half-open intervals prevent counting boundary events twice."""
    return start <= time < end
