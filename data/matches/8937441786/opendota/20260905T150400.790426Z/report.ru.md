# Данные OpenDota: 8937441786

Source: https://api.opendota.com/api/matches/8937441786
Retrieved UTC: 2026-09-05T15:04:02.020253+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 24 |
| `teamfights` | value | 7 |
| `chat` | value | 35 |
| `pauses` | value | 1 |
| `picks_bans` | value | 16 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 28 |
| `radiant_xp_adv` | value | 28 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1106913157 | 128 | 8/5/20 | 426 | 536 | 43 |
| 1 | 79018612 | 104 | 13/3/11 | 686 | 721 | 196 |
| 2 | 113006693 | 22 | 2/3/21 | 354 | 438 | 48 |
| 3 | 151648511 | 54 | 4/1/10 | 572 | 649 | 218 |
| 4 | 203182675 | 43 | 12/1/9 | 720 | 812 | 228 |
| 128 | 313741354 | 129 | 2/4/3 | 372 | 405 | 150 |
| 129 | 406427598 | 64 | 1/9/4 | 194 | 255 | 29 |
| 130 | 67860253 | 20 | 1/10/5 | 370 | 377 | 174 |
| 131 | 441174252 | 74 | 4/7/2 | 445 | 576 | 176 |
| 132 | 187690486 | 85 | 5/10/5 | 334 | 353 | 45 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 12 |
| `deaths` | value | 1 |
| `assists` | value | 9 |
| `net_worth` | value | 18730 |
| `gold_per_min` | value | 720 |
| `xp_per_min` | value | 812 |
| `last_hits` | value | 228 |
| `denies` | value | 3 |
| `hero_damage` | value | 22585 |
| `tower_damage` | value | 14820 |
| `hero_healing` | zero | 0 |
| `times` | value | 28 |
| `gold_t` | value | 28 |
| `xp_t` | value | 28 |
| `lh_t` | value | 28 |
| `dn_t` | value | 28 |
| `purchase_log` | value | 48 |
| `ability_upgrades_arr` | value | 18 |
| `ability_uses` | value | 6 |
| `ability_targets` | value | 3 |
| `item_uses` | value | 11 |
| `damage_inflictor` | value | 5 |
| `damage_targets` | value | 5 |
| `kills_log` | value | 12 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 10 |
| `obs_log` | value | 3 |
| `sen_log` | value | 2 |
| `obs_left_log` | value | 3 |
| `sen_left_log` | value | 2 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 85 |
| `actions` | value | 15 |
| `pings` | value | 12 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 2 |
| `benchmarks` | value | 10 |

## Пропуски и ограничения

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `cosmetics`, `draft_timings`, `my_word_counts`.
- Target player, **missing**: `additional_units`, `match_id`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `neutral_tokens_log`, `permanent_buffs`.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
