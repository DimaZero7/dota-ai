# OpenDota data: 8960626424

Source: https://api.opendota.com/api/matches/8960626424
Retrieved UTC: 2026-09-05T09:04:15.857447+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

The complete response is preserved. This report describes data availability, not gameplay quality.

## Match events

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 31 |
| `teamfights` | value | 8 |
| `chat` | value | 47 |
| `pauses` | value | 8 |
| `picks_bans` | value | 18 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 53 |
| `radiant_xp_adv` | value | 53 |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 203182675 | 43 | 7/8/13 | 652 | 780 | 504 |
| 1 | 201800977 | 36 | 15/4/10 | 853 | 1260 | 633 |
| 2 | 174798613 | 88 | 3/7/24 | 322 | 693 | 56 |
| 3 | 119860878 | 145 | 20/7/13 | 810 | 1228 | 558 |
| 4 | 1453342087 | 155 | 0/5/33 | 362 | 851 | 94 |
| 128 | 923211683 | 48 | 6/6/13 | 809 | 1111 | 756 |
| 129 | 134191442 | 128 | 8/8/18 | 458 | 681 | 121 |
| 130 | 162887818 | 2 | 8/16/8 | 524 | 692 | 364 |
| 131 | 1176829604 | 20 | 2/9/19 | 377 | 632 | 167 |
| 132 | 204885882 | 47 | 5/6/14 | 549 | 718 | 359 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 7 |
| `deaths` | value | 8 |
| `assists` | value | 13 |
| `net_worth` | value | 30889 |
| `gold_per_min` | value | 652 |
| `xp_per_min` | value | 780 |
| `last_hits` | value | 504 |
| `denies` | value | 11 |
| `hero_damage` | value | 28604 |
| `tower_damage` | value | 9740 |
| `hero_healing` | zero | 0 |
| `times` | value | 53 |
| `gold_t` | value | 53 |
| `xp_t` | value | 53 |
| `lh_t` | value | 53 |
| `dn_t` | value | 53 |
| `purchase_log` | value | 57 |
| `ability_upgrades_arr` | value | 19 |
| `ability_uses` | value | 6 |
| `ability_targets` | value | 2 |
| `item_uses` | value | 14 |
| `damage_inflictor` | value | 6 |
| `damage_targets` | value | 6 |
| `kills_log` | value | 7 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 11 |
| `obs_log` | value | 2 |
| `sen_log` | value | 2 |
| `obs_left_log` | value | 2 |
| `sen_left_log` | value | 2 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 83 |
| `actions` | value | 17 |
| `pings` | value | 2 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 4 |
| `benchmarks` | value | 10 |

## Gaps and limitations

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `cosmetics`, `draft_timings`, `my_word_counts`.
- Target player, **missing**: `additional_units`, `match_id`, `purchase_gem`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `neutral_tokens_log`.

missing means no key; null is an explicit null; empty is an empty collection or string; zero and false are real values. Optional schema fields need not appear, and empty event lists may mean no events occurred. The cause of gaps is not established. inventory.json describes every participant and observed nested paths. OpenDota estimates such as benchmarks and lane_efficiency are not raw events. Minute-level series do not replace a tick-level replay. A replay_url does not establish file availability.
