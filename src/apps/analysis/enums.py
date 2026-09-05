from enum import IntEnum, StrEnum


class Level(IntEnum):
    SOURCES = 0
    FACTS = 1
    EPISODES = 2
    PHASES = 3
    MATCH = 4
    PATTERNS = 5
    PROFILE = 6


class Support(StrEnum):
    OBSERVED = "observed"
    HYPOTHESIS = "hypothesis"
    INSUFFICIENT = "insufficient_data"


RULES_VERSION = "prototype-1"
META_POLICY = "disabled"
