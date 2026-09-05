# Incremental statistics updates

[Development](README.md) · [Русский](../../ru/development/cumulative-analysis.md) · [Accepted contracts](../architecture/cumulative-statistics.md)

Task 8 is implemented in `src/apps/analysis/cumulative/`. The service accepts new or corrected compact contributions, updates affected groups and stores a bounded change packet for the analyst. It does not read earlier games' source events. API collection and generation of new L4 signatures remain separate explicitly called operations.

## Storage

The implementation uses standard-library `sqlite3`, without a new dependency. The local database lives under `data/analysis/cumulative/`, excluded from Git by the existing `/data/analysis/` rule.

| Table | Contents and purpose |
| --- | --- |
| `contracts` | Player, catalogue, method/coordinate/grouping versions, window parameters and published generation |
| `matches` | Active revision per match_id, feature availability/eligibility and compact chronology |
| `revisions` | Immutable envelopes: L4 signature, optional phase/state L3 grid, provenance and dependencies |
| `members` | A separate small match contribution to each numeric or spatial group |
| `groups` | Distributions, joint statistics, spatial aggregates and recent-versus-history comparisons |
| `sequences` | Cached distributions of four metrics per session/outcome run, with input revisions |
| `states`, `changes` | Consistent overall state and published change history |
| `claims` | Versions of existing analyst-authored statements, evidence references and staleness |
| `jobs` | Targeted feature rebuild plans and actual completion coverage |

Authored conclusions do not replace numeric storage. Full envelopes support reproducibility and addressed retrieval; ordinary updates do not load earlier full envelopes. IDs and source references stay locally available, while the normal change packet does not list all matches.

## Imports, corrections and precision

Entry points are `schemas.contract`, `schemas.contribution`, `services.apply_batch`, `services.snapshot`, and `services.change_packet`; planning and evidence storage live in `review.py`. The CLI only reads parameters/JSON, calls a service and prints its result.

An envelope links its L4 signature to the spatial input: player, match, context, signatures and the dependency reference to the derived spatial L4 are checked. L4 alone is allowed, but contributes no spatial coverage. `source_revision` versus `calculation_or_spatial_revision` depends on whether the source snapshot reference changed; the label itself does not claim improved completeness. Changes in eligibility are reported separately.

Repeating the same revision returns `no_op`, without increasing observations or generation. Duplicate match IDs within a batch are rejected. Replacements and removals require `expected_revisions={match_id: current_envelope_revision}`; `expected_generation` is an additional optional check. Removal preserves history. Restoring a removed match requires the explicit value `"removed"`, preventing an old import from silently restoring it.

The previous contribution is removed from group membership, the new one inserted, and only affected compact groups are rebuilt. Extrema, quantiles, MAD and ranks are recalculated from group members; medians are not subtracted. Match-ID ordering is fixed. No approximate distributions are used: quantiles interpolate at `(n−1)p`, with ordinary Python floating-point arithmetic rather than an exact-decimal guarantee. Verified full and incremental results match exactly in this representation.

Numeric groups inherit task 7 conditions: hero, position, mode, game version and additional comparability conditions, with separate phase/state groups. Spatial groups also retain side and grid parameters. Unknown versions are not unconditionally pooled with known versions. Relaxed groups remain descriptive. Zero differs from absent/ineligible data; n, missingness, coverage and numerator/denominator totals are retained. Equal-match means and pooled-denominator rates stay separate.

Joint statistics include paired n, sums of x/y/x²/y²/xy, Pearson, Spearman and slope for declared pairs and match outcome. These are descriptive associations, not refreshed significance tests or causal evidence.

## Sessions, runs and recent windows

Compact chronology retains start time, duration, outcome, context and four metrics: experience, gold, death-time fraction and participation. Late arrivals or corrected timestamps can merge/split sessions, alter runs and relink adjacent transitions. `known_gaps` explicitly break unreliable sequences. The main session threshold is 60 minutes; sensitivity at 30/90 minutes and task 7's estimated-chronology limitations are preserved.

Boundaries and global chronology summaries currently rescan the entire compact table, O(n). Individual session/run statistics are cached, so unchanged inputs are not aggregated again. A metric correction updates affected sequences even when boundaries do not change. Caching applies to the main 60-minute threshold; 30/90 sensitivity is recomputed over compact history.

The recent window contains the last 10 games by `(start_time, match_id)`, with its size included in the contract. Comparisons use disjoint older history within strict whole-match groups, retaining distributions, mean/coverage changes and composition. If either arm is empty there is no comparison. Window arrivals/departures update affected comparisons. Separate rolling spatial/phase windows and recency weights are not implemented.

## Versions, new features and the analyst

The contract includes catalogue and method hashes, grouping/spatial parameters, map identifier and window size. The method hash covers source files in cumulative/longitudinal/spatial and is cached per process. Code changes conservatively create a separate calculation namespace; changed code requires a new process. A different implementation cannot append under the old contract. Meta effects are disabled; game version is a comparability condition.

`plan_rebuild` checks retained feature eligibility per match, choosing `reuse_compact`, `derive_from_compact`, or `targeted_sources_required`. The caller explicitly declares new formula dependencies; available numbers do not establish formula validity. Geometry/method changes conservatively require targeted source rebuilding. Planning does not automatically download or calculate anything.

