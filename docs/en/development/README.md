# Development and validation

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
