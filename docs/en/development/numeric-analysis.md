# Numeric levels L1–L4

[Development](README.md) · [Catalogue and level design](../architecture/cumulative-statistics.md) · [Русский](../../ru/development/numeric-analysis.md)

Task 5 is implemented in `src/apps/analysis/numeric/`. An ordinary match completes all four levels without model prose. Code stores a numeric trajectory with provenance, quality, hero, estimated position, lane, both drafts and team state. Existing task 3 authored analyses remain separate.

This is a foundation for longitudinal statistics, not a new finished player profile. Heatmaps belong to task 6, sessions and cross-match relationships to task 7, cumulative changes and the main L5–L6 analyst to tasks 8–9. Deferred directions currently return `unavailable` with a reason.

## Implemented flow

| Level | Input → calculated output |
| --- | --- |
| L1 | Verified local responses → typed target journals; economy, XP, levels and coordinates for all participants; context and source disagreements |
| L2 | L1 only → disjoint minute windows; gold/XP by reason; last hits; death/return intervals; damage clusters; purchases, uses, healing and recorded wards/objects |
| L3 | L2 only → ten-minute phases: rates/changes, time fractions, minute distributions, farming/damage combinations, team-state transitions and recorded team-XP share |
| L4 | L3 only → compact match trajectory, final kill participation, resource shares, duration distributions, numeric features and limits |

Minute windows include events in `[0,duration]` with exactly `duration` seconds of exposure. Intermediate boundaries are half-open; a final-timestamp event enters the last interval once. Pregame events remain in L1 and first purchases retain negative times. Later phases of a short game are absent rather than zero.

Deaths and combat clusters are additional views of the same data. Phase gold/XP/damage comes from disjoint windows, not overlapping episodes. Overlapping reported death intervals do not double absence time. A cluster is counted once at its start; damage stays assigned by actual event time.

## Contract and quality

Artifacts use `numeric-analysis-1`; calculations use `numeric-1`. `method_version=1` identifies the catalogue passport and `implementation_version` the implementation. Measurements contain ID, units, `source_observation` / `derived` / `proxy` kind, value, numerator/denominator, quality, uncertainty and provenance. Model assessments are separate and cannot replace measurements.

Source states distinguish `missing`, `null`, `empty` and `malformed`; zero/false do not replace absence. Bool is not accepted as a numeric value. Quality statuses are `observed`, `partial`, `conflicting`, `unavailable`. `eligible` means passing the implemented checks for this measurement, **not proven API completeness**. Raw/valid counts, invalid rows, observed time bounds and reasons are retained. Unknown temporal coverage is null.

Journal/final disagreements stay beside recorded values. In seven matches, assist journals cannot support unconditional time-window comparisons, but final participation `(kills + assists) / allied kills` independently uses reconciled final totals. The entire match is not dropped. A zero denominator gives null.

Economy/health snapshots must be no more than five seconds old. Team difference requires all ten participants; allied resource share requires all five allies. Missing snapshots return null plus coverage; transitions across unknown states are not invented. A personal counterpart must be the only enemy with the same known estimated position. Matching positions do not prove direct lane opposition.

## Measurements versus gameplay assessments

- **XP/gold:** recorded event sums with native reasons. Gold also splits by `isValidForStats`, preserving unknown flags. These are not necessarily GPM/XPM × duration, net worth or hypothetical income. Residuals remain; invented events never reconcile them.
- **Levels:** first observed attainment of 6/12/18/25/30; unattained levels are right-censored at match end. Monotonicity and final level are checked.
- **Development gaps:** intervals between positive XP events or last hits; edge gaps are censored. Missing recorded events do not prove passivity.
- **Observed activity:** ten-second bins containing a last hit, damage or building damage. Bin durations are a proxy, not continuous useful play. Movement, vision and other actions are outside this definition.
- **Death time:** union of `[time,time+timeDead)` clipped to match/phase. Source estimates, buybacks and timing errors limit actual absence claims.
- **Return:** first last hit/recorded damage/building damage after estimated death end and before the next death or match end. No event means right censoring. Health/mana before death and the first action, net-worth change and team difference are retained. Avoidability and lost potential gold are not estimated.
- **Combat clusters:** positive damage by the target hero to known enemy heroes with gaps up to 15 seconds and explicit non-illusion flags on both sides. These are damage sequences, not full teamfights. They miss participation without damage and actions by owned illusions. The threshold still needs longitudinal validation.
- **Damage:** preserve the raw sum; separately retain original enemy targets, illusion targets, unknown attribution and owned-illusion damage to original enemies. The last quantity is a subset and must not be added twice. Even filtered sums sometimes differ from finals; remaining causes are unresolved.
- **Healing:** distinguish self, other known recipients and final `heroHealing`. Self healing is not ally support; saved lives are not measured.
- **Purchases/uses:** native IDs, recorded times and use counts. Purchase is not delivery or readiness. Missing use does not prove a missed opportunity.
- **Wards/objects/support:** recorded counts by native codes; `scanUsed`/`pingUsed` counters retained. Minute-array stacks, effective vision and conversion of kills into typed objectives remain unavailable pending semantic validation. Native `npcId` values are not verified object names.

