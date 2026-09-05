# Running the analysis prototype

[Level 0–6 examples](prototype-examples.md) · [Contracts](../architecture/analysis-levels.md)

Run commands from the repository root using local Python 3.14.7. Settings come from `src/config.toml`, falling back to `src/default_config.toml`. The prototype uses the standard library and existing `toml==0.10.2`; no separate model API or new dependencies.

## Data and execution

The sample contains five matches for account 203182675: the frozen original and four subsequent entries in the latest available history. [Manifest and drafts](../../../data/prototype_matches.json). The hard limit is ten distinct matches; `data/selected_match.json` is preserved.

```powershell
# Only when local raw responses are missing; accesses the free APIs.
.\.venv\Scripts\python.exe -m src.apps.analysis.cli sample --total 5

# Local snapshots only; no network.
.\.venv\Scripts\python.exe -m src.apps.analysis.cli build --match-id 8960626424
.\.venv\Scripts\python.exe -m src.apps.analysis.cli series
```

Collection requires the configured STRATZ token. It resumes the saved manifest; increasing `--total` appends subsequent available matches without outcome/hero filtering. Existing complete snapshots are reused. The union of manifest IDs and local match directories must stay within ten. Reducing `--total` does not delete matches. The service does not request replay parsing, upgrade billing, or retry failed requests automatically.

Raw JSON is ignored by Git. After cloning, `sample` fetches new snapshots for the saved IDs. Historical example references require the original local responses with matching SHA-256; fresh API responses may differ.

## Current Codex file exchange

The CLI computes facts and exports a bounded packet. Current Codex reads it and produces structured findings following `response_contract`. The response is a separate JSON file validated for IDs, status and size. This is session file exchange, not an automatic model call or a template presented as model output. Actual saved interpretations are in `data/prototype/examples/`.

```powershell
.\.venv\Scripts\python.exe -m src.apps.analysis.cli packet --match-id 8960626424
.\.venv\Scripts\python.exe -m src.apps.analysis.cli packet --series --finding cohort:7a16d9c348bbb53d
.\.venv\Scripts\python.exe -m src.apps.analysis.cli packet --series --focus-match-ids 8959040566 8958839199 --question 'Evaluate only the Jakiro POSITION_2 exercise; no meta.'
.\.venv\Scripts\python.exe -m src.apps.analysis.cli detail --match-id 8959040566 --start 266 --end 372 --slot 0 --kinds kill,death,buyback --fields time,target,attacker,timeDead --session jakiro-review

# Substitute the actual packet and Codex response paths.
.\.venv\Scripts\python.exe -m src.apps.analysis.cli import-review --packet data/analysis/PACKET.json --response data/analysis/RESPONSE.json --session jakiro-review
```

Finding IDs are in the output `registry`. Python services `get_finding`, `list_children`, and `query_events` provide ID lookup, child pagination and event retrieval by interval, slot, kinds and selected fields. Extend an interval with another request. `next_offset` explicitly identifies unread events; CLI `--offset` continues a page.

Drill state persists between calls: three requests and 8000 response bytes per session. Exhaustion returns `budget_exhausted` and unresolved questions. A new `--session` name starts a new analysis; changed sources/rules require a new session. Valid pointers and schema do not establish semantic truth.

## Budget and persistence

The default 24000-byte UTF-8 budget reserves 11000 for initial input, 8000 for detail, 4000 for the answer and 1000 for overhead. `--budget-bytes` explicitly changes the total. Oversized packets fail. Purchase/child previews disclose omitted counts. `--focus-match-ids` explicitly lists omitted match contexts; request their drafts before interpreting those games in detail.

The exact tokenizer, token usage and full current-session overhead are unavailable to Python. `measured_model_tokens=null`. The byte guard bounds prepared data, not the entire Codex conversation. This experiment does not establish token savings or increased model accuracy.

Ignored `data/analysis/` stores match artifacts, series, packets, answers, drill sessions and profile history. Cache keys include source hashes, parameters, hero labels and analysis code. Code changes rebuild whole matches; per-episode invalidation is not implemented. Previous versions remain available and corrupt caches fail explicitly. Codex responses are not automatically reused with changed packets.

`save_profile_version` preserves previous revisions, sources and changed conditions. `evaluate_followup` requires compatible games newer than the baseline and rejects baseline reuse. Its result can be stored in a new profile revision through the history service. Future collection is not automatic; the current exercise is `untested`.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest tools.test_analysis tools.test_analysis_series
.\.venv\Scripts\python.exe -m tools.check_analysis
.\.venv\Scripts\python.exe -m compileall -q src tools
```

13 tests cover contracts, field states, budgets, correlated windows, incompatible roles, missing data, history, corrupt evidence and follow-up constraints. Synthetic data is confined to tests. The separate real-data check performs 40 checks, verifies the 0–6 graph and reuse, exports seven packets and verifies two drills. It does not generate new model answers.

[Acceptance result](../../../data/prototype/end-to-end.json) lists synthetic-only scenarios separately. Pointer semantics are sampled once per event kind, not independently verified for every provider event. Current-session interpretation is not blind: the assistant also inspected source data.
