# Данные OpenDota: 8945405839

Source: https://api.opendota.com/api/matches/8945405839
Retrieved UTC: 2026-09-05T15:13:33.963980+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 30 |
| `teamfights` | value | 11 |
| `chat` | value | 21 |
| `pauses` | value | 1 |
| `picks_bans` | value | 16 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 30 |
| `radiant_xp_adv` | value | 30 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 210978207 | 99 | 1/4/10 | 552 | 684 | 240 |
| 1 | 105009388 | 71 | 13/5/15 | 486 | 841 | 63 |
| 2 | 203182675 | 43 | 22/0/12 | 743 | 897 | 231 |
| 3 | 378416918 | 105 | 12/9/21 | 505 | 568 | 86 |
| 4 | 313039228 | 54 | 5/3/17 | 629 | 677 | 236 |
| 128 | 152220408 | 53 | 10/7/7 | 578 | 510 | 250 |
| 129 | 151909331 | 5 | 4/13/11 | 308 | 326 | 19 |
| 130 | 233182302 | 27 | 1/9/6 | 251 | 247 | 63 |
| 131 | 1179966687 | 96 | 1/13/7 | 294 | 376 | 96 |
| 132 | 451988337 | 138 | 4/12/4 | 477 | 739 | 173 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 22 |
| `deaths` | zero | 0 |
| `assists` | value | 12 |
| `net_worth` | value | 20582 |
| `gold_per_min` | value | 743 |
| `xp_per_min` | value | 897 |
| `last_hits` | value | 231 |
| `denies` | value | 5 |
| `hero_damage` | value | 32519 |
| `tower_damage` | value | 13755 |
| `hero_healing` | zero | 0 |
| `times` | value | 30 |
| `gold_t` | value | 30 |
| `xp_t` | value | 30 |
| `lh_t` | value | 30 |
| `dn_t` | value | 30 |
| `purchase_log` | value | 49 |
| `ability_upgrades_arr` | value | 18 |
| `ability_uses` | value | 7 |
| `ability_targets` | value | 2 |
| `item_uses` | value | 11 |
| `damage_inflictor` | value | 6 |
| `damage_targets` | value | 6 |
| `kills_log` | value | 22 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 11 |
| `obs_log` | value | 3 |
| `sen_log` | value | 2 |
| `obs_left_log` | value | 3 |
| `sen_left_log` | value | 2 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 100 |
| `actions` | value | 14 |
| `pings` | value | 1 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 3 |
| `benchmarks` | value | 10 |

## Пропуски и ограничения

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `cosmetics`, `draft_timings`, `my_word_counts`.
- Target player, **missing**: `additional_units`, `match_id`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `killed_by`, `neutral_tokens_log`.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
