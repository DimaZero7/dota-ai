# Data source comparison

[Architecture](README.md) · [Русский](../../ru/architecture/data-sources.md)

Status: comparison complete; recommendation awaiting the user's decision. Replay acquisition and a custom parser were removed from the current task at the user's request.

## Evidence

One match, `8960626424`, target account `203182675`, Death Prophet. This comparison uses snapshots collected on 2026-09-05 without new requests or changing the match:

- [OpenDota report and source data](../../../data/matches/8960626424/opendota/20260905T090414.607209Z/report.en.md).
- [STRATZ report, queries, and source data](../../../data/matches/8960626424/stratz/20260905T091417.870926Z/report.en.md).

Both sources cover all 10 participants, matched by account ID with hero identity checked. All **110 comparisons** agree: 11 statistics per participant — kills, deaths, assists, last hits, denies, GPM, XPM, net worth, hero damage, tower damage, and healing. Matching totals do not prove complete event coverage or independent sources.

## Coverage

Player-level counts refer to the target account; other counts cover the match. Record counts are not quality scores or necessarily counts of distinct actions.

| Category | OpenDota | STRATZ | Implication |
| --- | --- | --- | --- |
| Final statistics | All 10 players | All 10 players | Cross-check basic results |
| Player time series | 53 points each in times/gold_t/xp_t/lh_t/dn_t; times 0–3120 s | Usually 52 minute values; 53 networthPerMinute | Verify units, time alignment, and cumulative versus interval values |
| Position and health | lane_pos aggregates, no equivalent movement timeline in this response | 1860 position and 2349 health updates | More detailed sequence context, not every game tick |
| Abilities and items | 19 upgrades; ability_uses/item_uses aggregates | 19 upgrades, 338 ability-use and 86 item-use events | STRATZ adds action timing |
| Purchases | 57 purchase_log entries | 23 itemPurchases / purchaseEvents | Different journal scope; do not infer 34 lost purchases without item/time matching |
| Damage and healing | Totals and source/target breakdowns | Additionally 882 heroDamageEvents and 968 healEvents | More detail for individual episodes |
| Last hits | Total 504 and minute series | Total 504 and 504 csEvents | Event-level last hits |
| Deaths and assists | Totals and kill logs | 8 detailed deathEvents; 10 assistEvents versus 13 final assists | Event journals may not explain even their own source's totals |
| Wards | 2 obs_log and 2 sen_log for target, removal logs | 4 target wards; 224 wardEvents across the match | Spawn/removal events are not a count of placed wards |
| Fights and objectives | 8 teamfights, 31 objectives | towerDeaths, wardEvents, player events; empty roshanEvents/buildingEvents | OpenDota offers complementary structure; empty STRATZ arrays do not prove no events |
| Chat | 47 chat records | 75 chatEvents plus allTalks/chatWheels | chatEvents includes typed game events, so counts are not equivalent |
| Service estimates | benchmarks, lane_efficiency, other aggregates | Roles, lane outcomes, death flags; IMP and winRates null | Separate interpretations from observations and player intent |
| Missing data | metadata null, draft_timings empty, optional keys absent | IMP/winRates null, some playback branches empty | Distinguish missing, null, empty, zero, false, and not_requested |

STRATZ queries covered available fields in the selected match, stats, and playback branches. Profile histories, reference relationships, and other-match averages were excluded and recorded in metadata. Unique coverage claims concern these snapshots, not every possible API capability.

## Practical costs

| Criterion | OpenDota | STRATZ |
| --- | --- | --- |
| Authentication used | No key | Free token after Steam sign-in, stored locally |
| Observed quota | 59/minute and 2985/day remaining after match request; remaining values are not plan limits | Limit headers: 8/second, 150/minute, 1500/hour, 15000/day |
| Current collector requests | 2: match and schema | 13: schema, overview, stats, playback for 10 players |
| Raw bytes including schema | 397091 (~0.40 MB) | 11466707 (~11.47 MB) |
| Whole local snapshot at comparison time | ~0.96 MB | ~37.29 MB including merged copy and inventory |
| Parsing wait | Already parsed; queue delay not measured | Already parsed; queue delay not measured |
| Retrieval interval | ~0.5 s between first and last response | ~33.3 s including collector pauses of 1.1 s |
| Maintenance | Simple REST response; optional fields and parser versions | Token, GraphQL schema, multiple queries, partial errors, merging |

Response intervals are neither complete execution times nor a service speed benchmark. Recorded quotas may change and differ from the STRATZ website table. Reruns consume quota; large JSON files are ignored by Git. One match does not establish availability reliability, indexing delays, or full-history coverage.

## Recommendation for agreement

Use **STRATZ as the main source of detailed events, with OpenDota for complementary data and final-stat checks**. Keep the implemented OpenDota match selection: acquisition order does not define the main analysis source.

Use STRATZ sequences for movement, health, abilities, and damage, and OpenDota fight groupings, objectives, and extra journals. Preserve source and time for every observation. Do not overwrite disagreements or combine events before checking their definitions. If STRATZ is unavailable, OpenDota supports a limited analysis rather than an equivalent replacement.

STRATZ alone reduces the number of integrations but loses available OpenDota complements. OpenDota alone simplifies authentication and storage but loses detailed event sequences. For individual gameplay analysis, combining them is justified by the current match.

This is a recommendation, not an agreed decision or an implemented unified analysis. The final source choice remains with the user.