Additional `details`, minute-window and phase fields are versioned by `numeric-1`: internal event-gap distributions, snapshot coverage, damage attribution, 15-second clusters, ten-second activity bins and last-hit/original-hero-damage co-occurrence within a minute. These extend task 4 passports without introducing psychological scores. L4 keeps bounded summaries; full gaps and episode lists remain below.

## Results on the ten real matches

The [results and verification](../../../data/prototype/numeric-verification.json) use existing local snapshots. XP means recorded experience; death percentage is estimated time in source death intervals; participation uses final kill participation. Different heroes/positions do not form one player ranking.

| Match | Hero / position | XP before 10:00 | Recorded XP/min | Final XPM | Death % | Participation % |
| --- | --- | --- | --- | --- | --- | --- |
| 8960626424 | Death Prophet / 2 | 5118 | 780.5 | 780 | 17.65 | 44.4 |
| 8959457705 | Jakiro / 5 | 2573 | 705.9 | 705 | 13.67 | 42.9 |
| 8959269261 | Dragon Knight / 2 | 5666 | 783.1 | 783 | 13.66 | 52.1 |
| 8959040566 | Jakiro / 2 | 4744 | 964.7 | 964 | 4.02 | 57.1 |
| 8958839199 | Jakiro / 2 | 4673 | 841.7 | 841 | 10.02 | 87.9 |
| 8957931610 | Night Stalker / 2 | 5516 | 761.3 | 760 | 0.00 | 52.1 |
| 8957583110 | Underlord / 3 | 3430 | 805.7 | 805 | 11.79 | 58.8 |
| 8957325148 | Jakiro / 2 | 6654 | 860.1 | 859 | 13.35 | 81.6 |
| 8956189348 | Juggernaut / 1 | 3584 | 913.2 | 913 | 3.49 | 45.1 |
| 8955721990 | Jakiro / 2 | 4056 | 1030.9 | 1185 | 14.49 | 66.2 |

| Match | Recorded gold | Last hits: journal / final | Neutral / ancient¹ | Median return, s² | Damage clusters³ |
| --- | --- | --- | --- | --- | --- |
| 8960626424 | 23818 | 504 / 504 | 203 / 9 | 11.5 | 31 |
| 8959457705 | 16624 | 244 / 244 | 87 / 12 | 16.0 | 32 |
| 8959269261 | 18729 | 274 / 274 | 60 / 12 | 9 | 26 |
| 8959040566 | 20460 | 291 / 291 | 89 / 12 | 11 | 30 |
| 8958839199 | 18017 | 286 / 286 | 126 / 6 | 16.0 | 35 |
| 8957931610 | 13695 | 152 / 152 | 33 / 0 | — | 24 |
| 8957583110 | 15029 | 270 / 270 | 88 / 3 | 21.0 | 24 |
| 8957325148 | 18960 | 311 / 311 | 102 / 1 | 6.5 | 28 |
| 8956189348 | 33626 | 547 / 547 | 195 / 20 | 13.0 | 26 |
| 8955721990 | 44634 | 616 / 615 | 140 / 11 | 10 | 45 |

¹ Flags may overlap; ancient counts must not be added to neutral counts again. ² Estimated death end to first recorded action, excluding unavailable/censored returns. ³ Observed clusters under the stated rule, not the number of teamfights.

Conflicting journals: assists 7/10, kills 1/10, last hits 1/10. Table values do not remove these limitations.

L4: 43,904–53,104 UTF-8 bytes; L1/L4: 69.6–160.1×.
This is a complete numeric match artifact, not a bounded model packet. Future L5 aggregates these rows in code; a thousand L4 records are not sent to the analyst as a list.

Newly visible distinctions:

