# Dota AI

[Русская версия](README.md)

## About the project

Dota AI is a project for detailed Dota 2 match analysis and identifying individual opportunities for player improvement. The plan is to retrieve selected matches from a player's profile through available APIs, collect as much data as those sources provide, and gradually build a database of matches and their analyses.

As the history grows, analysis should reveal a consistent playing style: habits, decision-making patterns, strengths, and recurring mistakes. This will inform a gameplay and psychological portrait within the game, such as patterns in risk-taking, responses to setbacks, and team interaction. These interpretations will be treated as hypotheses grounded in observable gameplay, accounting for data completeness and match context.

The goal is to uncover subtle mistakes and opportunities for improvement that are difficult to spot in a single match. Another focus is to turn intuitive game understanding into clear explanations: which situational cues matter, why a decision worked or failed, and what pattern the player can apply in future matches.

## Patches and the meta

Match analysis should account for the patch on which each match was played and its relevant meta. The initial plan is to analyze the current patch and meta, recording them as the starting context for match analysis.

With each new patch, the plan is to maintain a change log, examine its gameplay impact, and update the overall description of the current meta. Earlier descriptions will be preserved so that older matches can be analyzed in their original context and the player's adaptation to changes can be tracked.

## Current status

The repository structure, AI instructions, and documentation are in place. Selecting the latest available completed match through OpenDota and saving its context are implemented. Full OpenDota response collection for the frozen match is implemented, including all participants, request provenance, and field coverage reports. Authenticated STRATZ collection includes statistics and playback for all participants, coverage reports, and final-stat comparisons with OpenDota. Replay acquisition and a custom parser are outside the current task. The [source comparison](docs/en/architecture/data-sources.md) is ready; its recommendation awaits agreement. A local level 0–6 prototype now covers five matches: facts, episodes, stages, match summaries, conditional patterns and a preliminary profile. Meta is disabled. Current Codex interprets bounded file packets; there is no automatic model API. [Examples](docs/en/development/prototype-examples.md), [commands and checks](docs/en/development/analysis.md). Python 3.14.7, Pipenv, and a local `.venv` environment are configured for development. Configuration loading uses `toml==0.10.2`.

The ten saved matches support [numeric L1–L4](docs/en/development/numeric-analysis.md) and [task 6 spatial features and maps](docs/en/development/spatial-analysis.md), including bounded conditional L5 groups. No new matches were fetched for this stage.

Implemented [longitudinal L5 statistics](docs/en/development/longitudinal-analysis.md): conditional distributions, game sessions, temporal comparisons and exploratory associations. [August verification](docs/en/development/longitudinal-results.md) uses 45 ranked games for chronology and complete detailed data for 23, with explicit STRATZ gaps and no meta effects.

Implemented [task 8 incremental updates](docs/en/development/cumulative-analysis.md): new and corrected matches update affected groups while retaining history, coverage and an analyst change packet. Verified on the original ten matches and a synthetic 1000+10 scenario, without reading earlier source events.

Implemented the [L5–L6 analyst workflow](docs/en/development/analyst-analysis.md): bounded packets, hypothesis lifecycles, personal-profile revisions and match comparison with an independent preceding baseline. The [reviewed profile](docs/en/development/analyst-profile-after.md) and [before/after session](docs/en/development/analyst-results.md) use the original ten games. Stability and usefulness validation belong to task 10.

## Structure

- `AGENTS.md` — entry point for AI instructions.
- `.agent/` — project and agent interaction rules.
- `.agent/tasks/` — task index, backlog, and `items/` for numbered task files.
- `src/` — source code.
- `tools/` — supporting tools.
- `docs/ru/` and `docs/en/` — Russian and English documentation.

## Documentation

- [Contents](docs/en/README.md)
- [Environment](docs/en/environment/README.md)
- [Architecture](docs/en/architecture/README.md)
- [Development and validation](docs/en/development/README.md)
- [Build and distribution](docs/en/distribution/README.md)

## Getting started

Before making changes, read the [project rules](.agent/PROJECT_RULES.md) and [interaction rules](.agent/INTERACTION_RULES.md). Keep the README files and relevant documentation sections up to date as the concept is refined and implemented. See [environment setup](docs/en/environment/README.md) for Python and local environment instructions. See [development](docs/en/development/README.md) for the match selection command.
