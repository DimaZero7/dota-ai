# STRATZ: 8960626424

Source: https://api.stratz.com/graphql · UTC: 2026-09-05T09:14:18.820375+00:00

[Metadata](metadata.json) · [Inventory](inventory.json) · [Merged data](match.json)

Status: **complete**. Requests: **13**. Players: **10**.

Для каждого запроса сохранены GraphQL, variables.json и исходный ответ; корневой match.json объединён по playerSlot. Токен находится только в локальной конфигурации. Большие JSON исключены из Git.

## Реальные лимиты

```json
{
  "x-ratelimit-limit-minute": "150",
  "x-ratelimit-limit-hour": "1500",
  "x-ratelimit-limit-day": "15000",
  "x-ratelimit-remaining-second": "7",
  "x-ratelimit-remaining-minute": "149",
  "x-ratelimit-remaining-hour": "1486",
  "x-ratelimit-remaining-day": "14986",
  "ratelimit-reset": "1",
  "ratelimit-remaining": "7",
  "ratelimit-limit": "8",
  "x-ratelimit-limit-second": "8"
}
```

## Match

| Field | State | Value / Count |
| --- | --- | --- |
| `id` | value | 8960626424 |
| `didRadiantWin` | value | True |
| `durationSeconds` | value | 3122 |
| `startDateTime` | value | 1787469159 |
| `endDateTime` | value | 1787472281 |
| `towerStatusRadiant` | value | 1824 |
| `towerStatusDire` | zero | 0 |
| `barracksStatusRadiant` | value | 61 |
| `barracksStatusDire` | value | 48 |
| `clusterId` | value | 182 |
| `firstBloodTime` | value | 116 |
| `lobbyType` | value | RANKED |
| `numHumanPlayers` | value | 10 |
| `gameMode` | value | ALL_PICK_RANKED |
| `replaySalt` | null | None |
| `isStats` | value | True |
| `tournamentId` | null | None |
| `tournamentRound` | null | None |
| `actualRank` | value | 64 |
| `averageRank` | null | None |
| `averageImp` | null | None |
| `parsedDateTime` | value | 1787473078 |
| `statsDateTime` | value | 1787473086 |
| `leagueId` | null | None |
| `radiantTeamId` | null | None |
| `direTeamId` | null | None |
| `seriesId` | null | None |
| `gameVersionId` | value | 182 |
| `regionId` | value | 8 |
| `sequenceNum` | value | 7531389633 |
| `rank` | value | 64 |
| `bracket` | value | 6 |
| `analysisOutcome` | null | None |
| `predictedOutcomeWeight` | null | None |
| `radiantNetworthLeads` | value | 54 |
| `radiantExperienceLeads` | value | 54 |
| `radiantKills` | value | 54 |
| `direKills` | value | 54 |
| `pickBans` | value | 27 |
| `towerStatus` | value | 12 |
| `laneReport` | value | 2 |
| `winRates` | null | None |
| `predictedWinRates` | null | None |
| `chatEvents` | value | 75 |
| `towerDeaths` | value | 29 |
| `playbackData` | value | 8 |
| `spectators` | empty | 0 |
| `bottomLaneOutcome` | value | RADIANT_VICTORY |
| `midLaneOutcome` | value | RADIANT_VICTORY |
| `topLaneOutcome` | value | RADIANT_VICTORY |
| `didRequestDownload` | value | True |

## Player 203182675

| Field | State | Value / Count |
| --- | --- | --- |
| `matchId` | value | 8960626424 |
| `playerSlot` | zero | 0 |
| `steamAccountId` | value | 203182675 |
| `isRadiant` | value | True |
| `isVictory` | value | True |
| `heroId` | value | 43 |
| `gameVersionId` | value | 182 |
| `kills` | value | 7 |
| `deaths` | value | 8 |
| `assists` | value | 13 |
| `leaverStatus` | value | NONE |
| `numLastHits` | value | 504 |
| `numDenies` | value | 11 |
| `goldPerMinute` | value | 652 |
| `networth` | value | 30889 |
| `experiencePerMinute` | value | 780 |
| `level` | value | 26 |
| `gold` | value | 4179 |
| `goldSpent` | value | 29200 |
| `heroDamage` | value | 28604 |
| `towerDamage` | value | 9740 |
| `heroHealing` | zero | 0 |
| `partyId` | null | None |
| `isRandom` | false | False |
| `lane` | value | MID_LANE |
| `position` | value | POSITION_2 |
| `streakPrediction` | null | None |
| `intentionalFeeding` | false | False |
| `role` | value | CORE |
| `roleBasic` | value | CORE |
| `imp` | null | None |
| `award` | null | None |
| `item0Id` | value | 36 |
| `item1Id` | value | 610 |
| `item2Id` | value | 277 |
| `item3Id` | value | 123 |
| `item4Id` | value | 29 |
| `item5Id` | value | 116 |
| `backpack0Id` | null | None |
| `backpack1Id` | null | None |
| `backpack2Id` | null | None |
| `neutral0Id` | value | 574 |
| `behavior` | zero | 0 |
| `additionalUnit` | null | None |
| `abilities` | value | 19 |
| `invisibleSeconds` | zero | 0 |
| `dotaPlusHeroXp` | value | 2749 |
| `variant` | zero | 0 |

## Player stats

