# L5–L6 analyst: profile and updates

[Development](README.md) · [Русский](../../ru/development/analyst-analysis.md) · [Session results](analyst-results.md)

Task 9 is implemented in `src/apps/analysis/analyst/`. The normal path is task 8 cumulative state → bounded numerical packet → current Codex → evidence/version validation → saved personal profile. Software calculates and checks provenance; the analyst authors explanations. There is no separate model API or automatic threshold-based assignment of traits.

## Packet and numerical interpretation

`services.prepare` reads cached SQLite aggregates, composition, coverage, chronology status, previous hypotheses and changes since the last profile. It does not automatically read full match signatures, source events or lower authored narratives. Main input is capped at 32,000 UTF-8 bytes, with a minimum requested budget of 8000. The limit applies to delivered input, not database size.

The question uses an explicit metric list. Each metric includes units, formula and reading guidance: an increase does not necessarily mean better play. Inputs retain n, missingness, coverage, quantiles, mean, pooled numerator/denominator and outcomes. Fractions of 0.10 mean 10%; deaths, team kills, seconds and combat windows are not interchangeable denominators.

Hero, estimated position, mode, versions and grouping conditions remain explicit, including relaxed conditions, uncontrolled drafts and team decisions. Flags identify outcome contrasts whose direction depends on weighting. Correlations remain descriptive; stale significance tests are not presented as current.

Previously cited evidence, changed groups and populated whole-match groups take priority, followed by phase/state groups. Previously displayed but uncited groups do not gain priority merely because they appeared earlier. Omitted groups are counted; groups empty for requested metrics do not occupy the main packet. Changed displayed groups include before/after values; recent windows retain comparisons against disjoint earlier history. Large compositions show the top 12 categories per axis and count omitted observations.

Preparation currently reads all cached aggregates for ranking and change logs since the preceding profile. Processing is not constant-cost; this optimization primarily concerns analyst input. Methods, windows and precision inherit [task 8](cumulative-analysis.md).

## Profiles, hypotheses and revisions

Initial formation uses `mode=initial`; updates use `mode=update` with the previous compact profile. Current Codex supplies a portrait, limitations, change reasons, one to six hypotheses and one to three development priorities. RU/EN are required. See the [initial answer](../../../data/prototype/analyst/initial-response.json) and [update answer](../../../data/prototype/analyst/update-response.json).

Each hypothesis stores its ID, status, hero/position scope, statement, alternative, criterion, uncertainty, decision reason, support and counterevidence. Lifecycle: `discovered` → `testing`, then potentially `supported`, `weakened`, or `rejected`. Rejected hypotheses can reopen through testing. Previous hypotheses cannot silently disappear; the working set holds up to six, including rejected ones. This is an explicit prototype boundary; archival of an overflowing working set is not implemented.

Promotion to `supported` requires newly versioned cited evidence. Repeating prose or the same episode cannot raise confidence. A new revision itself does not confirm a hypothesis: the analyst still authors the decision and criterion. Confidence remains preliminary/conditional. Schema validation cannot establish semantic truth, causality or coaching usefulness.

`wording=retain` preserves the portrait verbatim while reasons, limitations and evidence are reviewed; `revise` explicitly edits it. Profile history retains prior revision, statistics generation, population and data-period end. Identical answer acceptance is idempotent; different answers to a closed session, stale generations and conflicting newer profiles are rejected.

`analyst_sessions`, `analyst_drills`, `analyst_profiles`, `analyst_lower`, and `analyst_match_reviews` are added to local SQLite without changing task 8 numerical contracts. Profile publication is transactional. `read_profile` reports `current` or `pending_analyst_review` by generation. This is the authored layer's status; task 8's numerical `states.profile_status` is not rewritten and does not replace authored-version freshness.

## Addressed retrieval and lower interpretation

A profile session permits four successful drills, at most 12,000 bytes combined and 5000 per response. Quotas persist in SQLite; preparing the same packet again does not reset them. Oversized responses fail without delivery. Quotas/counters describe successful responses, not all internal reads during rejected attempts.

`retrieval.drill` opens:

- `group`: one metric and up to three cases: middle by order, lower tail and upper tail. Selection, ID, date, hero, role, drafts and unexamined remainder are explicit. Tails are countercheck candidates, not automatically detected mistakes.
- `match`: one compact match signature and available phase selectors.
- `phase`: a selected ten-minute phase, economy, deaths, team state and source quality.
- `episode`: an explicit death interval or `longest`, with neighboring minute windows and limitations. Duration does not rate error severity.

