# Данные OpenDota: 8946760594

Source: https://api.opendota.com/api/matches/8946760594
Retrieved UTC: 2026-09-05T15:14:34.536316+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 26 |
| `teamfights` | value | 8 |
| `chat` | value | 29 |
| `pauses` | empty | 0 |
| `picks_bans` | value | 17 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 36 |
| `radiant_xp_adv` | value | 36 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 132183143 | 79 | 4/5/21 | 383 | 530 | 78 |
| 1 | 479132453 | 48 | 8/3/7 | 822 | 1103 | 558 |
| 2 | 303956511 | 135 | 10/2/16 | 632 | 884 | 278 |
| 3 | 105009388 | 71 | 7/7/23 | 431 | 653 | 96 |
| 4 | 203182675 | 60 | 14/3/16 | 614 | 868 | 245 |
| 128 | 249887924 | 128 | 3/10/9 | 407 | 419 | 188 |
| 129 | 313068594 | 14 | 3/8/10 | 245 | 313 | 29 |
| 130 | 927692834 | 2 | 5/10/8 | 283 | 326 | 37 |
| 131 | 128375702 | 11 | 5/7/5 | 535 | 665 | 315 |
| 132 | 31541645 | 26 | 1/8/10 | 345 | 429 | 158 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 14 |
| `deaths` | value | 3 |
| `assists` | value | 16 |
| `net_worth` | value | 19952 |
| `gold_per_min` | value | 614 |
| `xp_per_min` | value | 868 |
| `last_hits` | value | 245 |
| `denies` | value | 3 |
| `hero_damage` | value | 24567 |
| `tower_damage` | value | 4149 |
| `hero_healing` | zero | 0 |
| `times` | value | 36 |
| `gold_t` | value | 36 |
| `xp_t` | value | 36 |
| `lh_t` | value | 36 |
| `dn_t` | value | 36 |
| `purchase_log` | value | 41 |
| `ability_upgrades_arr` | value | 18 |
| `ability_uses` | value | 6 |
| `ability_targets` | value | 1 |
| `item_uses` | value | 15 |
| `damage_inflictor` | value | 6 |
| `damage_targets` | value | 7 |
| `kills_log` | value | 14 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 7 |
| `obs_log` | value | 1 |
| `sen_log` | value | 1 |
| `obs_left_log` | value | 1 |
| `sen_left_log` | value | 1 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 65 |
| `actions` | value | 18 |
| `pings` | value | 7 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 3 |
| `benchmarks` | value | 10 |

## Пропуски и ограничения

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `all_word_counts`, `cosmetics`, `draft_timings`, `my_word_counts`, `pauses`.
- Target player, **missing**: `additional_units`, `camps_stacked_t`, `hero_damage_t`, `hero_healing_t`, `match_id`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `neutral_tokens_log`.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