1. **Final XPM hides the development trajectory.** The four position-2 Jakiro matches have 4744, 4673, 6654 and 4056 XP before 10:00. The highest final XPM, 1185, belongs to the lowest starting value in this group. Final XPM therefore does not describe the opening. The trajectory preserves both observations; explaining differences requires contextual analysis.
2. **Raw damage may describe attacking illusions.** Juggernaut has 206,425 recorded damage, including 173,720 to illusion targets. The remaining 32,705 against original enemy heroes includes 2299 from owned illusions and matches final `heroDamage`. Filtering does not fully reconcile every other hero, so this is not claimed as universally reconstructed final damage.
3. **Self healing differs from support.** Death Prophet has 32,717 recorded self healing with final `heroHealing=0`. A zero final value cannot establish that no health restoration occurred, nor should self healing become ally-support credit.
4. **Return to events differs from the cost of dying.** Underlord has one censored return and a 21-second median among observed returns. This does not prove slow play. The contract retains first-action type, state and limitations so the analyst can select an appropriate episode.

These tables are prototype measurements. Stable relationships, causes and a portrait are not asserted from individual values; subsequent L5–L6 work is required.

## Selective interpretation

A separate exchange supports **one selected death**. Input includes numeric episode, neighbouring minute windows, context and question, limited to 16,000 UTF-8 bytes including the envelope. Current Codex supplies up to 8000 answer bytes and 1–4 claims with kind, evidence, alternative, uncertainty and next check. There is no external model API.

The [saved real example](../../../data/prototype/numeric-review-example.json) reviews Death Prophet, match 8960626424, death at 41:33. The source reports 90 seconds dead, then 14 seconds until a last hit. Between sampled endpoints, net worth changes by +53 and team difference from +9146 to +9956. Another death follows 54 seconds after the first last hit. The analyst prioritizes reviewing decisions after returning; the first death's duration alone proves neither a lost team lead nor an error.

Packets/responses are hashed; identical inputs produce the same key. `read_numeric_review` retrieves the saved response after dependency and source-hash checks. Changed questions or numeric nodes require a new assessment; changed sources invalidate the old one. Validation checks structure/provenance, not semantic truth.

## Services and commands

Main operation: `src.apps.analysis.numeric.services.build_numeric_match_from_sources(root=..., match_id=..., account_id=...)`. Only IDs in the existing ten-match `data/prototype/synthesis/selection.json` are allowed. The offline workflow requires no API token or new settings.

Direct lower operations: `facts.build_numeric_facts(Sources)`, `episodes.build_numeric_episodes(l1)`, `phases.build_numeric_phases(l2)`, `phases.build_numeric_match(l3)`. They validate versions and immediate lower levels. `prepare_numeric_review`, `accept_numeric_review`, `read_numeric_review` are exported by `numeric.services`.

```powershell
# One match or the existing selection
.venv\Scripts\python.exe -m src.apps.analysis.numeric.cli build --match-id 8960626424
.venv\Scripts\python.exe -m src.apps.analysis.numeric.cli build --all --summary .agent/tmp/numeric-run.json

# Independent source checks and full recomputation
.venv\Scripts\python.exe -m tools.check_numeric_analysis --output .agent/tmp/numeric-verification.json

# Formulas, boundaries, quality, versions, optional reviews and historical contracts
.venv\Scripts\python.exe -m unittest tools.test_numeric_analysis tools.test_analysis tools.test_analysis_series tools.test_synthesis
```

For a selected review, substitute the `directory` printed by `build`:

```powershell
.venv\Scripts\python.exe -m src.apps.analysis.numeric.cli prepare-review --directory <directory> --episode death:5 --question "What should be checked in this episode?"
.venv\Scripts\python.exe -m src.apps.analysis.numeric.cli accept-review --directory <directory> --packet <packet.json> --response <response.json>
```

`<...>` denotes replaceable arguments. The saved example's `response` supplies the response shape; use the new packet ID and write a new assessment. Copying old prose is not a fresh analysis.

Artifacts live at `data/analysis/numeric/<match>/<key>/L1.json` … `L4.json`, with a manifest of sizes, hashes and revisions. The key includes source references, catalogue, parameters, numeric code and shared dependency modules. Reads also verify the child chain. `data/analysis/` is already ignored; only small verification results and the example are tracked. Historical artifacts are not overwritten. Per-match caching is not the cumulative store planned in task 8.

## Verification

36 tests pass: 16 new and 20 existing. Coverage includes overlapping intervals, final boundaries, zero/missing/invalid inputs, one-journal conflicts, snapshot freshness, unknown position, censoring, damage attribution, missing opponent XP, dependency/artifact corruption, review budgets and reuse.

The ten-match offline verification checks source hashes/participants, 186 selected source pointers, direct XP/gold sums, independently unioned death intervals, final participation using OpenDota, window/phase additivity and the level graph. Full recomputation produces identical revisions; subsequent runs use cache. New matches: 0. Mandatory model responses: 0. These checks do not establish journal completeness, cluster-threshold usefulness or causal relationships.
