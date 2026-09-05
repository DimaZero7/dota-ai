# Real prototype examples without meta

[Commands and checks](analysis.md) · [Five-match manifest](../../../data/prototype_matches.json)

These are actual current-Codex interpretations through file exchange. Code computes measurements; source events constrain interpretation. Each level has a packet and response in `data/prototype/examples/`. The user delegated format and usefulness decisions to the assistant.

## Death Prophet: levels 0–4

Match 8960626424, account 203182675, Death Prophet, STRATZ POSITION_2/MID_LANE, a win lasting 52:02. Position is a source estimate. Both drafts accompany each packet; meta is disabled.

| Level | Example | Use and limit |
| --- | --- | --- |
| [0. Sources](../../../data/prototype/examples/L0.review.json) | SHA-256 verified, ten slots/heroes matched, compared final statistics agree | Supports specific fields, not a claim of complete game state |
| [1. Facts](../../../data/prototype/examples/L1.review.json) | Journals confirm 7 kills, 8 deaths, 504 last hits; 10 assists versus 13 final assists | Do not fabricate three missing events or declare the assist journal complete |
| [2. Episode](../../../data/prototype/examples/L2.review.json) | 09:01–10:34: five last hits, seven ability uses, three item uses, one death | Inspect health and positions before 10:01; no error established |
| [3. Stage](../../../data/prototype/examples/L3.review.json) | Before the first recorded tower destruction at 13:18: 4 kills, 2 deaths, 79 last hits; net worth 600 → 5795 | Descriptive boundary, not “lane won”; net worth change is not income |
| [4. Match](../../../data/prototype/examples/L4.review.json) | 7/8/13, 504 last hits, 9740 building damage, 551 seconds of recorded timeDead clipped to match end | Resource and damage output are observable; decision quality needs episodes |

The first review priority is decisions before deaths at **41:33, 44:11 and 48:12**, totaling 285 recorded timeDead seconds. Inspect the preceding objective, known threats, available resources and team trade. The result should be a concrete available alternative or an explicit failure to establish an error. Avoiding every death is not the goal. The original buyback journal is empty; 551 seconds is a transformed source-field sum, not established lost potential.

## Episode drill

A query for 09:50–10:02 selects health, abilities, items and death. Sharing repeated source descriptions allowed all 16 events to fit in 5938 bytes; the previous format returned 14 events in 7863 bytes with pagination. Hashes and pointers remain intact.

HP was 729/1198 at 09:58. Two ability uses (IDs 5091 and 5685) occur at 09:59; item ID 36 and HP 364/1198 occur at 10:00. This narrows the next question to positions and incoming damage. It does not establish escape availability, enemy visibility or optimal execution.

## Series: level 5

| Match | Hero | STRATZ position | Own death within 90 seconds after a kill / eligible kills |
| --- | --- | --- | --- |
| 8960626424 | Death Prophet | 2 | 2/5; two late kills excluded for incomplete observation windows |
| 8959457705 | Jakiro | 5 | 1/4 |
| 8959269261 | Dragon Knight | 2 | 6/11 |
| 8959040566 | Jakiro | 2 | 3/12 |
| 8958839199 | Jakiro | 2 | 1/6 |

Cohorts require the same hero, position, lane, mode and source-specific patch IDs. Opponent rank is unknown in the detailed snapshots used here. Both drafts are retained; matchup difficulty is not adjusted. All five selected available games happened to be wins. Selection did not filter outcomes, but this acceptance sample contains no losses.

[Actual level 5 interpretation](../../../data/prototype/examples/L5.review.json): **Jakiro POSITION_2 has 4/18 windows, three distinct deaths and 14 windows without a recorded death**. This suggests reviewing post-kill reassessment, not declaring a habit. Drafts differ: STRATZ assigns opposing POSITION_2 to Io in one game and Legion Commander in the other.

[Verified source drill](../../../data/prototype/examples/pattern-drill.json): kills at **04:41** and **06:00** in match 8959040566 share one death at **06:09**. A contrast case is a kill at **13:45** with no own death recorded in the next 90 seconds. This is an outcome contrast, not a matched counterfactual or proof of a good decision.

Two drills used 2316 bytes; every returned pointer resolved. Sensitivity checks produce 3/18 for 30/60-second windows and 4/18 for 90/120 seconds. Four windows must not be presented as four independent mistakes. The horizon is exploratory, not a game norm.

## Profile and development: level 6

[Actual level 6 interpretation](../../../data/prototype/examples/L6.review.json): **stable style and psychological traits are not established**. Three hero-position groups have one game; only Jakiro POSITION_2 has two. The useful output is a conditional review plan.

Exercise for Jakiro POSITION_2: after a kill, state the **next objective, known threats and current resources** before continuing or disengaging. Annotate the first ten eligible situations in future compatible games: information, decision, alternative and outcome. Ten is an observation target, not a skill norm.

Baseline: 4/18 and three distinct deaths. Repeat the same calculation and assess team trades separately. Reduced death frequency without useful participation does not establish progress. No prospective follow-up exists; status is **untested**. No additional training games were collected.

## Corrections and validation

- Seven OpenDota kill times are one second later than STRATZ. Other categories were not globally shifted. Native coordinates are not treated as reconstructed map geography.
- Stage detection was corrected to actual `building_kill` events with `tower`/`rax` keys. Missing objective journals leave a single descriptive segment, not fabricated strategic stages.
- Dragon Knight's `isStats=false` does not mean playback is absent: concrete journals exist and were checked. Availability is field-specific. Three additional OpenDota games lack parsing; STRATZ supplies their events.
- Post-kill windows have explicit denominators, end-censored events are excluded, and overlaps remain a limitation.
- 13 tests and 40 real-data checks pass. The 429-card evidence graph spans levels 0–6. Repeat execution reuses saved versions.

Initial packet sizes for levels 0–6 are **9676, 4836, 5206, 7479, 8998, 6178 and 8146 UTF-8 bytes**, each below 11000. Answers use 730–1531 bytes against a 4000-byte reserve. Detailed profile context focuses on the two Jakiro games; omitted contexts are listed explicitly.

These are prepared-data sizes, not exact model token usage. The session also inspected raw events, so interpretation was not blind. Improved model accuracy and training effectiveness are unproven. The [acceptance report](../../../data/prototype/end-to-end.json) separately lists synthetic missing-data, corruption and profile-update checks.
