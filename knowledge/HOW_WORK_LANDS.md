# How contributor work lands, and how to measure it

**Read this before you report anyone's contribution record, including your own.** On hermes-agent, "PRs merged" says little about impact.

## The mechanism: salvage into a carrier PR

Maintainers land most outside work by **salvage**. They cherry-pick a contributor's commits into their own carrier PR, keep the original author on each commit, merge the carrier, and close the contributor's PR. The contributor's PR shows *closed, not merged*, but their code is on `main` under their name. Upstream asks for exactly this: "salvage by cherry-pick so authorship survives" ([AGENTS.md L41](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L41)).

## Measured 2026-11-24 (main `8545fee`, commits 2026-10-25..11-23)

- **11,400 commits** reached `main` from **1,387 distinct GitHub authors** (228 more had no linked account).
- **5,870 (51%)** were committed by someone other than their author, i.e. carried. teknium1 was committer on 7,773 (68%).
- 1,203 commit messages carry `Co-authored-by:` or `(cherry picked from …)` trailers.
- Top commit authors: teknium1 2,831, c2h5oh 1,448, unsupportedpastels 370, yoniebans 361, BearHuddleston 302, alt-glitch 284, kshitijk4poor 260.
- Over a similar window, 4,229 PRs were merged ([WHO_MAINTAINS_WHAT.md](./WHO_MAINTAINS_WHAT.md)), far fewer than the number of authors whose commits landed.

Source: `gh api --paginate repos/NousResearch/hermes-agent/commits -f sha=8545fee… -f since=2026-10-25T00:00:00Z -f until=2026-11-24T00:00:00Z`, counting `.author.login` vs `.committer.login`.

## The right metric

Count **commits authored by the person that are on the default branch**:

```bash
SINCE=$(date -u -v-30d +%Y-%m-%dT00:00:00Z)   # GNU: date -u -d '30 days ago' +%Y-%m-%dT00:00:00Z
# commits by <login> on main
gh api --paginate -X GET repos/NousResearch/hermes-agent/commits \
  -f author=<login> -f since=$SINCE -f per_page=100 --jq '.[].sha' | wc -l
# who carried them
gh api --paginate -X GET repos/NousResearch/hermes-agent/commits \
  -f author=<login> -f since=$SINCE -f per_page=100 --jq '.[].committer.login' | sort | uniq -c | sort -rn
```

Then add credit trailers that don't change the author (`Co-authored-by:`, `Reported-by:`, `(cherry picked from commit …)`).

| Number | What it tells you |
|---|---|
| Commits authored on `main` | Code that shipped. The headline metric. |
| Committer of those commits | Which maintainer carries your work. |
| PRs merged under your name | Very little on this repo. Don't lead with it. |

## The channel that works

A small, **add-on commit offered on a maintainer's open PR**, with red/green evidence pinned to SHAs, is easy for a carrier to cherry-pick. Our own (non-public) offer log, 861 offers from 2026-09-20 to 11-22, saw about 53% adopted on maintainer PRs, against about 5% on community PRs. Treat that as one contributor's anecdote, not a public statistic.

## Rule for agents

Re-measure any contribution figure older than a week before quoting it. If a document cites PR-merge counts as impact, correct it.
