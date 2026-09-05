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
