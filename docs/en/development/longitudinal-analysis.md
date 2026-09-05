# Longitudinal statistics L5

Task 7 implements numerical conditional summaries, chronology and exploratory association screening. L5 consumes retained compact match rows. Current Codex receives distributions, contrasts and limitations rather than every game's events. This is analyst input; the code does not produce psychological labels or causal conclusions.

## Commands

From the repository root, without additional dependencies:

```powershell
.\.venv\Scripts\python.exe tools/check_longitudinal_analysis.py
.\.venv\Scripts\python.exe tools/collect_ranked_month.py --year 2026 --month 8 --discover-only
.\.venv\Scripts\python.exe tools/collect_ranked_month.py --year 2026 --month 8
.\.venv\Scripts\python.exe tools/check_longitudinal_analysis.py --dataset data/datasets/2026-08-ranked/selection.json --label august
.\.venv\Scripts\python.exe tools/check_longitudinal_analysis.py --dataset data/datasets/2026-08-ranked/selection.json --label august --reuse-signatures
```

The first command retains the original ten-match example. Monthly collection is a separate explicit network operation using the account and token loaded by `src/settings.py`. The user authorized August 2026, from August 1 00:00 inclusive to September 1 00:00 exclusive, UTC+3. OpenDota history is paginated to the lower month boundary; raw pages and request metadata are preserved. Selection includes completed ranked games (`lobby_type=7`) without hero/outcome filtering. Visible non-ranked games remain available to detect chronology gaps. Exhausting API pages does not establish complete actual account history.

STRATZ requests are sequential. Monthly collection retries only HTTP 502/503/504, at most three attempts per query with delays; 401/403/429 are not automatically retried. Exhausted gateway failures remain explicit gaps while other selected games continue. Rerunning reuses complete snapshots and successful per-query responses for the same match when query text, variables, byte size and SHA-256 match. Original retrieval time and reuse provenance remain recorded. Responses from different dates are not described as a simultaneous snapshot. No paid operations or repeat parsing are requested.

The final command recalculates L5 using only stored L4 signatures, without reading raw journals or fetching data. It rebuilds the compact table's aggregates; updates to affected aggregates are now available through the [task 8 service](cumulative-analysis.md). Run without `--reuse-signatures` to incorporate additional collected games.

## New information between levels

| Lower data | New L4 signature | New L5 information |
| --- | --- | --- |
| XP, gold, duration | Recorded XP/min, gold/min, numerators and denominators | Conditional distributions, joint changes, outcome contrasts |
| Deaths and absence intervals | Death-time fraction, deaths/10 min, repeated death within 120 s of the previous recorded death end | Risk composition by phase and prior team state; outcome associations |
| Final team kills/assists | Participation `(K+A)/team kills` | Participation × XP change following combat minutes |
| Consecutive minutes and purchases | Difference in next-minute changes between cases and control minutes | Purchase × damage change; joint route changes |
| Native grid cells and presence time | Most-visited-cell concentration, transitions/min, distance to observed ally | Spatial variation and association with losses |
| Start time, duration, outcome | Compact chronology, including games without detailed playback | Estimated sessions, runs, after-result transitions and game order |

Gold means recorded incoming gold, not automatically the source's final GPM. XP is separate. Tower damage measures observed pressure, not verified conversion of an advantage into objectives. The share of deaths while behind divides by all deaths in that phase, not time spent behind: death composition is not a state-specific hazard rate.

Distributions retain n, missingness, coverage, equal-match mean, median, quartiles, p10/p90, sample standard deviation, MAD and extremes. Quantiles use linear `(n−1)p` interpolation. Pooled-denominator values are distinct: the mean of `1/2` and `10/100` is 30%, whereas `11/102` is 10.78%. They answer different questions.

## Conditions and joint changes

Strict groups use hero, position, mode, side, both version identifiers, STRATZ rank-estimate band and 10-minute duration band. Phase groups additionally use start time, full/partial phase and team state before the phase; death groups use state immediately before the death. States are ahead/behind by more than 1000 gold or approximately even, based on sufficiently fresh snapshots. Rank is a source proxy, not an exact skill measure.

Both complete drafts remain in signatures for drill-down; draft strength and requirements are not computed. Even strict groups do not fix drafts or team decisions. Relaxed hero/position/mode/version groups explicitly remove side, rank and duration constraints: useful descriptions, excluded from statistical confirmation. Unknown versions cannot silently pool across matches.

Post-combat XP compares `next-minute XP − current-minute XP` for minutes with and without damage to original enemy heroes. Controls are in the same match, 10-minute phase, prior team state, death-presence category and 250-XP baseline band. Purchase contrasts compare damage changes with a 500-damage baseline band. Purchase does not establish delivery or use. Coarse matching does not eliminate regression to the mean, timing selection or other confounding: this describes an observed sequence, not an action's effectiveness.

