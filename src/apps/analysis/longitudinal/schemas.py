"""Versioned compact match signatures and cross-match outputs."""
from ..evidence import digest
from ..numeric.schemas import number

VERSION='longitudinal-analysis-1'
PARAMETERS={'session_gap_minutes':60,'session_sensitivity_minutes':[30,60,90],
            'repeat_death_seconds':120,'minimum_group':5,'minimum_days':8,
            'discovery_fraction':.7,'permutations':999,'max_permutations':199999,'alpha':.05,
            'rank_band_width':10,'duration_band_seconds':600,'contrast_xp_band':250,'contrast_damage_band':500,
            'minimum_spatial_coverage':.8,'minimum_spatial_seconds':60,'meta_applied':False}
CORE_CONTEXT=('hero_id','position','mode','side','stratz_version','opendota_version','rank_band')


class LongitudinalError(ValueError):
    """Incompatible or incomplete inputs to an explicitly requested analysis."""


def signed(data: dict) -> dict:
    clean={k:v for k,v in data.items() if k!='revision'}
    return {**clean,'revision':digest(clean)}


def validate(data: dict, level: int | None = None) -> None:
    if data.get('schema_version')!=VERSION or data.get('revision')!=signed(data)['revision']:
        raise LongitudinalError('Longitudinal version/integrity failure')
    if level is not None and data.get('level')!=level:raise LongitudinalError('Incorrect longitudinal level')


def measure(value: float | None, *, unit: str, numerator: float | None = None,
            denominator: float | None = None, scale: float = 1, eligible: bool = True,
            reason: str | None = None) -> dict:
    return {'value':value if number(value) else None,'numerator':numerator if number(numerator) else None,
            'denominator':denominator if number(denominator) else None,'scale':scale,
            'unit':unit,'eligible':eligible and number(value),'reason':reason}
