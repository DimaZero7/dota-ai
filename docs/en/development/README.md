# Development and validation

Implemented [incremental statistics updates](cumulative-analysis.md): transactional storage, contribution corrections, recent windows and 1000+10 verification without earlier source events.

Implemented [longitudinal L5 statistics](longitudinal-analysis.md): conditional distributions, sessions, recent changes and association screening with bounded analyst input.

Implemented [spatial statistics and heatmaps](spatial-analysis.md): presence, resources, participation, deaths, routes and L5 groups.

[Numeric L1–L4 without mandatory model responses](numeric-analysis.md) are implemented: commands, ten-match tables and verification.

[Contents](../README.md)

## Match selection

Set the player in the local `src/config.toml`:

```toml
[player]
dotabuff_url = "https://ru.dotabuff.com/players/203182675"
account_id = 203182675
```

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m src.apps.matches.cli
```

If `data/selected_match.json` does not exist, the command reads OpenDota's available recent history, selects the latest completed match by start time, verifies the player's participation, and saves its context. Internet access is required; an API key is not. Request and validation errors produce a nonzero exit code.

If the file already exists, the command prints the saved selection without network requests. It never automatically replaces the match; changing it for the current comparison requires the user's agreement. A different configured account causes an error.

Output: [saved match](../../../data/selected_match.json), including source, check time, hero, mode, duration, and patch. This is the latest match in OpenDota's available history, which may lag behind actual play. The exact letter subpatch has not been established.

Verification covered a live OpenDota response, offline reuse, unsorted history, exclusion of future matches, and errors for empty history, mismatched participants, conflicting context, and a corrupt saved record.

## Detailed OpenDota data

After freezing the match, run:

```powershell
.\.venv\Scripts\python.exe -m src.apps.opendota.cli
```

The command uses the configured account_id and existing `data/selected_match.json`, fetching the full `/matches/{match_id}` response and API schema. Free access requires no key. Each run sends new requests and creates a separate snapshot; previous snapshots and the selection are preserved. Remaining quota headers are recorded in metadata; errors are not retried automatically.

The selected match is already parsed (`has_parsed=true`, version=22), so no repeat parse was requested. If parsing is not confirmed in a future response, the command preserves the response and report with `needs_parse_review` status and exit code 2; automatic parse queue submission is not implemented. Errors return 1 and completed collection returns 0.

Result: [OpenDota report](../../../data/matches/8960626424/opendota/20260905T090414.607209Z/report.en.md). Raw JSON includes all participants; inventory.json lists fields and observed nested paths. The report distinguishes observed events from service estimates and lists gaps. The preserved replay URL has not been checked.

Verification covered a live request, raw response hashes and sizes, all participants, byte preservation, distinct value states, rejection of a different match or conflicting context, separate snapshots on reruns, and explicit incomplete and failed statuses. Match selection regression checks also passed. Check syntax offline with:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src
```

## STRATZ

Sign in through Steam on the [STRATZ API page](https://stratz.com/api) and save the available free token in local `src/config.toml`:

```toml
[stratz]
token = "YOUR_TOKEN"
```

Do not put the token in default_config.toml, queries, or reports. Local config.toml is excluded from Git. Run:

```powershell
.\.venv\Scripts\python.exe -m src.apps.stratz.cli
```

For the current match, the command reads the frozen selection and sends 13 sequential queries: schema, overview, all-player statistics, and playback for each of 10 participants. Requests are spaced by 1.1 seconds. Observed limits on 2026-09-05 were 8/second, 150/minute, 1500/hour, and 15000/day. Limits may change; response headers are retained. There are no automatic retries or plan upgrades.

Each run creates a separate snapshot. Exit code 0 means collection completed, 2 means partial data with GraphQL errors/missing requested participants, and 1 means failure. Null and empty events alone are not failures. Reports compare final statistics against the latest complete local OpenDota snapshot of the same match, if its raw JSON is available.

[STRATZ result](../../../data/matches/8960626424/stratz/20260905T091417.870926Z/report.en.md). Large match.json, schema.json, and inventory.json files are ignored by Git; rerun collection after cloning to obtain them. Queries, small metadata, and reports are retained in the repository. Playback data is not a downloaded full replay.

Verification covered 13 live responses, hashes, all participants, absence of the token in artifacts, value states, schema-driven queries, partial GraphQL errors, stopping after HTTP 429, and unchanged match selection. Use the compileall command above for syntax validation.


## Analysis 0–6

**Current result:** [personal profile](player-profile.md), [profile-conditioned match review](profile-match-review.md), [analyst workflow and propagation](synthesis.md).

[Commands, Codex exchange and verification](analysis.md). [Real examples at all seven levels](prototype-examples.md).

[Analysis of the ten latest available games](latest-ten-analysis.md): gameplay findings, verified episodes and current prototype limitations.