After explicitly calculating/importing new envelopes, `reconcile_jobs` checks target feature eligibility and whether the plan's source revision is current. An unchanged envelope cannot complete a required source rebuild. Until all planned features are materialized, `coverage_complete=false`; a changed source revision produces `stale_source_plan`. The old namespace remains readable. New methods require corresponding executable code, not relabelled old results.

`change_packet` caps output at 32,000 UTF-8 bytes (configurable down to 2000): selected groups' previous/current values, changed-match counts, window entries/exits, stale evidence counts, work and a full-change reference. Omitted groups are counted. Group ordering is technical; analyst prioritization belongs to task 9. `snapshot` and addressed group/sequence reads are detailed local operations, not bounded model-context packets.

`save_claim` stores already-authored text after validating generation and evidence revisions. Changed evidence marks statements stale. Numerical updates set the profile to `pending_analyst_review`. Task 7 screening is marked `stale`: temporal splits, comparison families and p values require a separate explicit recalculation using existing L5 functionality. That recalculation is not integrated into incremental imports. Personal text updates and L6 profile history belong to task 9.

## Consistency and recovery

Contributions, groups, sequences, changes, evidence staleness and generation publish in one `BEGIN IMMEDIATE` transaction with `synchronous=FULL`. Readers use a separate consistent transaction and see the previous state until commit. After an error/process exit, retrying is safe: unfinished contributions roll back and committed ones are recognized as duplicates. Database `user_version=2` adds tables without deleting earlier contributions.

Guarantees rely on a local filesystem and SQLite's write/synchronization assumptions; the process-exit test does not simulate physical power loss. [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html), [SQLite transactions](https://www.sqlite.org/lang_transaction.html).

## Commands and verified results

From the project root, offline, with saved inputs for the ten matches from tasks 5–7:

```powershell
.\.venv\Scripts\python.exe tools/check_cumulative_analysis.py
.\.venv\Scripts\python.exe -m unittest tools.test_cumulative_analysis tools.test_longitudinal_analysis tools.test_spatial_analysis tools.test_numeric_analysis tools.test_analysis tools.test_analysis_series tools.test_synthesis
$verification = Get-Content data/prototype/cumulative-verification.json -Raw | ConvertFrom-Json
.\.venv\Scripts\python.exe -m src.apps.analysis.cumulative.cli --db data/analysis/cumulative/ten.sqlite read --contract $verification.contract_id
.\.venv\Scripts\python.exe -m src.apps.analysis.cumulative.cli --db data/analysis/cumulative/ten.sqlite read --contract $verification.contract_id --change 1
```

`--group <group_ref>` retrieves one packet-referenced group; `--sequence <id>` retrieves one sequence from `snapshot.state.sequence_refs`. Ordinary `read` returns an overall summary without full chronology. The local example packet is `data/analysis/cumulative/ten-change.json`.

A separate numeric-only L4 import example, without spatial data, into another database:

```powershell
$signaturePath = (Get-Content data/analysis/longitudinal/ten/signatures.json -Raw | ConvertFrom-Json).paths[0]
.\.venv\Scripts\python.exe -m src.apps.analysis.cumulative.cli --db data/analysis/cumulative/example.sqlite import --account 203182675 --catalog docs/contracts/statistics-catalog.json --map-version native-source-grid-1 --signature $signaturePath
```

Use repeatable `--envelope <json>` for full envelopes, `--expected <json>` with a revision mapping for corrections, and repeatable `--remove <match_id>` for removal. Errors exit nonzero; unchanged reimports succeed with `no_op`. JSON output uses UTF-8, including when redirected on Windows.

Verified 2026-09-05: [machine-readable results](../../../data/prototype/cumulative-verification.json). The original ten real matches produced **292 groups, including 68 spatial groups**. Full calculation and 3+4+3 batches matched; numeric distributions matched task 7 and spatial distributions matched task 6. No new games were fetched; meta was disabled.

The synthetic scenario contains 1010 rows, 20 heroes and 60 groups. This verifies mechanics, not gameplay; deliberately identical timestamps for some rows exercise ambiguous chronology. In the measured run:

| Check | Result |
| --- | --- |
| Initial 1000 / add 10 | 2.58 s / 2.60 s; update measured with tracemalloc |
| Groups rebuilt | 30 of 60 |
| Compact group contributions read | 2030 rows / 1,360,128 bytes; a match contributes to multiple groups |
| Sequence statistics | 20 rebuilt, 1933 reused |
| Old-match correction | 3 groups, 153 contributions; 2 sequences rebuilt, 1951 reused |
| Earlier full L4 / source events | 0 / 0 reads |
| Chronology | 1000 previous rows read; boundaries/global summaries evaluated over 1010 |
| Peak Python / database size after correction | 13,684,286 / 18,128,896 bytes |
| Addition packet | 31,766 bytes |

Full, incremental and corrected calculations matched, including sequence caches; duplicates left state unchanged. Source loading and Python file reads were forcibly prohibited during the measured update; SQLite's internal database reads remained allowed. **100 tests pass**, including 20 new tests covering missing features, spatial replacement, late arrival, window eviction, stale writes, targeted plans, three rollback checkpoints, reading during a write, abrupt exit of a separate process and CLI encoding. Actual CLI summary/change/group/sequence reads, importing and duplicate importing were also exercised.

Timings depend on hardware. Tracemalloc excludes SQLite native allocations and OS cache. Spatial scaling to 1000 games was not separately measured. Exact distribution cost depends on affected group sizes, while global chronology remains linear; this does not promise constant update cost for arbitrary history.
