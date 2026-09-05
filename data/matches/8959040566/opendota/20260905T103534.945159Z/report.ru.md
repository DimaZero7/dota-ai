# Данные OpenDota: 8959040566

Source: https://api.opendota.com/api/matches/8959040566
Retrieved UTC: 2026-09-05T10:35:35.611886+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 21 |
| `teamfights` | value | 11 |
| `chat` | value | 26 |
| `pauses` | empty | 0 |
| `picks_bans` | value | 19 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 38 |
| `radiant_xp_adv` | value | 38 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 203182675 | 64 | 12/3/20 | 644 | 964 | 291 |
| 1 | 1036699266 | 62 | 5/5/32 | 498 | 774 | 37 |
| 2 | 457846707 | 97 | 12/5/20 | 581 | 811 | 249 |
| 3 | 161290149 | 6 | 15/6/12 | 751 | 949 | 369 |
| 4 | 1045938991 | 9 | 12/4/25 | 506 | 694 | 148 |
| 128 | 300386472 | 14 | 6/16/5 | 397 | 503 | 173 |
| 129 | 782399412 | 85 | 4/16/9 | 307 | 400 | 76 |
| 130 | 390878677 | 67 | 4/8/5 | 500 | 714 | 326 |
| 131 | 1299449509 | 91 | 4/10/4 | 450 | 660 | 255 |
| 132 | 241495613 | 105 | 4/8/7 | 268 | 381 | 80 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 12 |
| `deaths` | value | 3 |
| `assists` | value | 20 |
| `net_worth` | value | 22449 |
| `gold_per_min` | value | 644 |
| `xp_per_min` | value | 964 |
| `last_hits` | value | 291 |
| `denies` | value | 11 |
| `hero_damage` | value | 29042 |
| `tower_damage` | value | 2128 |
| `hero_healing` | value | 110 |
| `times` | value | 38 |
| `gold_t` | value | 38 |
| `xp_t` | value | 38 |
| `lh_t` | value | 38 |
| `dn_t` | value | 38 |
| `purchase_log` | value | 54 |
| `ability_upgrades_arr` | value | 19 |
| `ability_uses` | value | 4 |
| `ability_targets` | value | 1 |
| `item_uses` | value | 14 |
| `damage_inflictor` | value | 9 |
| `damage_targets` | value | 9 |
| `kills_log` | value | 12 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 13 |
| `obs_log` | value | 2 |
| `sen_log` | value | 1 |
| `obs_left_log` | value | 2 |
| `sen_left_log` | value | 1 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 81 |
| `actions` | value | 17 |
| `pings` | value | 4 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 4 |
| `benchmarks` | value | 10 |

## Пропуски и ограничения

- Match, **missing**: `comeback`, `dire_team`, `league`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `all_word_counts`, `cosmetics`, `draft_timings`, `my_word_counts`, `pauses`.
- Target player, **missing**: `additional_units`, `match_id`, `purchase_gem`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `neutral_tokens_log`.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
