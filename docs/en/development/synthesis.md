# Analyst-authored bottom-up synthesis

[Personal profile](player-profile.md) · [Profile-conditioned match review](profile-match-review.md) · [Verified run](../../../data/prototype/synthesis/verification.json)

Current Codex is the analyst. Software preserves sources, calculates measurements, prepares bounded packets and checks dependencies. It does not infer playing style from thresholds or generate coaching text for the model. Every L2–L6 example was authored by current Codex after examining lower material. Replaying stored responses is not new analysis.

## Correction after user feedback

The first version stored Codex responses separately from the numerical pipeline. Cross-match synthesis depended almost entirely on deaths after kills, and a mismatched kill journal excluded the only loss from its old profile. A structurally correct graph therefore did not produce a useful personal portrait. Previous `series`, `profile.py` and `patterns.py` remain historical numerical screening, not the current player profile.

The replacement links L0 source responses → L1 measurement windows → L2 sequence interpretations → L3 phase explanations → L4 personal match explanations → L5 conditional cross-match patterns → L6 portrait and priorities. Parent packets contain accepted analyses from the immediately lower level; they do not automatically receive raw events.

For example, personal/team economy diverges in the Jakiro loss (L1). The local interpretation distinguishes personal success from team position (L2); the phase identifies the continuing divergence (L3); the match explains substantial involvement without sufficient team progression (L4). Other Jakiro games challenge the idea that more participation would fix it (L5). The profile therefore focuses development on selecting the next team task (L6). This is an interpretation chain, not a causal proof; hypotheses retain their status.

## The implemented example

The same ten matches were reused without network calls, replays or meta. Each has four packets: through 10:00 inclusive; the transition through 20:00 inclusive; development after twenty minutes; and a selected problematic or positive control window. Event intervals are half-open. These are comparison windows, not automatically detected strategic or laning boundaries.

Forty L2 interpretations become twenty L3 phases, ten L4 matches, five L5 dimensions and one L6 profile. The main graph contains 116 L1–L6 nodes; L0 consists of original response references beneath L1. Critical windows may overlap development summaries and are not independent additional cases. Economic observations span the game, while decision analysis remains selective.

The five dimensions are early resource foundation, Jakiro involvement, team results of activity, re-entry under pressure, and role applicability. Every match contributes to at least one dimension. Hero, estimated position and both drafts survive into match explanations; L5 states its conditions. A bad metric does not discard the entire match: the loss retains final K+A and economy while its incomplete kill journal is excluded from precise event frequencies.

A separate baseline uses the other nine games for match application. The service rejects a target already present in profile evidence and accepts at most three selected L4 comparisons. This is profile application, not a seventh hierarchy level. It is retrospective: the analyst already saw the loss, some baseline games are later, and all nine baseline games are wins. It is neither blind validation nor a prediction test.

## Commands and callable services

Run from the repository root with the existing Python 3.14.7 `.venv`; no dependencies were added.

```powershell
# Replay this exact saved example; does not request a new model analysis.
.\.venv\Scripts\python.exe -m tools.replay_player_analysis

.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node player:203182675:L6:profile
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node series:L5:team_result
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node 8957325148:L4:match
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node 8957325148:L3:late
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node 8957325148:L2:critical
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli show --node 8957325148:facts:critical

.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli prepare --node review:match --level 4 --children 8957325148:L3:early 8957325148:L3:late --question 'Explain personal play and contradictions between phases.'

# Substitute the real packet path and the response written by Codex.
.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli accept --packet data/analysis/synthesis/current/packets/ID.json --response data/analysis/response.json

.\.venv\Scripts\python.exe -m src.apps.analysis.synthesis_cli check --node player:203182675:L6:profile --verify-sources
.\.venv\Scripts\python.exe -m unittest tools.test_analysis tools.test_analysis_series tools.test_synthesis
```

Callable services are `prepare_analysis`, `accept_analysis`, `read_analysis`, `validate_analysis` in `src.apps.analysis.synthesis` (also exported through `services.py`); `prepare_match_dossiers` in `dossiers`; and `prepare_match_review`/`accept_match_review` in `match_review`. The application takes an L6 profile, a separate L4 match and selected comparisons. No HTTP framework or paid model API is connected.

A response includes `packet_id`, `author="current Codex"`, `summary`, `scope`, `not_established`, and one to six `claims`. Each claim has `statement`, `kind` (`observation`, `interpretation`, `hypothesis`), immediate-child `basis` IDs, `why`, `alternative`, and `check`. L6 additionally requires one to three `priorities` containing action, reason, baseline, check and basis. [Saved responses](../../../data/prototype/synthesis/) show the exact format; authored machine-readable examples are Russian, while user-facing reports and documentation are available in both languages.

Missing lower responses return `Awaiting analyst review`. Revising a child makes dependent analyses stale and requires another analyst pass; history is preserved. Recomputed measurements change revision when their payload or references change. Bump `synthesis.VERSION` when changing synthesis rules; previous graphs are then rejected. Import checks format, references, versions and size, not semantic truth.

Packets and versions live in ignored `data/analysis/synthesis/`. Git retains small authored responses, recipes and reports. Exact replay after cloning requires original source snapshots with their original hashes. Missing derived caches are rebuilt from local sources. A changed API response may require new analysis; replay neither downloads it nor silently rebinds old interpretations.

## Method critique and limits

| Measurement | Supported use | Not established |
| --- | --- | --- |
| Ten-minute economy | Same-position difference, observation at most 5 seconds old | Lane victory, draft difficulty, individual skill |
| Final K+A / team kills | Involvement in kills | All attended fights, timing, decision quality |
| Building damage | One result of contribution, conditioned on composition | Missed available objectives or full map control |
| Repeated deaths | Candidates for examining re-entry | Error frequency without opportunity denominator, an available escape |
| Restored contribution | Gameplay involvement continues | Tilt, intentions or psychological resilience |

The old ninety-second death-after-kill metric does not drive the new profile. Without an appropriate comparison, handling correlated windows and incomplete journals, it is too weak for a personal characterization.

Validation includes twenty automated tests and clean replay of 82 authored responses: 76 in the main chain and six additional baseline responses. Replay verifies original hashes and immediate dependencies; tests cover missing/stale reviews, bad-metric limitations, level skipping and target leakage into the baseline. Corruption/error cases use synthetic fixtures. These checks do not automatically prove usefulness or truth.

Actual inputs range from 3,198 to 25,272 UTF-8 bytes under a 32,000-byte input limit; the profile packet is 20,769 bytes and match application 17,921. Answer reserve is 16,000 bytes and drill reserve 8,000; existing bounded `detail`/`DrillSession` handles event retrieval. Exact tokens are unknown. Packet size is bounded, not the entire current conversation: Codex retains previously seen context. This run does not establish model quality under fully isolated packets.

The revision supplies a working personal portrait and focused development questions. Available alternatives before a specific death and the effect of exercises remain unestablished. The prototype does not yet explain every player decision from statistics.
