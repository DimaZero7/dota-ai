# OpenDota data: 8948658937

Source: https://api.opendota.com/api/matches/8948658937
Retrieved UTC: 2026-09-05T15:15:46.284821+00:00

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
| `picks_bans` | value | 20 |
| `draft_timings` | missing | — |
| `radiant_gold_adv` | missing | — |
| `radiant_xp_adv` | missing | — |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1679318553 | 25 | 3/7/6 | 430 | 533 | 252 |
| 1 | 923149397 | 29 | 5/5/5 | 417 | 493 | 187 |
| 2 | 1269157390 | 41 | 4/5/6 | 477 | 559 | 275 |
| 3 | 236938763 | 50 | 0/8/13 | 224 | 396 | 42 |
| 4 | 113450549 | 26 | 4/5/6 | 214 | 333 | 25 |
| 128 | 969922573 | 129 | 7/4/14 | 546 | 593 | 177 |
| 129 | 1134647484 | 74 | 7/3/9 | 548 | 511 | 208 |
| 130 | 203182675 | 49 | 6/1/17 | 610 | 761 | 269 |
| 131 | 130637664 | 30 | 8/3/8 | 404 | 427 | 33 |
| 132 | 326585227 | 20 | 2/5/17 | 314 | 440 | 17 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 6 |
| `deaths` | value | 1 |
| `assists` | value | 17 |
| `net_worth` | value | 18955 |
| `gold_per_min` | value | 610 |
| `xp_per_min` | value | 761 |
| `last_hits` | value | 269 |
| `denies` | value | 4 |
| `hero_damage` | value | 22866 |
| `tower_damage` | value | 12273 |
| `hero_healing` | zero | 0 |
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
