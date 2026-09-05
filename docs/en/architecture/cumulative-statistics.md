# Cumulative statistics: catalogue and contracts

[Architecture](README.md) · [Running version contracts](analysis-levels.md) · [Русский](../../ru/architecture/cumulative-statistics.md)

Status: **task 4 design complete**. An offline audit of ten saved matches was performed. This document specifies the design to implement in tasks 5–10. At task 4 completion the engine was a design. Tasks 5–9 are now implemented, including [numeric L1–L4](../development/numeric-analysis.md), [incremental storage](../development/cumulative-analysis.md) and [profile updates](../development/analyst-analysis.md). The earlier task 3 example retains authored responses at L2–L6.

L0–L4 primarily collect and calculate. L5 produces conditional numerical summaries and the analyst connects patterns. L6 explains playing style, specific characteristics and development priorities. Prose at every lower level is not a mandatory intermediate product. A number needs a meaningful, verifiable definition; it does not assign a personality trait.

## Audit findings

The [reproducible audit](../../../data/prototype/statistics-audit.json) covers **137 field paths**, ten matches and original OpenDota/STRATZ responses. Source sizes, SHA-256, match identity and participants are checked. `states_by_match` retains values, zero, false, empty collections, null and absent keys; multiple states can occur in one journal. `matches_with_numeric_or_value` means at least one value exists, not complete coverage. Player-field auditing targets this player; separate counters check that all ten participants have position/economy data.

| Observation | Catalogue decision |
| --- | --- |
| STRATZ movement and economy journals exist for all 100 participants across ten matches | Team differences and spatial features can be designed; temporal coverage still needs measurement |
| No OD/ST disagreements in 11 final statistics across all 100 participants | Use final KDA, GPM, XPM, damage etc. separately from event sums |
| Target death counts reconcile in 10/10, kills in 9/10, assists in 3/10, last hits in 9/10 | Eligibility belongs to a metric. Assist discrepancies do not remove a match from XP/death statistics |
| XP journals exist in 10/10; match 8955721990 has 64,400 recorded XP versus `1185 XPM × 3748 / 60 = 74,023` | Measure **recorded XP**, not necessarily all earned XP. The discrepancy is unresolved; level-cap mechanics are not inferred |
| Sum of `timeDead` is 551 versus OD `life_state_dead=552` in one parsed match and 91 versus 90 in the other | Treat death intervals as source-based estimates, not exact absence or avoidable loss |
| OD objectives, teamfights, XP timelines and ward lifecycles exist in only 2/10 | Additional validation and limited features, not a mandatory input for the entire sample |
| `stats.wards` and `wardDestruction` have entries in 8/10, empty lists in 2/10, no nulls | Zero recorded events is possible; effective vision is not measured. Type-code mapping requires verification |
| `inventoryEvents` contains only one initial event at −89 seconds in every match | Item availability at an arbitrary time cannot be reconstructed. Purchase and use remain separate observations |
| Maximum target position-observation gaps range from 15 to 105 seconds by match | Event density is not occupancy time. Explicit gap handling and temporal coverage are required |
| OD `average_rank` and ST `averageRank` are absent/null in 10/10; ST `rank` is populated | Preserve STRATZ rank with provenance, not as verified individual match-time rank |
| STRATZ `isStats=false` in two matches despite existing journals | Inspect actual fields rather than rejecting analysis based on this flag |

A field in the saved GraphQL schema does not establish that it was requested or returned. The catalogue uses actual original response values. Many saved schema descriptions are empty: disputed flags, minute-array indexing, object types and coordinate systems need validation before interpretation. Request metadata and schemas remain in source snapshots. Chat messages and other players' profiles are outside this catalogue.

## Catalogue and metric passports

The shared [machine-readable catalogue](../../contracts/statistics-catalog.json) contains **46 passports: 26 core, 15 additional, 5 candidate**, with bilingual names. `core` defines required future engine scope, not guaranteed availability for every match. `additional` uses existing fields but may need semantic validation. `candidate` is blocked by missing data or an unverified definition; it does not authorize automatically adding another provider.

