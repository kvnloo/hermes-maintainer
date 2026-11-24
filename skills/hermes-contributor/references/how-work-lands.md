# How work lands in hermes-agent, and how to measure it

## Mechanism

Maintainers land most outside work by **salvage**: they cherry-pick a
contributor's commits into their own carrier PR, keep the original author on
each commit, merge the carrier, and close the contributor's PR. The
contributor's PR shows as *closed, not merged*, yet their code is on `main`
under their name. A small number of maintainers merge the large majority of
PRs; outside contributors' commits arrive through those carriers.

Consequence: "PRs merged under X's name" understates outside contributors and
overstates nobody usefully. Do not lead with it.

## The metric: commits authored on `main`

```bash
REPO=NousResearch/hermes-agent
LOGIN=<github-login>
# portable "30 days ago" (GNU date, then BSD/macOS date)
SINCE=$(date -u -d '30 days ago' +%Y-%m-%dT00:00:00Z 2>/dev/null || date -u -v-30d +%Y-%m-%dT00:00:00Z)

# commits authored by LOGIN on the default branch in the window
gh api --paginate -X GET repos/$REPO/commits \
  -f author=$LOGIN -f since=$SINCE -f per_page=100 --jq '.[].sha' | wc -l

# who landed them (committer = the maintainer who carried them)
gh api --paginate -X GET repos/$REPO/commits \
  -f author=$LOGIN -f since=$SINCE -f per_page=100 --jq '.[].committer.login' \
  | sort | uniq -c | sort -rn

# rank against all authors on main for the same window
gh api --paginate -X GET repos/$REPO/commits \
  -f since=$SINCE -f per_page=100 --jq '.[].author.login // "unlinked"' \
  | sort | uniq -c | sort -rn | head -25
```

Then add credit that does not change the author field, by searching commit
messages on `main` for the person's name or login in these trailers:

```bash
git log origin/main --since="$SINCE" -i --grep="Co-authored-by: .*<name-or-login>" --oneline
git log origin/main --since="$SINCE" -i --grep="Reported-by: .*<name-or-login>" --oneline
git log origin/main --since="$SINCE" --grep="cherry picked from commit" --author="<name>" --oneline
```

The `author` API filter only matches commits whose author email is linked to
the GitHub account; check unlinked emails with `git log --author=<email>` on a
local clone.

| Number | What it tells you |
|---|---|
| Commits authored on `main` | Code that shipped. The headline metric. |
| Committer of those commits | Which maintainer trusts and carries the work. |
| Add-on offers adopted / offered | Whether offered commits fit maintainers' PRs. |
| Human replies to review comments | Whether reviewers find the evidence useful. |
| PRs merged under the person's name | Almost nothing on this repo. |

## Finding the carrier

A carrier is the maintainer PR that will (or did) land a contributor's commits.

```bash
# open maintainer PRs touching the same area
gh pr list -R $REPO --state open --search "<area keywords>" \
  --json number,title,author,createdAt,headRefName --limit 50

# PRs that reference the contributor PR or issue number
gh pr list -R $REPO --state all --search "<number> in:body" --json number,title,author,state

# was a closed contributor PR salvaged? look for its commits on main
gh pr view <N> -R $REPO --json commits --jq '.commits[].messageHeadline'
git log origin/main --oneline -i --grep="<distinctive headline text>"
git log origin/main --oneline --grep="#<N>"
```

A closed PR whose commit headlines (or a `(cherry picked from commit <sha>)`
trailer) appear on `main` was salvaged, not rejected.

## Channel that works

An **add-on commit offered on a maintainer's open PR**, with red/green
evidence pinned to SHAs, is the highest-yield contribution. In the measured
history behind this knowledge base, offers on maintainer PRs were adopted about
ten times as often as comments on community PRs or issues, and offers made
within a day of the carrier opening did best. Re-measure before quoting any
rate.

## Rule for agents

When a document gives a contribution figure older than a week, re-measure it
with the commands above before quoting it. If a document cites PR-merge counts
as impact, correct it.
