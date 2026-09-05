# Данные OpenDota: 8959457705

Source: https://api.opendota.com/api/matches/8959457705
Retrieved UTC: 2026-09-05T10:33:38.280389+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **None**.
Parse status: `not_confirmed`. `od_data`: `{'has_api': True, 'has_gcdata': False, 'has_parsed': False, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

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

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | None | 14 | 5/13/14 | 304 | 471 | 104 |
| 1 | 367873824 | 120 | 5/7/18 | 630 | 838 | 358 |
| 2 | 131819683 | 11 | 7/7/8 | 653 | 960 | 518 |
| 3 | 131839338 | 74 | 8/6/13 | 536 | 775 | 300 |
| 4 | 1024427021 | 9 | 4/10/13 | 339 | 406 | 111 |
| 128 | None | 7 | 13/8/16 | 627 | 836 | 321 |
| 129 | 203182675 | 64 | 4/10/14 | 479 | 705 | 244 |
| 130 | 124649983 | 63 | 8/5/22 | 407 | 642 | 113 |
| 131 | 154266644 | 1 | 7/4/7 | 711 | 965 | 513 |
| 132 | 208185952 | 86 | 10/5/16 | 601 | 906 | 297 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 4 |
| `deaths` | value | 10 |
| `assists` | value | 14 |
| `net_worth` | value | 20750 |
| `gold_per_min` | value | 479 |
| `xp_per_min` | value | 705 |
| `last_hits` | value | 244 |
| `denies` | value | 2 |
| `hero_damage` | value | 22556 |
| `tower_damage` | value | 4754 |
| `hero_healing` | value | 194 |
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

## Пропуски и ограничения

- Match, **missing**: `all_word_counts`, `chat`, `comeback`, `cosmetics`, `dire_team`, `draft_timings`, `league`, `loss`, `my_word_counts`, `negative_votes`, `objectives`, `pauses`, `positive_votes`, `radiant_gold_adv`, `radiant_team`, `radiant_xp_adv`, `replay_salt`, `replay_url`, `series_id`, `series_type`, `skill`, `teamfights`, `throw`, `version`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: —.
- Target player, **missing**: `ability_targets`, `ability_uses`, `actions`, `actions_per_min`, `additional_units`, `ancient_kills`, `buyback_count`, `buyback_log`, `camps_stacked`, `camps_stacked_t`, `connection_log`, `cosmetics`, `courier_kills`, `creeps_stacked`, `damage`, `damage_inflictor`, `damage_inflictor_received`, `damage_taken`, `damage_targets`, `dn_t`, `first_purchase_time`, `gold_reasons`, `gold_t`, `hero_damage_t`, `hero_healing_t`, `hero_hits`, `hero_kills`, `is_roaming`, `item_usage`, `item_uses`, `item_win`, `kill_streaks`, `killed`, `killed_by`, `kills_log`, `lane`, `lane_efficiency`, `lane_efficiency_pct`, `lane_kills`, `lane_pos`, `lane_role`, `lh_t`, `life_state`, `life_state_dead`, `match_id`, `max_hero_hit`, `multi_kills`, `necronomicon_kills`, `neutral_item_history`, `neutral_kills`, `neutral_tokens_log`, `obs`, `obs_left_log`, `obs_log`, `obs_placed`, `observer_kills`, `observer_uses`, `party_id`, `permanent_buffs`, `pings`, `position_est`, `purchase`, `purchase_log`, `purchase_time`, `purchase_tpscroll`, `roshan_kills`, `rune_pickups`, `runes`, `runes_log`, `sen`, `sen_left_log`, `sen_log`, `sen_placed`, `sentry_kills`, `sentry_uses`, `stuns`, `times`, `tower_kills`, `xp_reasons`, `xp_t`.
- Target player, **null**: `name`.
- Target player, **empty**: —.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
