# OpenDota data: 8954535280

Source: https://api.opendota.com/api/matches/8954535280
Retrieved UTC: 2026-09-05T15:18:23.605113+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

The complete response is preserved. This report describes data availability, not gameplay quality.

## Match events

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 23 |
| `teamfights` | value | 5 |
| `chat` | value | 39 |
| `pauses` | empty | 0 |
| `picks_bans` | value | 16 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 37 |
| `radiant_xp_adv` | value | 37 |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 378308848 | 54 | 18/0/19 | 716 | 863 | 286 |
| 1 | 61068821 | 21 | 8/3/17 | 493 | 659 | 190 |
| 2 | 910581197 | 86 | 10/4/26 | 536 | 811 | 119 |
| 3 | 148429689 | 26 | 10/5/22 | 504 | 796 | 145 |
| 4 | 1084627968 | 135 | 7/8/30 | 436 | 643 | 140 |
| 128 | 105009388 | 71 | 8/14/8 | 303 | 410 | 67 |
| 129 | 203182675 | 1 | 5/12/4 | 389 | 503 | 191 |
| 130 | 188246554 | 64 | 1/10/8 | 278 | 291 | 65 |
| 131 | 175971366 | 25 | 5/8/0 | 589 | 724 | 394 |
| 132 | 126013234 | 7 | 1/9/10 | 331 | 408 | 158 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 5 |
| `deaths` | value | 12 |
| `assists` | value | 4 |
| `net_worth` | value | 11948 |
| `gold_per_min` | value | 389 |
| `xp_per_min` | value | 503 |
| `last_hits` | value | 191 |
| `denies` | value | 8 |
| `hero_damage` | value | 13451 |
| `tower_damage` | value | 162 |
| `hero_healing` | zero | 0 |
| `times` | value | 37 |
| `gold_t` | value | 37 |
| `xp_t` | value | 37 |
| `lh_t` | value | 37 |
| `dn_t` | value | 37 |
| `purchase_log` | value | 33 |
| `ability_upgrades_arr` | value | 17 |
| `ability_uses` | value | 4 |
| `ability_targets` | value | 1 |
| `item_uses` | value | 10 |
| `damage_inflictor` | value | 4 |
| `damage_targets` | value | 4 |
| `kills_log` | value | 5 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 9 |
| `obs_log` | value | 1 |
| `sen_log` | value | 1 |
| `obs_left_log` | value | 1 |
| `sen_left_log` | value | 1 |
| `camps_stacked` | value | 1 |
| `lane_pos` | value | 80 |
| `actions` | value | 14 |
| `pings` | value | 2 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 3 |
| `benchmarks` | value | 10 |

## Gaps and limitations

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `cosmetics`, `draft_timings`, `my_word_counts`, `pauses`.
- Target player, **missing**: `additional_units`, `camps_stacked_t`, `hero_damage_t`, `hero_healing_t`, `match_id`, `purchase_ward_observer`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `kill_streaks`, `multi_kills`, `neutral_tokens_log`, `permanent_buffs`.

missing means no key; null is an explicit null; empty is an empty collection or string; zero and false are real values. Optional schema fields need not appear, and empty event lists may mean no events occurred. The cause of gaps is not established. inventory.json describes every participant and observed nested paths. OpenDota estimates such as benchmarks and lane_efficiency are not raw events. Minute-level series do not replace a tick-level replay. A replay_url does not establish file availability.
