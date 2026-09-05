# Architecture

[Contents](../README.md)

The `src/apps/matches/` application selects and preserves a match:

- `clients.py` — OpenDota HTTP requests with a timeout and error handling.
- `services.py` — completed-match selection, participation verification, context lookup, and persistence.
- `exceptions.py` — match selection errors.
- `cli.py` — loading configuration through `src/settings.py`, invoking the service, and presenting output.

Context is stored in `data/selected_match.json`. Subsequent calls reuse the saved match. The selected raw history entry is separate from context fields; source URLs and data limitations are included. Full statistics collection, STRATZ, and replay parsing are not implemented yet.

The HTTP client uses Python's standard library; no additional packages are needed for this stage. [Running](../development/README.md).
