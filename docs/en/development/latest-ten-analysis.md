# Analysis of the ten latest available matches

> Historical version rejected by the user as insufficiently personal. Current results: [personal profile](player-profile.md) and [profile-conditioned match review](profile-match-review.md). The measurements below remain historical material and do not replace the new authored synthesis.

Account **203182675**. History checked **5 September 2026**. The API returned ten completed matches from **20–23 August 2026**; newer private or unavailable games were not verified. Exactly ten distinct games were collected through OpenDota and STRATZ. No meta assumptions were applied.

**Main finding:** early personal economy is usually favorable in this sample. The most useful review priorities are changing threats after the lane and sequences of deaths on Jakiro. Avoidable mistakes are not established: the evidence identifies situations, but player-visible alternatives remain incomplete.

The sample has **9 wins and 1 loss**, seven position-2 games and one each on positions 1, 3 and 5. Five games use Jakiro; four are position 2. Positions are STRATZ estimates. This short successful run is not an estimate of normal win rate.

[Evidence and original-response pointers](../../../data/analysis/reports/latest-ten-20260905/evidence.json) · [Verified history](../../../data/prototype/latest-ten-request.json) · [Commands](analysis.md)

## Match overview

ΔNW10 is net worth difference at 10:00 versus the opposing estimated same-position player, not proof of a won lane. Positions 3/5 do not necessarily face each other directly. Participation is `(final kills + assists) / final allied kills`, not participation in every fight.

| Match | Hero | Position | Result | Duration | K/D/A | Last hits | ΔNW10 | Participation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8960626424 | Death Prophet | 2 | Win | 52:02 | 7/8/13 | 504 | +918 | 44.4% |
| 8959457705 | Jakiro | 5 | Win | 47:03 | 4/10/14 | 244 | -5 | 42.9% |
| 8959269261 | Dragon Knight | 2 | Win | 34:46 | 11/5/14 | 274 | +1536 | 52.1% |
| 8959040566 | Jakiro | 2 | Win | 37:41 | 12/3/20 | 291 | +1026 | 57.1% |
| 8958839199 | Jakiro | 2 | Win | 45:44 | 6/6/23 | 286 | +306 | 87.9% |
| 8957931610 | Night Stalker | 2 | Win | 24:09 | 14/0/11 | 152 | +1041 | 52.1% |
| 8957583110 | Underlord | 3 | Win | 37:36 | 3/5/27 | 270 | +247 | 58.8% |
| 8957325148 | Jakiro | 2 | Loss | 40:50 | 12/6/19 | 311 | +1224 | 81.6% |
| 8956189348 | Juggernaut | 1 | Win | 46:52 | 11/2/12 | 547 | +1701 | 45.1% |
| 8955721990 | Jakiro | 2 | Win | 62:28 | 15/11/32 | 615 | -763 | 66.2% |

## Positive evidence

In **six of seven position-2 games**, your net worth at ten minutes exceeds the opposing position-2 player's. The four Jakiro differences are +1026 against Io, +306 against Legion Commander, +1224 against Ember Spirit and −763 against Arc Warden. Hero strength, matchup difficulty and allied help are not adjusted.

Night Stalker finished **14/0/11 in 24:09**. Juggernaut finished **11/2/12 with 547 last hits and 19,727 building damage**, 66.0% of the team's total. These are positive counterexamples to universal claims of constant deaths or farming without objective contribution, not established hero mastery.

Jakiro's four position-2 participation values are **57.1%, 87.9%, 81.6%, 66.2%**. They demonstrate recorded involvement in allied kills; they do not grade the decisions to join or miss particular fights.

## Priority 1: identify the actual threat beyond the opposing mid

The sole loss, **8957325148**, is particularly informative: Jakiro **12/6/19**, involvement in **31/38 allied kills**, 311 last hits. Your draft was **Riki, Jakiro, Earth Spirit, Bane, Vengeful Spirit**; opponents were **Phantom Lancer, Ember Spirit, Slardar, Rubick, Crystal Maiden**.

| Time | Your net worth | Ember Spirit | Phantom Lancer | Allied minus enemy team net worth |
| --- | --- | --- | --- | --- |
| 20:00 | 10,698 | 9,160 | 8,814 | −1,332 |
| 30:00 | 16,530 | 12,620 | 16,746 | −3,213 |
| 38:00 | 22,279 | 16,141 | 27,483 | −9,147 |
| 40:00 | 22,162 | 17,967 | 31,602 | −18,885 |

At 38:00 you are **6,138 ahead of Ember but 5,204 behind PL**. Your last three deaths, at **15:53, 25:59, 38:11**, name Phantom Lancer as attacker; the first three name Ember Spirit. In the verified **37:20–38:41** interval PL also appears as attacker in Bane, Vengeful Spirit and Earth Spirit death records. Repeated hero records are not distinct players; timing does not establish shared location.