Each passport consists of its entry plus `passport_defaults`: stable ID and method version, definition/formula, units, numerator/denominator, window, source through `audit_fields`, comparison context, level, dependencies, limits, validation, coverage and retained state. `depends_on` describes computational lineage. The exchange contract also forwards required base numbers through immediate children; it does not permit L6 to read raw journals.

| ID | Metric | Level | Tier | Kind |
| --- | --- | --- | --- | --- |
| `context.match` | Match context | L1 | Core | Observation |
| `economy.networth` | Net worth snapshot | L1 | Core | Observation |
| `space.observations` | Coordinate observations | L1 | Core | Observation |
| `economy.gold_flow` | Gold flow by reason | L2 | Core | Observation |
| `xp.gain` | Recorded XP by reason | L2 | Core | Observation |
| `xp.level_time` | Level attainment time | L2 | Core | Observation |
| `farm.last_hits` | Last hits by source | L2 | Core | Observation |
| `death.count` | Death count | L2 | Core | Observation |
| `death.reported_time` | Reported death time | L2 | Core | Proxy |
| `combat.participation` | Team kill participation | L4 | Core | Observation |
| `combat.damage` | Recorded hero damage | L2 | Additional | Observation |
| `support.healing` | Recorded healing by recipient | L2 | Additional | Observation |
| `items.purchase_time` | First recorded item purchase | L2 | Core | Observation |
| `items.use_count` | Item use counts | L2 | Additional | Observation |
| `abilities.use_count` | Ability use counts | L2 | Additional | Observation |
| `vision.placements` | Recorded ward placements | L2 | Additional | Observation |
| `vision.destructions` | Recorded ward destruction | L2 | Additional | Observation |
| `support.actions` | Stacks and support actions | L3 | Additional | Proxy |
| `objectives.destroyed` | Building destructions | L2 | Additional | Observation |
| `economy.team_state` | Team economic state | L2 | Core | Observation |
| `episodes.post_kill_death` | Death after a recorded kill | L2 | Additional | Observation |
| `episodes.return_activity` | Return to recorded activity | L2 | Additional | Proxy |
| `xp.phase_rate` | Phase recorded-XP rate | L3 | Core | Observation |
| `economy.phase_flow` | Phase gold flow and net-worth change | L3 | Core | Observation |
| `death.phase_fraction` | Phase reported-death fraction | L3 | Core | Proxy |
| `farm.phase_rate` | Phase farming rate | L3 | Core | Observation |
| `space.isolation` | Distance to nearest ally | L2 | Additional | Proxy |
| `space.occupancy` | Observed-time grid distribution | L3 | Additional | Proxy |
| `transition.lead_change` | Team lead transitions | L3 | Core | Observation |
| `match.trajectory` | Numeric match trajectory | L4 | Core | Observation |
| `match.resource_share` | Team resource shares | L4 | Core | Observation |
| `match.conversion` | Combat-to-objective adjacency | L4 | Additional | Proxy |
| `match.space_distribution` | Match spatial distribution | L4 | Additional | Proxy |
| `sessions.match_context` | Match position in observed session | L4 | Core | Proxy |
| `distance.distribution` | Conditional metric distributions | L5 | Core | Observation |
| `distance.association` | Conditional outcome associations | L5 | Core | Observation |
| `distance.session_effect` | Within-session and streak changes | L5 | Core | Proxy |
| `distance.trend` | Longitudinal change and stability | L5 | Core | Observation |
| `distance.spatial` | Conditional spatial differences | L5 | Additional | Proxy |
| `profile.hypotheses` | Profile and testable hypotheses | L6 | Core | Interpretation |
| `profile.delta` | Profile update delta | L6 | Core | Interpretation |
| `abilities.opportunity` | Available cast opportunities | L2 | Blocked | Undefined |
| `vision.effective` | Effective visibility | L3 | Blocked | Undefined |
| `space.semantic_regions` | Semantic map regions | L3 | Blocked | Undefined |
| `context.draft_strength` | Draft strength and requirements | L5 | Blocked | Undefined |
| `profile.psychological_cause` | Behavioural causes and psychological labels | L6 | Blocked | Undefined |

Calculation rules:

