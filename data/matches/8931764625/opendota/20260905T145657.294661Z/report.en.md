# OpenDota data: 8931764625

Source: https://api.opendota.com/api/matches/8931764625
Retrieved UTC: 2026-09-05T14:56:58.308397+00:00

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
| `picks_bans` | value | 16 |
| `draft_timings` | missing | — |
| `radiant_gold_adv` | missing | — |
| `radiant_xp_adv` | missing | — |

## All participants

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1441283624 | 105 | 20/4/18 | 716 | 1172 | 209 |
| 1 | 1703749274 | 26 | 13/2/14 | 559 | 804 | 171 |
| 2 | 1201986224 | 79 | 1/9/25 | 375 | 560 | 49 |
| 3 | 1408184967 | 54 | 12/0/11 | 724 | 949 | 313 |
| 4 | 1189883416 | 123 | 6/3/34 | 431 | 719 | 60 |
| 128 | 319896298 | 52 | 4/10/4 | 551 | 611 | 344 |
| 129 | 446064321 | 91 | 1/10/4 | 214 | 538 | 12 |
| 130 | 1657713861 | 75 | 1/11/6 | 274 | 361 | 61 |
| 131 | 203182675 | 1 | 5/12/4 | 442 | 539 | 223 |
| 132 | 127693172 | 135 | 6/10/7 | 518 | 670 | 280 |

## Target player: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 5 |
| `deaths` | value | 12 |
| `assists` | value | 4 |
| `net_worth` | value | 12569 |
| `gold_per_min` | value | 442 |
| `xp_per_min` | value | 539 |
| `last_hits` | value | 223 |
| `denies` | value | 18 |
| `hero_damage` | value | 15966 |
| `tower_damage` | zero | 0 |
| `hero_healing` | zero | 0 |
| `times` | missing | — |
| `gold_t` | missing | — |
| `xp_t` | missing | — |
| `lh_t` | missing | — |
| `dn_t` | missing | — |
| `purchase_log` | missing | — |
| `ability_upgrades_arr` | value | 17 |
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
- Target player, **empty**: `permanent_buffs`.

missing means no key; null is an explicit null; empty is an empty collection or string; zero and false are real values. Optional schema fields need not appear, and empty event lists may mean no events occurred. The cause of gaps is not established. inventory.json describes every participant and observed nested paths. OpenDota estimates such as benchmarks and lane_efficiency are not raw events. Minute-level series do not replace a tick-level replay. A replay_url does not establish file availability.
