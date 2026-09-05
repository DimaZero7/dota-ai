# What L5 showed in the August sample

Verified on 2026-09-05 for account **203182675**, without meta effects. This is an example of numerical evidence and current Codex's interpretation, not a final player profile.

## Data and limitations

Available August history contains **45 ranked games: 29 wins and 16 losses**, a 64.4% win rate. Visible games span August 6–23; discovery covered the entire calendar month in Moscow time. Full OpenDota responses were retained for all 45. Complete STRATZ snapshots for all participants were obtained for **23 games**; 22 ended in repeated HTTP 503 failures, with partial responses and reasons preserved.

Chronology uses 45 games; detailed statistics use 23. The detailed subset contains 17 wins and six losses: 73.9% wins versus 64.4% in the visible history. Data availability therefore changes sample composition; detailed findings cannot simply be generalized to the whole month. The original ten-game 9:1 example remains separate.

Sources: [selection and collection statuses](../../../data/datasets/2026-08-ranked/selection.json), [August L5 verification](../../../data/prototype/longitudinal-august-verification.json), [original ten verification](../../../data/prototype/longitudinal-ten-verification.json). Large raw JSON and computed packets remain local and are ignored by Git.

## A practical question for your next review

The largest detailed group is **Jakiro, position 2: eight games, five wins and three losses**. It combines sides, durations and rank bands under the same mode/version identifiers. This describes your observed games, without comparison to other players.

| Metric | Eight-game median | Middle 50% of games |
| --- | ---: | ---: |
| Recorded XP/min | 851 | 748–922 |
| Recorded gold/min | 440 | 406–484 |
| Participation in team kills | 63.5% | 58.7–72.5% |
| Time fraction in recorded death intervals | 11.7% | 8.3–14.5% |
| Repeated-death fraction | 33.3% | 22.9–38.1% |

In these games you participate in roughly two out of three team kills. **21 of 59 recorded deaths** occurred within 120 seconds of the previous recorded death end: a pooled 35.6%. The table's equal-match median answers a different question. This is a share of all deaths, not the probability of dying after each return. Buybacks can make recorded death intervals imperfect absence estimates.

Outcome contrasts make the review question more specific:

| Equal-match mean, Jakiro position 2 | Wins, n=5 | Losses, n=3 |
| --- | ---: | ---: |
| Kill participation | 65.2% | 70.6% |
| Death-time fraction | 8.2% | 18.3% |
| Recorded XP/min | 784 | 858 |
| Repeated-death fraction | 24.1% | 38.4% |

**My working hypothesis for targeted review:** examine the conditions in which fight involvement coincides with prolonged hero unavailability and repeated deaths after returning. Participation and XP are not lower in these losses, but death time is greater. Together, these features pose a question about the cost of involvement and subsequent decisions rather than merely counting deaths.

Three losses with different durations, drafts and team conditions do not establish that participation was mistaken. Losing team conditions may force deaths; longer games change XP rates even after dividing by minutes. The next check is to compare returns under matching phases, prior team states and ally availability, including supporting and contradicting cases. Group reference: `cohort:440ba6465beef599af79`; the main summary does not require remembering eight match IDs.

## Metrics not yet suitable for style conclusions

Post-combat XP contrasts were available in six of these eight games, using only 19 eligible combat windows, 1–5 per match. The median contrast is −233.75 XP/min change, whereas the window-pooled contrast is +188.93; the equal-match mean is even higher due to an extreme value. **The sign depends on aggregation, so “you recover farm poorly after fights” is not supported here.** This remains a diagnostic of sparse observed windows, requiring fuller controls and alternative-explanation checks.

Cell-distribution changes and damage changes after purchases are also available numerically. They do not evaluate item value: purchases may precede delivery, coincide with returning to the map, or follow an ongoing situation change. Spatial analysis inherits task 6's verified map alignment and version limitations.

## Sessions and result history

A 60-minute break threshold produces **38 estimated sessions**: 32 single-game, five two-game and one three-game session. The 30-minute threshold yields 39 sessions; 90 minutes yields 35. There are only seven within-session adjacent pairs at the 60-minute threshold, leaving little material for long-session effects.

The next observed game was won **19/28 times after a win — 67.9%**, and **10/16 after a loss — 62.5%**. Only five and two transitions respectively occur within an estimated session. Maximum observed result runs are seven wins and three losses; result runs may cross long breaks.

These numbers do not establish tilt or fatigue. There are no adjacent detailed games matching every strict condition for behavioral-change comparisons. After-result win rates therefore do not become claims about decision changes. Recent/history comparisons find two strict matching groups, each with only one historical and one recent game: no skill-growth estimate is justified.

## Implementation status

The 23 detailed signatures produce **394 conditional groups** and **110 declared screening pairs**. These are not 394 independent samples: a game can contribute to different questions, but only once within any group. There are **zero temporally replicated associations** and no sufficiently populated strict comparisons for screening p values. Lack of confirmation means insufficient evidence, not absence of player patterns.

The normal L5 packet uses **31,157 UTF-8 bytes**, without a match list. Full distributions and examples are available through up to three drill requests sharing 8000 bytes. Zero-priority discovery candidates remain in full L5 but do not occupy the normal packet.

**80 tests pass**, including a known artificial association, seeded null, same-day dependence, discovery/validation separation, 1000 artificial signatures and collection recovery from missing/corrupt files. Signature-only recalculation was also checked. [Methods and commands](longitudinal-analysis.md).

Task 7 provides new numerical evidence and targeted retrieval. Updating only affected aggregates belongs to task 8; systematic analyst claim history and L6 profile updates belong to task 9. This example establishes a review direction without replacing those stages.
