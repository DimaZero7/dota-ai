# Данные OpenDota: 8935744163

Source: https://api.opendota.com/api/matches/8935744163
Retrieved UTC: 2026-09-05T15:02:28.253392+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 28 |
| `teamfights` | value | 8 |
| `chat` | value | 30 |
| `pauses` | empty | 0 |
| `picks_bans` | value | 17 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 31 |
| `radiant_xp_adv` | value | 31 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 56089947 | 14 | 20/6/16 | 552 | 636 | 114 |
| 1 | 1084409317 | 86 | 7/4/28 | 431 | 520 | 65 |
| 2 | 1013388444 | 92 | 12/3/12 | 562 | 657 | 118 |
| 3 | 1259581593 | 21 | 7/3/17 | 374 | 509 | 56 |
| 4 | 317159211 | 48 | 1/1/10 | 671 | 688 | 366 |
| 128 | 216723127 | 74 | 3/10/4 | 267 | 303 | 45 |
| 129 | 370933458 | 119 | 3/13/11 | 296 | 385 | 53 |
| 130 | 812885513 | 6 | 1/12/5 | 365 | 438 | 166 |
| 131 | 135587563 | 42 | 2/3/6 | 472 | 576 | 216 |
| 132 | 203182675 | 43 | 8/9/3 | 468 | 518 | 132 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 8 |
| `deaths` | value | 9 |
| `assists` | value | 3 |
| `net_worth` | value | 11775 |
| `gold_per_min` | value | 468 |
| `xp_per_min` | value | 518 |
| `last_hits` | value | 132 |
| `denies` | value | 5 |
| `hero_damage` | value | 16965 |
| `tower_damage` | value | 2019 |
| `hero_healing` | zero | 0 |
| `times` | value | 31 |
| `gold_t` | value | 31 |
| `xp_t` | value | 31 |
| `lh_t` | value | 31 |
| `dn_t` | value | 31 |
| `purchase_log` | value | 41 |
| `ability_upgrades_arr` | value | 16 |
| `ability_uses` | value | 5 |
| `ability_targets` | value | 2 |
| `item_uses` | value | 14 |
| `damage_inflictor` | value | 6 |
| `damage_targets` | value | 6 |
| `kills_log` | value | 8 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 9 |
| `obs_log` | value | 2 |
| `sen_log` | value | 2 |
| `obs_left_log` | value | 2 |
| `sen_left_log` | value | 2 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 96 |
| `actions` | value | 14 |
| `pings` | value | 8 |
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
