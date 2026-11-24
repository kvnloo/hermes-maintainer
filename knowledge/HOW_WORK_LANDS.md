# How contributor work lands in Hermes, and how to measure it

**Read this before you report on anyone's contribution record, including your own.** The most common mistake agents make on this project is measuring impact by "PRs merged". On hermes-agent that number is close to meaningless.

## The mechanism

Maintainers land most outside work by **salvage**: they cherry-pick a contributor's commits into their own carrier PR, keep the original author on each commit, merge the carrier, and close the contributor's PR. The contributor's PR shows as *closed, not merged*, yet their code is on `main` under their name.

Evidence (merged PRs 2026-10-07..11-06, `docs/MAINTAINERS-ACTIVITY.md`): 2,538 PRs merged; teknium1 merged 1,969 of them. Over the 30 days to 2026-11-24, the top authors of commits on `main` were all maintainers, with outside contributors' commits arriving through their carriers.

## The right metric

Count **commits authored by the person that are on the default branch**:

```bash
# commits by <login> on main in the last 30 days
gh api --paginate -X GET repos/NousResearch/hermes-agent/commits \
  -f author=<login> -f since=$(date -u -v-30d +%Y-%m-%dT00:00:00Z) -f per_page=100 --jq '.[].sha' | wc -l
# who landed them (committer = the maintainer who carried them)
gh api --paginate -X GET repos/NousResearch/hermes-agent/commits \
  -f author=<login> -f since=... -f per_page=100 --jq '.[].committer.login' | sort | uniq -c | sort -rn
```

Then add credit trailers that don't change the author: `Co-authored-by:`, `Reported-by:`, and `(cherry picked from commit ...)`. Rank against all authors on `main` for the same window.

| Number | What it tells you |
|---|---|
| Commits authored on `main` | Code that shipped. The headline metric. |
| Committer of those commits | Which maintainer trusts and carries your work. |
| Offers adopted / offered | Whether your add-on commits fit maintainers' PRs. |
| Human replies to your comments | Whether reviewers find your evidence useful. |
| PRs merged under your name | Almost nothing on this repo. Don't lead with it. |

## Channel that works

An **add-on commit offered on a maintainer's open PR**, with red/green evidence pinned to SHAs, is the highest-yield contribution. Measured across 861 offers (09-20..11-22): 53% adopted on maintainer PRs, about 5% on community PRs and 3% on community issues. Offers made within a day of the carrier PR opening do best.

## Rule for agents

When a document gives a contribution figure older than a week, re-measure it with the commands above before quoting it. If a document cites PR-merge counts as impact, correct it.
