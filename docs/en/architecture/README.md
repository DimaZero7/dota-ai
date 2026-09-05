# Architecture

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

Each run creates a separate snapshot in `data/matches/<match_id>/opendota/<UTC>/`. `match.json` and `schema.json` retain original response bytes; `metadata.json` records provenance and status; `inventory.json` and `report.ru.md` / `report.en.md` describe coverage. Errors mark the snapshot as failed while preserving received responses. STRATZ and replay parsing are not implemented yet.

The HTTP client uses Python's standard library; no additional packages are needed for this stage. [Running](../development/README.md).
