# Highest-volume easy close on NousResearch/hermes-agent

**Close table (posted):** https://github.com/NousResearch/hermes-agent/issues/109552

2743 open tickets **labeled** `duplicate` or `invalid`. That label is mostly alt-glitch and is **unverified**. DavidMetcalfe: the bot mislabels; do not close from the tag. liuhao1024 showed stale/backwards rows (canonical already gone, approved PRs). The issue is a label audit, not a close list: https://github.com/NousResearch/hermes-agent/issues/109552

Fan-out "ready to close" pointers are being deleted except on threads that already got a reply. This account still cannot close foreign tickets.

Skip: #108914, #109508, #109505, #109446.

Live snapshot 2026-09-13. kvnloo has **pull only** (no triage, no merge). Foreign closes 403. Authors can close their own.

## Board size

| | Open | Closed/merged |
| --- | --- | --- |
| Issues | 14,065 | 13,519 |
| PRs | 28,303 | 13,435 merged + 39,603 closed |
| `ci-reviewed` open | **0** | nothing in the merge queue |

Do not merge the 28k. Almost none are reviewed. `ci-reviewed` is the human merge gate and it is empty (Bot Screen #108914 is blocked on that label, not on red CI).

## The play (≈2,750 items, **labels only — not validated**)

We listed open tickets that already had the label. A sample of 40 `duplicate` PRs had a `Duplicate of #N` string pointing at a still-open number. That is **not** same-scope proof. It missed backwards labels (canonical closed as superseded by the "copy"), withdrawn canonicals, circular duplicates, and approved PRs. Do not bulk-close.

| Label | Open issues | Open PRs | Action |
| --- | --- | --- | --- |
| `duplicate` | **995** | **1,549** | Close as duplicate. Canonical stays. |
| `invalid` | **86** | **120** | Close as not planned (titles include `test`, `permission-probe-delete-me`). |
| `needs-repro` | 1,060 | — | Not this pass (real bugs waiting). |
| `P0` | 2 | — | Leave. |

Duplicate-labeled open PRs are concentrated (700 sampled): kokhlo 36, fangliquanflq 29, liuhao1024 15, then 8–12 each for Sahilvishnaliya, salch-cred, RelaxJonh, KoNit-K, webtecnica, KhanCold. One maintainer close-script beats 9 author pings.

Related clone farms that are **not** yet “fixed on main” (do not mass-merge): ~750 open PRs matching `close HTTP response` (KhanCold has 20 / 8 labeled duplicate); ~40 still-open heartbeat/fence PRs even though `87b013b` (`fix(cron): do not hold fire fence during heartbeat save_jobs`) is on `main`. After the duplicate label pass, grep that SHA against remaining titles.

## Maintainer one-liner (needs triage)

```bash
# Issues labeled duplicate
gh issue list --repo NousResearch/hermes-agent --label duplicate --state open --limit 1000 --json number \
  --jq '.[].number' | while read n; do
  gh issue close "$n" --repo NousResearch/hermes-agent --reason duplicate \
    --comment "Already labeled duplicate. Canonical is the issue/PR named in triage. Closing the copy."
  sleep 0.3
done

# PRs labeled duplicate (gh pr list, not issue list)
gh pr list --repo NousResearch/hermes-agent --label duplicate --state open --limit 1000 --json number \
  --jq '.[].number' | while read n; do
  gh pr close "$n" --repo NousResearch/hermes-agent \
    --comment "Already labeled duplicate of an open canonical. Closing the copy so review lands on one PR."
  sleep 0.3
done

# Obvious invalid
gh issue list --repo NousResearch/hermes-agent --label invalid --state open --limit 200 --json number,title \
  --jq '.[] | select(.title|test("^(test|permission-probe)";"i")) | .number' | while read n; do
  gh issue close "$n" --repo NousResearch/hermes-agent --reason "not planned" \
    --comment "Invalid / probe ticket."
  sleep 0.3
done
```

`--limit 1000` only gets a page. Duplicate issues are 995 (one page) and PRs 1549 (two pages). Loop with `--search` + cursor or GraphQL `after` until empty.

Do **not** auto-close `needs-repro`, `P0`, or Bot Screen follow-ups #109508 / #109505 / #109446 (cherry-picked into #108914, close those when 108914 lands).

## What kvnloo can do (done / not done)

Closed as author:

- https://github.com/NousResearch/hermes-agent/issues/102262 — labeled duplicate of #87119; `fallback add` still `_require_tty` on main, so the *canonical* stays open.

Not closed (hunks are **not** on main — file-exists is a false positive):

- #100017 bang-shell TTY/bare-`!` (main already has #72257 `!command` only)
- #98912 Telegram native clarify
- #98105 Groq Orpheus
- #94973 Wayland fullscreen (partial overlap with existing throttle tests)
- Kanban mobile #87494 / #88716 / issue #87186
- #108878 headed-cloud RFC (keep; complements #108592)

Do not merge those from this account. `mergeable_state` is dirty/unknown except #94973 `clean` (still needs `ci-reviewed`).

## Do not merge competing desktops

#97859, #17258, #104567, #90423, and #108878 stay. Not duplicates of Bot Screen.
