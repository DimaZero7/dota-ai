# Architecture

[Numeric L1–L4 without mandatory model responses](../development/numeric-analysis.md) are implemented: commands, ten-match tables and verification.

Next-version design: [cumulative statistics and numeric contracts](cumulative-statistics.md). Task 4 catalogue and audit are complete; [numeric L1–L4 are implemented](../development/numeric-analysis.md), spatial task 6 is also complete, with tasks 7–10 still ahead. The authored chain below remains the running task 3 version.

[Contents](../README.md)

The `src/apps/matches/` application selects and preserves a match:

- `clients.py` — an adapter from the shared OpenDota client to match selection errors.
- `services.py` — completed-match selection, participation verification, context lookup, and persistence.
- `exceptions.py` — match selection errors.
- `cli.py` — loading configuration through `src/settings.py`, invoking the service, and presenting output.

Context is stored in `data/selected_match.json`. Subsequent calls reuse the saved match. The selected raw history entry is separate from context fields; source URLs and data limitations are included.

The `src/apps/opendota/` application collects detailed data for this match:

- `clients.py` — HTTP client with timeouts, timestamps, SHA-256, and quota headers; also used by match selection.
- `services.py` — match and participant validation, raw response and API schema preservation, parse status inspection, and report generation.
- `inventory.py` — field and nested path inventory distinguishing missing keys, null, empty collections, zero, and false; RU/EN reports.
- `exceptions.py` and `cli.py` — integration errors and the entry point.

Each run creates a separate snapshot in `data/matches/<match_id>/opendota/<UTC>/`. `match.json` and `schema.json` retain original response bytes; `metadata.json` records provenance and status; `inventory.json` and `report.ru.md` / `report.en.md` describe coverage. Errors mark the snapshot as failed while preserving received responses.

The `src/apps/stratz/` application collects STRATZ data for the same match. `clients.py` handles Bearer authentication, HTTP, and quota headers; `queries.py` builds queries from the saved GraphQL schema; `services.py` preserves responses and merges participants by playerSlot with identity validation; `reports.py` inventories coverage and compares final statistics with OpenDota; `cli.py` supplies dependencies. Queries stay within match data; profile, reference, and other-match aggregate relationships are listed as not_requested.

STRATZ snapshots live in `data/matches/<match_id>/stratz/<UTC>/`. Query subdirectories retain GraphQL, variables.json, and raw match.json (schema.json for introspection). Root match.json is a merged representation, not a raw response; metadata.json records provenance. GraphQL errors are preserved alongside partial data; HTTP errors stop collection without automatic retries. Replay acquisition and a custom parser are outside the current task. [Source comparison and recommendation](data-sources.md).

The HTTP client uses Python's standard library; no additional packages are needed for this stage. [Running](../development/README.md).


`src/apps/analysis/` implements local [levels 0–6](analysis-levels.md). `services.py` summarizes episodes, stages and matches; `pipeline.run_match` orchestrates lower levels; `series.run_series` builds patterns and the profile. Dependencies and paths are explicit service inputs. `cli.py` loads settings and invokes these operations. [Examples](../development/prototype-examples.md).