Phase/episode requests require a substantive reason and a registry of existing numeric bundles. The selected L2, or L3 and its L4 anchor, is read; hashes and dependencies on the imported signature are checked. The entire L1/raw-journal chain is not opened. This verifies the retained snapshot; later API changes require explicit collection and revision import.

`accept_lower` stores an optional structured current-Codex observation/hypothesis/interpretation, alternative, uncertainty and next check, capped at 4000 bytes. Matching question and lower-input revision reuse the accepted assessment with its addressed reference, without another model interpretation. Changed input does not reuse the old assessment as current.

## Match review through a suitable profile

`comparison.prepare_match` excludes the target from the numerical baseline and selected profile's population. It matches hero, position, mode and both source versions. Unknown versions or missing comparable history can produce an empty baseline; another hero/role is not substituted automatically.

`past_only` uses games completed strictly before the target's start and a compatible earlier profile. Target final metrics are visible: this reviews an outcome through earlier evidence, rather than forecasting. `retrospective` allows later baseline games while excluding the target and labelling hindsight. `forecast` builds only a simulation input: preceding completed games/profile, without target outcome, duration or final metrics; drilling is disabled to prevent leakage.

Position and drafts still originate from a retained postgame source; pre-match availability is not verified. The example's earlier-period profile is authored now. No mode alone establishes blind forecasting accuracy. `memory.previously_seen`, `blind=false`, and `isolated=false` retain this boundary. Current conversation memory is not isolated.

## Commands

From the repository root, without network access:

```powershell
$contractId = (Get-Content data/analysis/analyst/update.json -Raw | ConvertFrom-Json).contract_id
.\.venv\Scripts\python.exe -m src.apps.analysis.analyst.cli --db data/analysis/analyst/prototype.sqlite --output data/analysis/analyst/review.json prepare --contract $contractId --question "Review the profile using current evidence"
$reviewPacket = Get-Content data/analysis/analyst/review.json -Raw | ConvertFrom-Json
.\.venv\Scripts\python.exe -m src.apps.analysis.analyst.cli --db data/analysis/analyst/prototype.sqlite --output data/analysis/analyst/current.md report --contract $contractId --language en
```

Current Codex then reads `review.json`, optionally drills, authors a JSON response and runs `accept-profile --session <session_id> --response <file>`. Historical responses above belong to their original packets; they cannot be substituted into another packet without review. `audit --session <id>` exposes quotas, delivered card counts, evidence and assessment reuse. `profile --contract <id> --revision <revision>` reads a saved version. `match --contract <id> --match-id <id> --question <text> --mode past_only` prepares a separate session, accepted with `accept-match`.

Lower retrieval example parameters: `drill --session <id> --kind episode --target <match_id> --selector longest --reason <substantive question> --registry data/analysis/analyst/numeric-bundles.json`. The registry maps match IDs to numeric-bundle paths inside `--root`. See [lower-response.json](../../../data/prototype/analyst/lower-response.json); use `accept-lower --session <id> --ref <ref> --response <file>` to accept it.

Checks:

```powershell
.\.venv\Scripts\python.exe -m unittest tools.test_analyst_analysis tools.test_cumulative_analysis tools.test_longitudinal_analysis tools.test_spatial_analysis tools.test_numeric_analysis tools.test_analysis tools.test_analysis_series tools.test_synthesis
.\.venv\Scripts\python.exe tools/check_analyst_analysis.py verify
```

The final command verifies the already conducted local session and writes [measurements](../../../data/prototype/analyst-verification.json). **120 tests pass, including 20 new tests** covering budgets at 1000 synthetic games, persistent quotas, evidence versions/scopes, role changes, before/after values, lifecycle, assessment reuse, corrupted lower input, target/future exclusion and compatible profile periods.

The tool's `initial`, `update`, `historical`, `historical-match`, and `match` stages support a stepwise session with manually authored answers between stages. They do not automatically generate interpretations. Do not rerun the initial stage on an advanced database; use ordinary `prepare` for another review. Local databases/packets are ignored by Git. After cloning, saved task 5–7 inputs and stage execution are required; authored responses, reports and measurements are available as project artifacts.