| Field | State | Value / Count |
| --- | --- | --- |
| `matchId` | value | 8960626424 |
| `steamAccountId` | value | 203182675 |
| `gameVersionId` | zero | 0 |
| `level` | value | 26 |
| `killEvents` | value | 7 |
| `deathEvents` | value | 8 |
| `assistEvents` | value | 10 |
| `lastHitsPerMinute` | value | 52 |
| `goldPerMinute` | value | 52 |
| `experiencePerMinute` | value | 52 |
| `healPerMinute` | value | 52 |
| `heroDamagePerMinute` | value | 52 |
| `towerDamagePerMinute` | value | 52 |
| `towerDamageReport` | value | 12 |
| `courierKills` | empty | 0 |
| `wards` | value | 4 |
| `itemPurchases` | value | 23 |
| `itemUsed` | value | 14 |
| `allTalks` | value | 5 |
| `chatWheels` | value | 4 |
| `actionsPerMinute` | value | 52 |
| `actionReport` | value | 11 |
| `locationReport` | value | 68 |
| `farmDistributionReport` | value | 9 |
| `runes` | value | 16 |
| `abilityCastReport` | value | 3 |
| `heroDamageReport` | value | 8 |
| `inventoryReport` | value | 55 |
| `networthPerMinute` | value | 53 |
| `campStack` | value | 52 |
| `matchPlayerBuffEvent` | empty | 0 |
| `deniesPerMinute` | value | 52 |
| `impPerMinute` | null | None |
| `tripsFountainPerMinute` | value | 52 |
| `spiritBearInventoryReport` | null | None |
| `heroDamageReceivedPerMinute` | value | 52 |
| `wardDestruction` | value | 1 |

## Player playback

| Field | State | Value / Count |
| --- | --- | --- |
| `abilityLearnEvents` | value | 19 |
| `abilityUsedEvents` | value | 338 |
| `abilityActiveLists` | value | 1 |
| `itemUsedEvents` | value | 86 |
| `playerUpdatePositionEvents` | value | 1860 |
| `playerUpdateGoldEvents` | value | 3125 |
| `playerUpdateAttributeEvents` | value | 51 |
| `playerUpdateLevelEvents` | value | 26 |
| `playerUpdateHealthEvents` | value | 2349 |
| `playerUpdateBattleEvents` | value | 293 |
| `killEvents` | value | 7 |
| `deathEvents` | value | 8 |
| `assistEvents` | value | 10 |
| `csEvents` | value | 504 |
| `goldEvents` | value | 593 |
| `experienceEvents` | value | 656 |
| `healEvents` | value | 968 |
| `heroDamageEvents` | value | 882 |
| `towerDamageEvents` | value | 669 |
| `inventoryEvents` | value | 1 |
| `purchaseEvents` | value | 23 |
| `buyBackEvents` | empty | 0 |
| `streakEvents` | value | 2 |
| `runeEvents` | value | 16 |
| `spiritBearInventoryEvents` | null | None |

## Match playback

| Field | State | Value / Count |
| --- | --- | --- |
| `courierEvents` | empty | 0 |
| `runeEvents` | value | 258 |
| `wardEvents` | value | 224 |
| `buildingEvents` | empty | 0 |
| `towerDeathEvents` | value | 29 |
| `roshanEvents` | empty | 0 |
| `radiantCaptainHeroId` | zero | 0 |
| `direCaptainHeroId` | zero | 0 |

## Сравнение с OpenDota

| STRATZ field | OpenDota field | STRATZ | OpenDota | Equal |
| --- | --- | --- | --- | --- |
| kills | kills | 7 | 7 | True |
| deaths | deaths | 8 | 8 | True |
| assists | assists | 13 | 13 | True |
| numLastHits | last_hits | 504 | 504 | True |
| numDenies | denies | 11 | 11 | True |
| goldPerMinute | gold_per_min | 652 | 652 | True |
| experiencePerMinute | xp_per_min | 780 | 780 | True |
| networth | net_worth | 30889 | 30889 | True |
| heroDamage | hero_damage | 28604 | 28604 | True |
| towerDamage | tower_damage | 9740 | 9740 | True |
| heroHealing | hero_healing | 0 | 0 | True |

## Дополнения и ограничения

STRATZ добавляет временные события позиций, здоровья, применения способностей и предметов, получения золота/опыта, урона и лечения. Это позволяет разбирать последовательность действий подробнее, чем по агрегатам OpenDota. Обнаруженные признаки смертей (например, isWardWalkThrough и isAttemptTpOut), оценки линий, роли и intentionalFeeding являются интерпретациями STRATZ, а не доказательством намерений игрока. IMP и winRates в этом ответе отсутствуют (null).

Числа событий разных сервисов напрямую не равнозначны: STRATZ chatEvents содержит типизированные игровые события, а не только текст чата; itemPurchases может иметь иной состав, чем purchase_log. Длина рядов тоже отличается: нельзя совмещать их по индексу без проверки времени и смысла показателя. Счётчик assists и список assistEvents внутри STRATZ могут расходиться. Координаты и события playback не означают полного покадрового реплея. Пустые roshanEvents/buildingEvents не доказывают отсутствия этих событий в игре.

Нули и false сохранены как значения; null, empty, missing и not_requested различаются в inventory.json. Не запрашивались переходы к истории профилей, справочникам героев/способностей, объектам турниров/команд и средним показателям других матчей. Список исключений сохранён ниже. Все остальные доступные поля выбранных веток запрошены по сохранённой схеме; это не гарантия полноты данных сервиса.

- `match.league`: reference/profile/aggregate relationship or collected in a separate query.
- `match.radiantTeam`: reference/profile/aggregate relationship or collected in a separate query.
- `match.direTeam`: reference/profile/aggregate relationship or collected in a separate query.
- `match.series`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.match`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.steamAccount`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.hero`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.heroAverage`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.dotaPlus`: reference/profile/aggregate relationship or collected in a separate query.
- `match.players.abilities.abilityType`: reference/profile/aggregate relationship or collected in a separate query.
