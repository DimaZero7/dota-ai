# OpenDota data: 8953990641

Source: https://api.opendota.com/api/matches/8953990641
Retrieved UTC: 2026-09-05T15:17:41.381440+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **None**.
Parse status: `not_confirmed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': False, 'has_archive': False}`.

The complete response is preserved. This report describes data availability, not gameplay quality.

## Match events

| Field | State | Count |
| --- | --- | --- |
| `objectives` | missing | — |
| `teamfights` | missing | — |
| `chat` | missing | — |
| `pauses` | missing | — |
| `picks_bans` | value | 17 |
| `draft_timings` | missing | — |
| `radiant_gold_adv` | missing | — |
| `radiant_xp_adv` | missing | — |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 234993465 | 87 | 1/12/15 | 218 | 316 | 18 |
| 1 | 436401812 | 48 | 5/9/6 | 625 | 687 | 404 |
| 2 | 1876260371 | 39 | 7/3/4 | 488 | 689 | 220 |
| 3 | 178725099 | 42 | 3/7/6 | 436 | 592 | 225 |
| 4 | 277449150 | 131 | 4/6/7 | 254 | 348 | 49 |
| 128 | 203182675 | 60 | 8/5/6 | 560 | 734 | 259 |
| 129 | 105009388 | 84 | 2/5/18 | 444 | 533 | 75 |
| 130 | 2597282 | 40 | 5/2/23 | 485 | 572 | 143 |
| 131 | 1509699509 | 94 | 6/1/11 | 750 | 762 | 521 |
| 132 | 1270693641 | 14 | 13/7/11 | 592 | 724 | 184 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 8 |
| `deaths` | value | 5 |
| `assists` | value | 6 |
| `net_worth` | value | 18378 |
| `gold_per_min` | value | 560 |
| `xp_per_min` | value | 734 |
| `last_hits` | value | 259 |
| `denies` | value | 1 |
| `hero_damage` | value | 16750 |
| `tower_damage` | value | 3553 |
| `hero_healing` | value | 2 |
| `times` | missing | — |
| `gold_t` | missing | — |
| `xp_t` | missing | — |
| `lh_t` | missing | — |
| `dn_t` | missing | — |
| `purchase_log` | missing | — |
| `ability_upgrades_arr` | value | 18 |
| `ability_uses` | missing | — |
| `ability_targets` | missing | — |
| `item_uses` | missing | — |
| `damage_inflictor` | missing | — |
| `damage_targets` | missing | — |
| `kills_log` | missing | — |
| `buyback_log` | missing | — |
| `runes_log` | missing | — |
| `obs_log` | missing | — |
| `sen_log` | missing | — |
| `obs_left_log` | missing | — |
| `sen_left_log` | missing | — |
| `camps_stacked` | missing | — |
| `lane_pos` | missing | — |
| `actions` | missing | — |
| `pings` | missing | — |
| `connection_log` | missing | — |
| `neutral_tokens_log` | missing | — |
| `neutral_item_history` | missing | — |
| `benchmarks` | value | 10 |

## Gaps and limitations

- Match, **missing**: `all_word_counts`, `chat`, `comeback`, `cosmetics`, `dire_team`, `draft_timings`, `league`, `loss`, `my_word_counts`, `negative_votes`, `objectives`, `pauses`, `positive_votes`, `radiant_gold_adv`, `radiant_team`, `radiant_xp_adv`, `skill`, `teamfights`, `throw`, `version`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: —.
- Target player, **missing**: `ability_targets`, `ability_uses`, `actions`, `actions_per_min`, `additional_units`, `ancient_kills`, `buyback_count`, `buyback_log`, `camps_stacked`, `camps_stacked_t`, `connection_log`, `cosmetics`, `courier_kills`, `creeps_stacked`, `damage`, `damage_inflictor`, `damage_inflictor_received`, `damage_taken`, `damage_targets`, `dn_t`, `first_purchase_time`, `gold_reasons`, `gold_t`, `hero_damage_t`, `hero_healing_t`, `hero_hits`, `hero_kills`, `is_roaming`, `item_usage`, `item_uses`, `item_win`, `kill_streaks`, `killed`, `killed_by`, `kills_log`, `lane`, `lane_efficiency`, `lane_efficiency_pct`, `lane_kills`, `lane_pos`, `lane_role`, `lh_t`, `life_state`, `life_state_dead`, `match_id`, `max_hero_hit`, `multi_kills`, `necronomicon_kills`, `neutral_item_history`, `neutral_kills`, `neutral_tokens_log`, `obs`, `obs_left_log`, `obs_log`, `obs_placed`, `observer_kills`, `observer_uses`, `pings`, `position_est`, `purchase`, `purchase_log`, `purchase_time`, `purchase_tpscroll`, `roshan_kills`, `rune_pickups`, `runes`, `runes_log`, `sen`, `sen_left_log`, `sen_log`, `sen_placed`, `sentry_kills`, `sentry_uses`, `stuns`, `times`, `tower_kills`, `xp_reasons`, `xp_t`.
- Target player, **null**: `name`.
- Target player, **empty**: —.

missing means no key; null is an explicit null; empty is an empty collection or string; zero and false are real values. Optional schema fields need not appear, and empty event lists may mean no events occurred. The cause of gaps is not established. inventory.json describes every participant and observed nested paths. OpenDota estimates such as benchmarks and lane_efficiency are not raw events. Minute-level series do not replace a tick-level replay. A replay_url does not establish file availability.
