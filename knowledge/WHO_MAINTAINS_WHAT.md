# Who merges and reviews what

*Measured 2026-11-24 with [`scripts/maintainer-activity.py`](../scripts/maintainer-activity.py) (read-only GraphQL): PRs merged into `NousResearch/hermes-agent` 2026-10-26..11-24, main at `8545fee`. Full output: [docs/MAINTAINERS-ACTIVITY.md](../docs/MAINTAINERS-ACTIVITY.md). These are public counts, not assessments of anyone.*

**4,229 PRs merged in 30 days; 1,480 were merged by their own author.**

## Merges, by area

"Area" is the first path segment of the files a PR touched.

| Merger | Merged | Median h open→merge | Top areas |
|---|---:|---:|---|
| teknium1 | 3,390 | 24.5 | plugin-catalog, contributors, tests, gateway, hermes_cli |
| c2h5oh | 270 | 17.2 | tests, hermes_cli, tools, website, agent |
| unsupportedpastels | 155 | 8.0 | tests, hermes_cli, website, apps, gateway |
| kshitijk4poor | 151 | 3.7 | tests, hermes_cli, website, apps, gateway |
| alt-glitch | 115 | 4.2 | tests, hermes_cli, scripts, agent, tools |
| BearHuddleston | 75 | 4.2 | tests, apps, hermes_cli, scripts, website |
| jquesnelle | 25 | 66.4 | tests, hermes_cli, agent, website |
| austinpickett | 23 | 13.5 | apps, web, hermes_cli |

## Reviews

teknium1 772 PRs (mostly plugin-catalog; 539 approvals, 721 change requests), BearHuddleston 552 (tests, hermes_cli, website, tools), unsupportedpastels 389 (tests, hermes_cli, gateway), kshitijk4poor 107.

## Timing

- **There are no office hours.** Merges land in every UTC hour (lowest hour: 67 merges in 30 days). They peak 09:00–11:00 UTC and 22:00–00:00 UTC. Thursday is the busiest day (1,014). Measured over 4,205 merged PRs 2026-10-25..11-23.
- First human response on a merged PR: median 6.7 h, p90 44.1 h. For outside contributors: median 13.6 h, p90 64.0 h. This counts merged PRs only, so a typical open PR waits longer.
- Merges are bursty. teknium1's daily count ranged from 2 to 415 in the window.

## So what

- Gateway, CLI and tests changes get fast human merges from several maintainers. Plugin-catalog entries go through one merger in sweeps.
- A quiet week on your PR is normal. Use it to check that your evidence is pinned to the current head (see [REVIEW_EVIDENCE.md](./REVIEW_EVIDENCE.md)).
- Merge counts are not contribution impact. Read [HOW_WORK_LANDS.md](./HOW_WORK_LANDS.md).

Re-run: `python3 scripts/maintainer-activity.py --repo NousResearch/hermes-agent --days 30 --out /tmp/ma` (needs `gh auth`; takes ~10 minutes).