Pairs may overlap and controls may be reused. Only one resulting metric per match/group reaches L5; more minutes do not create more independent outcomes. Spatial rates require at least 80% observed coverage outside recorded death intervals and at least 60 observed seconds. Purchase route comparisons require two full 60-second windows, each with at least 80% coverage. Geometry inherits the [spatial layer's limitations](spatial-analysis.md).

## Chronology and changes

Estimated sessions link games when the end-to-start break is at most 60 minutes, with 30/90-minute sensitivity results alongside. Known intervening missing/non-ranked games, overlapping times and unknown clocks break links. Observed history is censored at both ends; actual uninterrupted play, fatigue and tilt are not inferred.

Outcome runs refer to observed result adjacency and may cross long breaks. After each outcome, summaries show following games, results, hero/role changes and behavior differences. XP, gold, participation and death-fraction differences require identical strict conditions including duration. Unknown roles are not counted as role switches. Order-in-session summaries mix group composition and do not establish a second/third-game effect.

The recent period is the last `min(10, floor(n/3))` detailed matches, at least one. The historical baseline is disjoint. Strict-group comparisons show sample sizes, metric changes, coverage and both compositions. No matching conditions means no estimated skill change. Chronology can include more games than detailed statistics; both counts are explicit.

## Exploratory screening

Fixed feature pairs and each feature × outcome are declared before scoring in groups with n≥3. The earliest 70% of observed UTC calendar days form discovery; the rest form temporal validation. A day is never split. Direction and priority use discovery only.

Match-level Pearson/Spearman correlations and slopes are retained. Screening p uses equally weighted day means, so one day cannot masquerade as many independent observations. Requirements are at least eight days, five eligible matches, and for outcome tests five wins and five losses. These prototype gates do not guarantee adequate power. Permutation assumes exchangeable days under the null; it does not eliminate serial dependence between days. The reproducible random permutation count is chosen before scoring: max(999, ceil(family size/0.05)−1), capped at 199999, with a +1 correction. [SciPy permutation-test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).

Bonferroni corrects across the entire declared family separately in discovery and validation, including insufficient-data pairs. This is conservative. The smallest attainable adjusted p is family size/(permutations+1), capped at 1 and explicitly reported. Very large families can still make confirmation impossible once the permutation cap is reached. [NIST multiple-comparison reference](https://www.itl.nist.gov/div898/handbook/prc/section4/prc463.htm).

Candidate priority is absolute daily correlation × coverage × `min(days/8,1)` × leave-one-day-out sign agreement. Each candidate retains conditions, a practical next check and least/most directionally consistent examples. This ranks hypotheses, not player errors. Temporal replication requires matching signs and adjusted p≤0.05 in both parts; even then it is observational. Reusing the same holdout is not independent new validation. Persistent hypothesis tracking/updating belongs to subsequent tasks.

## Storage, services and context limits

Services: `longitudinal.services.prepare_match`, `aggregate_signatures`, `save_analysis`, `read_analysis`. Ignored `data/analysis/longitudinal/` stores match signatures, complete L5, drill indexes and `packet.json`. Small verification artifacts are retained in `data/prototype/longitudinal-*-verification.json`.

`compact_packet` is limited to 32,000 UTF-8 bytes and explicitly counts omitted cohorts/candidates with full-result references. Its normal input has no list of individual games. `DrillSession.query` allows up to three requests sharing 8000 bytes: `cohort:<id>` plus metric, `relation:<id>`, `sessions`, `recent`, `index`; `offset` selects a page. Exhausted budgets or oversized mandatory rows cause explicit errors. Examples carry ID, date, hero, position and revision, avoiding ambiguous references such as “the game against Arc.”

This is task 7's numerical contract. Automatic L5→L6 claim propagation, profile history and complete analyst-session budgeting belong to task 9. Stored signatures do not independently discover source changes: explicitly obtained corrected contributions enter [task 8 incremental storage](cumulative-analysis.md), updating affected statistics and marking earlier evidence stale.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest tools.test_longitudinal_analysis tools.test_spatial_analysis tools.test_numeric_analysis tools.test_analysis tools.test_analysis_series tools.test_synthesis
```

Tests cover unequal denominators, missing/invalid data, a known association and seeded null, role/version separation, no holdout influence on priority, day blocking, temporal boundaries, sessions, gaps, composition/coverage changes, integrity and actual byte budgets. An artificial 1000-row scenario checks packet size without fetching matches or using a model. [Real-data results](longitudinal-results.md).