- Windows are half-open `[a,b)`. An integer-timestamp final event can use an upper bound of `duration+1`; exposure remains `duration` seconds.
- Base phases are ten-minute bins clipped at match end. These are time bins, not automatically recognized strategic phases. A phase after match end is absent, not zero.
- Economy snapshots must be at most five seconds old. Team difference requires ten fresh values. Missing values break sequences and cannot become apparent lead transitions.
- Estimated death time is the union of `[time,time+timeDead)` intervals clipped to match and phase. It remains a proxy, especially with buybacks. The original sum of `timeDead` is stored separately for reconciliation.
- Every metric retains its own eligible, missing, conflicting, censored, observed-empty and temporal-coverage counts plus exclusion reasons. Conflict may coexist with a measured value; `quality_status` determines comparison eligibility. Missing or zero denominators produce null.
- The mean of individual ratios differs from the pooled numerator/denominator ratio. Both underlying quantities must be retained and the aggregation method named.
- Method, threshold parameters, source clock, grouping/grid version and source revision are provenance. Five seconds, 90/120 seconds, 1,000 gold and 20 matches are prototype parameters, not established laws of the game.

## What each level creates

| Level | New information | Compact upward output | Retained outside model context |
| --- | --- | --- | --- |
| L0 — sources | Identity, availability, conflicts and provenance | Source/quality manifest | Original responses, requests, schemas and hashes |
| L1 — facts | Typed events/snapshots and complete participant context | Numeric records with clocks, units and quality | Full journals and event index |
| L2 — windows/episodes | XP/gold by reason, death intervals, purchases/actions, conditional windows and censoring | Numerators, denominators, durations, states and a few drill keys | Window event membership and exceptional annotations |
| L3 — phases | Rates, time fractions, distributions, team-state changes and spatial coverage | Phase vectors and distribution statistics with distinct sources | Detailed timelines and local windows |
| L4 — match | Phase trajectory, resource shares, context row and position in observed chronology | Bounded numeric match row; complete drafts in a context dictionary | All phases, windows and provenance |
| L5 — history | Conditional/joint distributions, trends, sessions, counterexamples and changes | Condition groups, sample sizes, effects/uncertainty and hypothesis history | Match rows, contributions and cohort/counterexample indices |
| L6 — profile | Evidence/limits linked into a portrait, priorities and testable experiments | Personal explanation and profile change, referencing L5 groups | Claim revisions and addressable examples |

L5 combines calculation and interpretation: code supplies distributions and associations; current Codex judges their meaning, contradictions and missing evidence. L6 explains the result to the player. Ordinary ingestion does not require model answers at L2–L4.

Base values that do not become new metrics at an intermediate level pass through as compact numeric context with provenance, such as final kills/assists needed at L4. Journals do not pass through. Child references may point to a hashed manifest in storage instead of listing thousands of IDs in a model packet.

## Five derivation chains

| Family | L1 → L2 | L3 → L4 | L5 → L6 |
| --- | --- | --- | --- |
| XP | XP/level events → recorded XP by reason and level times | Phase XP rate → development trajectory for hero/position | Conditional distributions and rate changes → development hypothesis with XP-completeness caveat |
| Deaths | Time/`timeDead` → death windows and return to recorded activity | Phase death fractions → placement along match trajectory | Association with initial advantage/outcome and stability → decision-review priority, not automatic error attribution |
| Resources | Economy snapshots/flows → personal/team differences | Rates/transitions → resource share and trajectory | Conditional association with participation/objects → resource-use hypothesis, not a judgement from GPM alone |
| Space | Coordinates → distances with temporal coverage | Observed-time grid → match distribution by phase | Role/state differences → movement hypothesis; named regions only after map validation |
| Sessions | Match time/result → gameplay-window durations | Covered phases → compact row, UTC gap, session ordinal | Adjacent-game and previous-result changes → hypothesis about play scheduling, not fatigue/tilt attribution |

Session relationships emerge only after comparing completed match rows at L4. An event cannot contain information about a future game. The prototype session boundary is a gap greater than 60 minutes from previous end to next start, with sensitivity checks at 30/90 minutes. The first sample boundary is censored; missing history breaks verified adjacency. A list of recent ranked matches does not establish the absence of other games in between.

