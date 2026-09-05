# Данные OpenDota: 8940184740

Source: https://api.opendota.com/api/matches/8940184740
Retrieved UTC: 2026-09-05T15:05:50.846420+00:00

[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)

Players: **10**. Parser version: **22**.
Parse status: `already_parsed`. `od_data`: `{'has_api': True, 'has_gcdata': True, 'has_parsed': True, 'has_archive': False}`.

Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры.

## События матча

| Field | State | Count |
| --- | --- | --- |
| `objectives` | value | 21 |
| `teamfights` | value | 10 |
| `chat` | value | 83 |
| `pauses` | empty | 0 |
| `picks_bans` | value | 17 |
| `draft_timings` | empty | 0 |
| `radiant_gold_adv` | value | 29 |
| `radiant_xp_adv` | value | 29 |

## Все участники

| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 120484472 | 87 | 2/8/7 | 192 | 265 | 14 |
| 1 | 1160250755 | 76 | 6/9/3 | 417 | 523 | 130 |
| 2 | 1207617683 | 145 | 1/9/4 | 327 | 360 | 132 |
| 3 | 203182675 | 49 | 3/8/9 | 303 | 406 | 97 |
| 4 | 105009388 | 22 | 6/9/10 | 269 | 349 | 33 |
| 128 | 1033140387 | 9 | 6/5/25 | 359 | 393 | 36 |
| 129 | 1905958333 | 85 | 8/2/24 | 559 | 655 | 157 |
| 130 | 1280428254 | 50 | 4/2/24 | 368 | 586 | 33 |
| 131 | 1153604570 | 67 | 11/7/13 | 583 | 545 | 166 |
| 132 | 1622073974 | 126 | 14/3/10 | 548 | 570 | 117 |

## Твой игрок: 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `kills` | value | 3 |
| `deaths` | value | 8 |
| `assists` | value | 9 |
| `net_worth` | value | 7625 |
| `gold_per_min` | value | 303 |
| `xp_per_min` | value | 406 |
| `last_hits` | value | 97 |
| `denies` | value | 7 |
| `hero_damage` | value | 15423 |
| `tower_damage` | zero | 0 |
| `hero_healing` | zero | 0 |
| `times` | value | 29 |
| `gold_t` | value | 29 |
| `xp_t` | value | 29 |
| `lh_t` | value | 29 |
| `dn_t` | value | 29 |
| `purchase_log` | value | 26 |
| `ability_upgrades_arr` | value | 15 |
| `ability_uses` | value | 4 |
| `ability_targets` | value | 2 |
| `item_uses` | value | 10 |
| `damage_inflictor` | value | 5 |
| `damage_targets` | value | 6 |
| `kills_log` | value | 3 |
| `buyback_log` | empty | 0 |
| `runes_log` | value | 1 |
| `obs_log` | empty | 0 |
| `sen_log` | empty | 0 |
| `obs_left_log` | empty | 0 |
| `sen_left_log` | empty | 0 |
| `camps_stacked` | zero | 0 |
| `lane_pos` | value | 25 |
| `actions` | value | 14 |
| `pings` | value | 6 |
| `connection_log` | empty | 0 |
| `neutral_tokens_log` | empty | 0 |
| `neutral_item_history` | value | 2 |
| `benchmarks` | value | 10 |

## Пропуски и ограничения

- Match, **missing**: `dire_team`, `league`, `loss`, `negative_votes`, `positive_votes`, `radiant_team`, `skill`, `throw`, `win`.
- Match, **null**: `metadata`.
- Match, **empty**: `cosmetics`, `draft_timings`, `my_word_counts`, `pauses`.
- Target player, **missing**: `additional_units`, `camps_stacked_t`, `hero_damage_t`, `hero_healing_t`, `match_id`, `purchase_tpscroll`, `purchase_ward_observer`, `purchase_ward_sentry`.
- Target player, **null**: `name`.
- Target player, **empty**: `buyback_log`, `connection_log`, `cosmetics`, `kill_streaks`, `multi_kills`, `neutral_tokens_log`, `obs`, `obs_left_log`, `obs_log`, `permanent_buffs`, `sen`, `sen_left_log`, `sen_log`.

`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; `zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; пустой список событий может означать, что событий не было. Причина пропусков API не установлена. Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла.