Your team dealt **4,004 building damage**, versus **27,024** by the enemy. Your **2,758** is 68.9% of the allied value. There is insufficient evidence to blame your personal building contribution. Team conversion of favorable moments and response to PL are the review questions.

**Hypothesis:** inspect changing target priorities and conditions for continuing fights before prescribing last-hit practice. It is not established that you ignored PL or could safely escape the last death. During replay/data review, name the principal threat, conditions for a useful fight and the next reachable objective at minutes 20 and 30. In actual play use available information—observed items, damage, movement and deaths—not hidden exact API net worth.

## Priority 2: examine death sequences before late recovery conceals them

The long win **8955721990** ends at **15/11/32, 615 last hits and 112,515 hero damage**, but has **six deaths by 20:00 and nine by 30:00**. At minute 20 your net worth is 7,156 versus Arc Warden's 9,888, while your team still leads by 2,649. At minute 30 the individual figures are 12,836 versus 19,796.

Your draft: **Faceless Void, Jakiro, Enigma, Lion, Undying**. Opponents: **Dragon Knight, Arc Warden, Troll Warlord, Spirit Breaker, Magnus**. This context differs from the Io game; identical lane/farm expectations are unjustified.

The first review sequence contains deaths at **07:51, 08:49 and 10:29**; the latter two name Spirit Breaker. At **10:14** you kill Arc Warden and die 15 seconds later. Arc Warden also dies to Undying at 07:51. These are trades, so all three deaths cannot be called pointless feeding.

Another candidate, **8958839199**, moves from +306 against the opposing position 2 at minute 10 to −3,447 at minute 30, with three own deaths during minutes 20–30. Deaths at **21:59 and 23:35** name Shadow Fiend. Yet you participated in 29/33 allied kills and the whole team was behind. It is not established that you abandoned farming for useless fights.

Review whether the next engagement after a death has a clear objective and changed conditions: known threats, allied support and the value of the trade. Do not infer a repeated dangerous location without verified spatial/visibility evidence. Counterexample **8959040566** has no deaths between **13:03 and the end at 37:41**, finishing 12/3/20. The hypothesis is conditional, not a stable overaggression label.

## The earlier post-kill hypothesis

Three compatible Jakiro games with matching kill/death journals produce **8/32 eligible kills followed by an own death within 90 seconds**, with **24 windows without a recorded death**. Windows overlap and can contain multiple deaths; these are not eight independent mistakes.

Sensitivity: **6/32** at 30/60 seconds, **8/32** at 90, **9/32** at 120. There is no properly matched baseline probability of death in an equivalent fight. This metric selects review episodes; it does not establish that decisions worsen after a kill.

**The loss is excluded from this metric:** STRATZ has 11 kill events against 12 final kills. Its agreed final statistics, economy snapshots and death journal were therefore reviewed separately. No missing kill timestamp was fabricated. All three automatically grouped games are wins; their frequency cannot be generalized to losses.

## Current project stage

The prototype collects ten games, retains positions and both drafts, calculates traceable facts, selects intervals and drills into raw evidence. This run processed **891,407 events**, performed **79 source/structure checks**, and generated ten match packets of **5,035–6,858 UTF-8 bytes**. Those are prepared-data sizes, not exact session token usage.

The economic and threat comparisons in this report were additionally computed and interpreted by current Codex. **They are not yet a ready set of automatic coaching rules.** Automatic cross-match discovery currently contains one post-kill-death hypothesis.

Observed limitations:

1. The automatic profile lists **nine matches**: exclusion from one metric also removes that match from its profile list. This report retains all ten. A standalone profile must carry excluded games explicitly.
2. Journals can disagree with final totals: 11/12 kills in the loss, Underlord 37 assist records versus 27 final assists, and long-game Jakiro 616 last-hit events versus 615 final last hits. The overview uses final aggregates and preserves discrepancies.
3. Two health-detail queries reached their budget, returning 6/16 and 8/27 events. They are not used as complete mechanical-execution reviews; pagination and unresolved questions are saved.
4. Complete visibility, cooldowns, safe routes and intent are not reconstructed. Automatic avoidable-death judgments and psychological profiling are unsupported.

**Assessment:** a working research prototype with useful Codex-assisted review. It identifies specific intervals and verifiable questions. A standalone personal coach still requires checks of available alternatives, broader pattern discovery and correct propagation of exclusions.

Suggested exercise: in future Jakiro games select an episode after a death or kill and state **“my next objective is …; the main known threat is …; I continue if …”**. Review the actual choice and team trade afterward. Effectiveness is untested; no games beyond these ten were collected.