## Exchange contract

The proposed `numeric-analysis-1` format does not automatically replace existing files. Required envelope:

```text
schema_version, id, revision, level, scope, as_of
context_ref, context_summary, method_versions, parameter_hash
source_manifest_ref, children_manifest_ref
measurements[{metric_id, method_version, value, unit, numerator, denominator,
              coverage, quality_status, uncertainty, provenance_ref}]
interpretations[]
drill_index_ref, omitted{groups, features, examples, reason}
```

`scope` is account/match/slot/window at L1–L4, account/cohort/window at L5 and account/profile revision at L6. `value` may be a number, vector or passport-defined record. `coverage` includes eligible match/event counts and known time. `uncertainty` records a method, bounds/description and why an estimate is unavailable. An absent confidence interval does not mean zero uncertainty. Until a statistical method is selected and validated in task 7, results are descriptive, not declared significant.

`interpretations=[]` is valid at L1–L4. L5/L6 annotations contain claim ID, observation/interpretation/hypothesis type, scope, supporting/opposing groups, alternatives, limits, next check, analyst version and dependencies. L6 also supplies 1–3 priorities with action, baseline measurement, expected observable change and revision criteria.

An L6 packet carries selected L5 groups and previous claims, not a match list. Prototype budget: up to 32,000 UTF-8 input bytes, 16,000 reserved answer bytes, and up to 8,000 total drill bytes over three calls. Bytes are not a guaranteed token count. Task 9 must measure serialized size, expose omissions and reject silent truncation of required evidence. The main report never depends on an unstated memory of the other matches.

## Grouping and inference limits

Base comparisons retain hero, estimated position, mode, phase and known source/map versions, plus observed lane, side, both drafts, initial team difference and rank provenance. Phase analysis uses conditions **before** that phase; final state must not masquerade as a previously known factor. OD/ST patch IDs have separate namespaces and must not be equated numerically. Meta is disabled.

Full drafts remain addressable. For sparse exact groups, show size first; broader comparisons state which dimensions were dropped and the new composition. For example, same hero/position with different drafts and same position with different heroes are separate results. Unknown position/rank/side is not merged into a confirmed group. Roles and heroes are not collapsed into one player judgement without sample composition.

Prototype rule: `n<5` supports description only; if any compared outcome cell has fewer than five matches, do not claim a stable association. This is a minimum filter, not sufficient proof at `n>=5`. The current 9W/1L sample cannot establish a reliable relationship with win probability. Track tested hypotheses, adjacent-game dependence, group-composition changes and chronological validation data. Correlation of final statistics with victory establishes neither cause nor predictive validity.

## Updates without rereading old matches

Each passport's `retention` specifies sums, joint records, compact match rows, timelines, intervals, grids, chronology, original sources or claim versions. These requirements define the limits of the “1000 + 10” promise.

1. Existing features retain numeric per-match rows and aggregate contributions. Ten new matches pass through L0–L4, update affected L5 groups, and create an L6 change packet. The analyst does not read the previous thousand games.
2. Sums suffice for means/variance and predefined proportions. Exact median/IQR, a new split or an unanticipated relationship cannot be recovered from means alone. Compact rows and joint data support these operations. Code reading compact rows is acceptable and differs from the model reading raw match events.
3. A corrected/refetched match replaces its contribution by account/match/method/source revision instead of adding it again. Aggregates and contribution ledger update atomically. Duplicates leave counts unchanged.
4. Chronological appends use the previous end, result, run length, ordinal and verified boundary state. Backdated inserts/time corrections recompute affected sessions until the next verified boundary; a long result run may affect the entire remaining compact chronological suffix.
5. Changed formulas, grids, clocks, event semantics or missing new features require targeted recomputation. If compact data is insufficient, code reads required older timelines/sources. Historical coverage remains explicitly incomplete until backfill. Lost information cannot be recovered from old profile prose.
6. Every ingestion changes applicable numbers or coverage. The analyst revisits affected claims only; stable wording may remain. Record that evidence did not justify a text change instead of artificially modifying the player's character after every game.

