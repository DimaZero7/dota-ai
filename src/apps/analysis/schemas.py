"""Serializable contracts with explicit uncertainty and provenance."""
from dataclasses import asdict, dataclass, field
from typing import Any

from .enums import Level, Support, RULES_VERSION


@dataclass(frozen=True)
class Finding:
    id: str
    level: Level
    match_ids: list[int]
    account_id: int
    observation: str
    evidence: list[dict]
    support: Support = Support.OBSERVED
    hypothesis: str | None = None
    interval: tuple[float, float] | None = None
    children: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    counterexamples: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    verify: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    rules_version: str = RULES_VERSION

    def __post_init__(self) -> None:
        if not self.id or not self.match_ids or self.account_id <= 0:
            raise ValueError('Finding requires identity and match context')
        Level(self.level)
        Support(self.support)
        if self.support == Support.OBSERVED and self.hypothesis:
            raise ValueError('A hypothesis cannot be labeled observed')
        if self.support == Support.HYPOTHESIS and not self.hypothesis:
            raise ValueError('Hypothesis text required')
        if not self.evidence and not self.children and self.support != Support.INSUFFICIENT:
            raise ValueError('Evidence or child findings required')
        if self.support == Support.INSUFFICIENT and not self.limitations:
            raise ValueError('Explain insufficient evidence')
        if self.interval and self.interval[0] > self.interval[1]:
            raise ValueError('Reversed interval')

    def to_dict(self) -> dict:
        return asdict(self)


def inherit_limits(children: list[dict], own: list[str] | None = None) -> list[str]:
    return sorted(set(own or []) | {v for c in children for v in c.get('limitations', [])})
