# Analysis level contracts

Status: task 3 prototype implementation. Meta evaluation is disabled. Patch identifiers are provenance only; no hero strength, build norms, or meta rankings are applied.

| Level | Input | Output | Execution |
| --- | --- | --- | --- |
| 0 | Recorded responses and hashes | Verified sources, participants, coverage | Code |
| 1 | Level 0 | Events and measurements with time, units, actor, evidence | Code |
| 2 | Selected facts and interval | Episode cards and bounded hypotheses | Code; model interpretation via context packets |
| 3 | Episodes and facts | Stages with explicit boundaries, no double counting | Code and interpretation |
| 4 | Stages and final statistics | Match findings and testable recommendations | Code and interpretation |
| 5 | Multiple matches | Conditional patterns and counterexamples | Code and interpretation |
| 6 | Patterns | Preliminary profile and progress criteria | Code and interpretation |

Hero, source-reported position, observed lane, and both drafts are mandatory match/episode context. STRATZ position is an estimate, not proof of an obligation. Draft alone does not establish a correct action or ability availability. Hero/position cohorts are separated; draft differences limit comparability.

Findings retain observed/hypothesis/insufficient_data status, observations, hypotheses, evidence, alternatives, limitations, and verification steps. Aggregation inherits child limitations. Model packets select question-specific fields and time intervals; complete API dumps are not the context. Seven levels do not require seven agents or seven model calls.
