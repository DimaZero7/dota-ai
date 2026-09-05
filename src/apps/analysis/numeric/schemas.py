"""Versioned measurements and numeric nodes."""
import math
from copy import deepcopy

from ..evidence import digest

VERSION = 'numeric-analysis-1'
METHOD = 'numeric-1'
PARAMETERS = {'window_seconds': 60, 'phase_seconds': 600, 'snapshot_age_seconds': 5,
              'combat_gap_seconds': 15, 'post_kill_seconds': 90,
              'team_lead_band_gold': 1000, 'activity_bin_seconds': 10,
              'level_targets': [6, 12, 18, 25, 30], 'meta_applied': False}


class NumericError(ValueError):
    """Invalid, incompatible or unverifiable analysis inputs."""


def number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def divide(numerator: float | None, denominator: float | None) -> float | None:
    return numerator / denominator if number(numerator) and number(denominator) and denominator > 0 else None


def quality(*, state: str = 'value', invalid: int = 0, conflict: bool = False,
            reason: str | None = None) -> dict:
    status = 'unavailable' if state in ('missing', 'null', 'malformed', 'deferred') else 'conflicting' if conflict or invalid else 'observed'
    return {'status': status, 'field_state': state, 'invalid_events': invalid,
            'eligible': status == 'observed', 'reason': reason,
            'completeness': 'not independently established', 'observed_empty': state == 'empty',
            'temporal_coverage_seconds': None}


def measurement(id: str, value: object, unit: str, *, kind: str = 'derived',
                q: dict | None = None, numerator: object = None, denominator: object = None,
                provenance: list | None = None, details: dict | None = None) -> dict:
    q = deepcopy(q or quality())
    return {'metric_id': id, 'method_version': '1', 'implementation_version': METHOD, 'value': value, 'unit': unit,
            'kind': kind, 'numerator': numerator, 'denominator': denominator,
            'quality_status': q['status'], 'coverage': q,
            'uncertainty': {'status': 'not_estimated', 'reason': 'source coverage/semantics; no statistical confidence claim'},
            'provenance_ref': provenance or [], 'details': details or {}}


def point_quality(valid: int, count: int) -> dict:
    q=quality(state='value' if valid else 'missing',reason=None if valid==count else 'missing or stale required snapshots')
    if 0<valid<count:q.update(status='partial',eligible=False)
    q.update(observed_points=valid,requested_points=count)
    return q


def node(*, level: int, context: dict, measurements: list, source_manifest: dict,
         children: list[dict], payload: dict | None = None) -> dict:
    for child in children:
        validate_node(child)
        if child['level'] != level - 1 or child['scope']['match_id'] != context['match_id'] or child['scope']['account_id'] != context['account_id']:
            raise NumericError('Immediate lower level and same participant/match required')
    data = {'schema_version': VERSION, 'id': f"{context['match_id']}:{context['account_id']}:numeric:L{level}",
            'level': level, 'scope': {k: context[k] for k in ('match_id', 'account_id', 'target_slot')},
            'as_of': max((r.get('retrieved_at_utc', '') for r in source_manifest.values()), default=''),
            'context_summary': {k: context[k] for k in ('hero_id', 'position', 'duration', 'meta_applied')},
            'context_ref': digest(context), 'source_manifest_ref': digest(source_manifest),
            'method_versions': {'numeric': METHOD}, 'parameter_hash': digest(PARAMETERS),
            'children_manifest_ref': {c['id']: c['revision'] for c in children},
            'measurements': measurements, 'interpretations': [],
            'drill_index_ref': f"{context['match_id']}:{context['account_id']}:numeric:L2",
            'omitted': {'groups': 0, 'features': 0, 'examples': 0, 'reason': None}, **(payload or {})}
    data['revision'] = digest(data)
    return data


def validate_node(data: dict) -> None:
    if data.get('schema_version') != VERSION or data.get('method_versions', {}).get('numeric') != METHOD:
        raise NumericError('Incompatible numeric version')
    if data.get('parameter_hash') != digest(PARAMETERS):
        raise NumericError('Incompatible numeric parameters')
    if data.get('revision') != digest({k: v for k, v in data.items() if k != 'revision'}):
        raise NumericError('Numeric node integrity failure')


def measures(data: dict) -> dict:
    return {m['metric_id']: m for m in data['measurements']}