Upper levels use condition names and aggregates: “Jakiro, position 2, four matches, duration 37:41–62:28.” “Against Arc” belongs only inside a drilled example with match ID, date, hero, position and link. Limitations must also be expressed at group scope.

## When a model is needed below L5

Exceptions include inspecting an episode behind contradictory numeric signals, a specific moment requested by the user, or testing a new hypothesis and counterexample. Supply a bounded window, observed conditions and a precise question. Do not review every episode as a precaution.

Cache the annotation by hashes of source facts, method, window, question, rules and analyst version. Retain its structured conclusion, support, alternatives and unknowns. Revised dependencies make it stale. Such an assessment does not become an exact number without a separately defined and validated metric. “X seconds to the next recorded attack” can be a proxy; “the player recklessly wasted X seconds” requires evidence that this measurement does not provide.

## Example from numbers to profile

This is a **contract example using real data**, not a new complete portrait or proof of a stable pattern. The audit stores original references and computed examples for four Jakiro games at estimated position 2:

| Drill match ID | L3 deaths per ten-minute phase | L4 union of reported death intervals / duration | Recorded XP before 10:00 |
| --- | --- | --- | --- |
| 8959040566 | 2, 1, 0, 0 | 91 / 2261 s = 4.0% | 4744 |
| 8958839199 | 0, 2, 3, 1, 0 | 275 / 2744 s = 10.0% | 4673 |
| 8957325148 | 1, 3, 1, 1, 0 | 327 / 2450 s = 13.3% | 6654 |
| 8955721990 | 2, 4, 3, 1, 0, 1, 0 | 543 / 3748 s = 14.5% | 4056 |

L1 retains death and `timeDead`; L2 forms an interval; L3 intersects it with phases; L4 retains trajectory and numerator/denominator. L5 receives `hero=64, position=2, n=4`: median individual death fraction **11.68%**, range **4.02–14.49%**; median recorded XP in the first ten minutes **4708.5**. This group has three wins and one loss. Its match list is absent from the normal L6 packet: only the aggregate and drill key remain.

L6 analyst decision: “On mid Jakiro, the time recorded in death intervals varies substantially. Some games have long stretches without deaths, so frequent deaths should not yet be called a fixed part of your style. A useful next step is comparing conditions in safer and more expensive phases: prior team state, resource share, XP and actions after returning. We will assess improvement in comparable conditions rather than by death count alone.” This is a testable hypothesis, not a claim that 11.68% of playtime could have been saved.

Numbers establish variation; choosing to investigate conditions is the analyst's decision. Alternative explanations include duration, drafts and team trajectory. A win relationship is not established. The example shows how a profile generalizes data and chooses a next check without retelling matches. Useful strengths and more precise recommendations require other feature families; this example alone is not a sufficient profile.

## Migration and verification

Existing `Finding`, `authored-synthesis-1`, saved L2–L6 responses, profile and task 3 report remain historical versions. They must not be relabelled as calculated metric passports or have their prose automatically accepted as numeric facts.

- Task 5: calculate L1–L4 core features from local sources; forward required base context through levels; do not call `accept_analysis` for every numeric aggregation.
- Task 6 complete: [native grid, observed occupancy, distributions, routes and L5 groups](../development/spatial-analysis.md). World geometry and semantic regions remain unverified and unavailable.
- Task 7: [numerical L5, chronology, joint distributions and statistical limitations](../development/longitudinal-analysis.md) are implemented; verification results are documented separately.
- Task 8: implement idempotent accumulation, replacement of contributions and targeted recomputation.
- Task 9: give current Codex compact L5 data and claim history; adapt validation for numeric/authored nodes while retaining provenance and staleness checks.
- Task 10: evaluate profile usefulness and “1000 + 10” updates using artificial data. This does not authorize collecting additional real games.

The already available **audit** command, run from the repository root, uses no network or new collection:

```powershell
.venv\Scripts\python.exe -m tools.audit_analysis_catalog --output .agent/tmp/statistics-audit.json
```

Original local snapshots of the ten games are required; large raw files are not tracked in Git. A small audit result is tracked for inspection. Reproduction verifies bytes, identity and observed values; it does not establish API completeness, in-game causes, interpretation correctness or statistical stability.
