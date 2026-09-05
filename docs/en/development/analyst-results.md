# Real analyst session: profile before and after

[Methods and commands](analyst-analysis.md) · [Русский](../../ru/development/analyst-results.md)

Verified 2026-09-05 for player 203182675 on the original ten games, without new collection or meta. Main outputs: [reviewed profile](analyst-profile-after.md) and [preceding profile](analyst-profile-before.md). These are my interpretations as current Codex; software prepared numbers and validated revisions.

## Personal result

Your clearest context here is **position-two Jakiro**. XP acquisition coexists with involvement in most team kills: medians of 912 recorded XP/min and 73.9% participation across four games. I would investigate preserving that involvement after returning: 9 of 26 deaths occurred within 120 seconds after the preceding recorded death interval ended. This is a concrete re-entry question, not an established error or a reason simply to fight less.

A practical experiment is to state the objective, nearby allies and exit before re-entry, then inspect whether a genuinely useful alternative existed. Track useful involvement alongside repeated deaths. Improving one statistic by abandoning necessary actions is not improvement.

## Why three added games did not rewrite the portrait

Seven earlier games were processed first, followed by the remaining three chronologically. All ten were already known to the project. There were four Jakiro-mid games initially and still four after the update. The additional Jakiro game is position five: 706 XP/min and 42.9% participation, but one game in a different role. Pooling it with mid would manufacture a decline narrative without suitable evidence.

The portrait was therefore retained verbatim. A separate Jakiro-support observation scope and broader limitations were added, while confidence in mid hypotheses did not increase. Overall wins rose from 6/7 to 9/10, which cannot demonstrate an effect of the recommendation: games predate it and comparable mid observations did not increase.

| Question | Before | After | Reason |
| --- | --- | --- | --- |
| XP together with team involvement on Jakiro-mid | Discovered | Discovered | Same four-game group and revision |
| Re-entry conditions after death | Testing | Testing | No new comparable observations; reused episode is not fresh support |
| XP-tempo loss after combat | Testing, outside priorities | Unchanged | Median −91.3 and pooled +370.3 have opposite signs; only 13 combat windows |
| Applicability to Jakiro-support | No separate group | New preliminary scope | One position-five game cannot establish its typical style |

## What addressed checks changed

Three Jakiro-mid cases were opened by death exposure: middle by order, lower tail and upper tail. The upper tail was a win with 14.5% death-time exposure. This counters a simple death-based explanation; selection was by metric, not alleged mistake severity.

L2 and L3 were checked for that case: **8955721990, 2026-08-20, position-two Jakiro**. The 31:23–32:49 interval contains 86 recorded death seconds. The team was already behind; its economic deterioration was not attributed to the player alone. A limitation that compression could lose is `action_journals_eligible=false`, making the 17-second return estimate unsuitable for characterizing decisions.

The 30–40-minute phase records 99 death seconds and 21,255 XP, or 32.1% of recorded allied XP. Death exposure alongside a large XP inflow prevents describing the entire phase as disengagement. The 86/99 difference concerns one interval versus all death overlap in a full phase: different windows.

The structured episode assessment was stored. Updating reused that accepted answer with the same input revision, without another model interpretation. Establishing an avoidable error still requires an available alternative, not merely absence duration.

## A match through an earlier profile

A separate earlier slice was replayed: six games including three Jakiro-mid games, then **8959040566 on 2026-08-22**. It was excluded from both baseline and initial profile. All three comparison games ended before it.

| Metric | Median of three preceding Jakiro-mid games | Target game |
| --- | --- | --- |
| Recorded XP/min | 860 | 965 |
| Death-time fraction | 13.3% | 4.0% |
| Team-kill participation | 81.6% | 57.1% |
| Repeated deaths | 8/23 pooled; median fraction 33.3% | 1/3 |

The earlier profile frames a safety/involvement tradeoff to investigate. XP persisted and death exposure decreased, but participation fraction was lower. Neither improvement nor passivity follows automatically: the target contains 32 participations in 56 team kills, with different denominators, duration and drafts. The next addressed check is a team action without your involvement where a feasible useful contribution can be evaluated. Lower death exposure alone did not establish removal of re-entry risk.

For the latest **8960626424 on Death Prophet-mid**, no suitable preceding games/profile exist. The system returned an empty baseline rather than applying Jakiro recommendations. Its 551 death seconds and 1/8 repeated deaths cannot confirm another hero's mid hypothesis. [Saved Jakiro response](../../../data/prototype/analyst/historical-match-response.json), [Death Prophet response](../../../data/prototype/analyst/match-response.json).

## Cost and validation limits

| Session | Main input bytes | Drills | Drill bytes | Card deliveries | New lower answers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial profile, 7 games | 31,074 | 3 | 11,223 | 5 | 1 |
| Updated profile, 10 games | 31,444 | 1 | 3190 | 1 | 0; one reused |
| Earlier profile, 6 games | 15,892 | 0 | 0 | 0 | 0 |
| Jakiro through earlier profile | 10,006 | 0 | 0 | 1 | 0 |
| Death Prophet without suitable profile | 4760 | 0 | 0 | 1 | 0 |

Main profile packets contain **zero match cards**. The five initial deliveries are three selected cases and two additional reads of one case: three distinct matches, not five new games. Counters cover recorded successful exchange sessions, excluding preparatory development reads and current-conversation messages. A separate 1000-synthetic-game test checks the main packet limit and absence of full-card reading during preparation.

120 tests and local-session verification pass. [Machine-readable verification](../../../data/prototype/analyst-verification.json). Model tokens were not measured and current Codex memory was not isolated: it had previously seen these games and later observations first. The earlier profile is retrospective replay, not a blind forecast. Causality, training-advice effectiveness and a stable all-role profile remain unproven and belong to subsequent validation.
