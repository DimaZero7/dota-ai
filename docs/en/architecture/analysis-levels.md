# Analysis level contracts

Status: implemented local task 3 prototype, checked on five matches. Meta evaluation is disabled. Patch identifiers are provenance only; no hero strength, build norms, or meta rankings are applied.

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

## Implemented contracts

`Finding` includes `id`, `level`, `match_ids`, `account_id`, `observation`, `hypothesis`, `support`, `interval`, `evidence`, `children`, `alternatives`, `counterexamples`, `limitations`, `verify`, `metrics`, and `rules_version`. Validation checks required evidence, hypothesis/status compatibility and intervals. Match context adds hero, estimated position, lane, ten participants, time, patch and journal availability.

Normalized events contain `id`, `kind`, `time`, `slot`, `document`, `pointer`, and `data`. Evidence references carry a relative original-response path, source, SHA-256, JSON pointer and retrieval time. Event IDs are deterministic within a snapshot; evidence and artifact keys identify the exact data version. OpenDota and STRATZ retain native clocks, coordinates and semantics. Unknown values are not replaced with zero.

Cards form a descending graph: profile → patterns → matches → stages → episodes → facts → sources. Cache and source responses are separate from model interpretations. Upper levels aggregate structured facts and limitations; prior model prose does not become established evidence. Actual interpretations at each level are saved separately.

Level 2 selects death, OpenDota fight, purchase, objective, last-hit sequence, kill and quiet control windows. These are review candidates. Missing target playback produces an explicit insufficient-data card. Missing objective journals are not replaced with invented strategic stages.

The cross-match prototype hypothesis measures an own death within `(0, 90]` seconds after a kill. The denominator includes kills with complete future observation windows and kill/death journals checked against totals. End-censored windows are excluded. Cohorts separate hero, position, lane, mode and source-specific patch ID pairs. Drafts and available rank context accompany comparison but do not adjust difficulty.

One compatible game is `single_match`; two or more within the prototype are `preliminary`. Stable style is never assigned automatically: independent prospective evidence and review of alternatives are required. Overlapping windows are correlated; distinct deaths are counted separately. Profiles retain conditions, hypotheses, a training baseline and `untested` until follow-up. No psychological labels are generated.

[Commands, model budget and history](../development/analysis.md) · [Examples and usefulness review](../development/prototype-examples.md)
