# OpenDota data: 8943265928

Source: https://api.opendota.com/api/matches/8943265928
Retrieved UTC: 2026-09-05T15:11:29.592283+00:00

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
| `picks_bans` | value | 15 |
| `draft_timings` | missing | — |
| `radiant_gold_adv` | missing | — |
| `radiant_xp_adv` | missing | — |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 152966137 | 108 | 14/6/28 | 653 | 1119 | 378 |
| 1 | 125734100 | 131 | 6/7/26 | 322 | 693 | 57 |
| 2 | 372555550 | 71 | 16/12/19 | 556 | 799 | 258 |
| 3 | 466545053 | 67 | 19/7/27 | 814 | 1293 | 548 |
| 4 | 123845132 | 91 | 2/13/29 | 370 | 657 | 143 |
| 128 | 1121272850 | 128 | 3/10/20 | 345 | 507 | 98 |
| 129 | 328337404 | 35 | 13/12/13 | 538 | 671 | 340 |
| 130 | 203182675 | 64 | 11/13/19 | 570 | 937 | 298 |
| 131 | 81026687 | 14 | 12/8/15 | 525 | 837 | 289 |
| 132 | 296999238 | 26 | 5/15/21 | 301 | 478 | 19 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 11 |
| `deaths` | value | 13 |
| `assists` | value | 19 |
| `net_worth` | value | 23761 |
| `gold_per_min` | value | 570 |
| `xp_per_min` | value | 937 |
| `last_hits` | value | 298 |
| `denies` | value | 10 |
| `hero_damage` | value | 69388 |
| `tower_damage` | value | 7365 |
| `hero_healing` | zero | 0 |
| `times` | missing | — |
| `gold_t` | missing | — |
| `xp_t` | missing | — |
| `lh_t` | missing | — |
| `dn_t` | missing | — |
| `purchase_log` | missing | — |
| `ability_upgrades_arr` | value | 21 |
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
