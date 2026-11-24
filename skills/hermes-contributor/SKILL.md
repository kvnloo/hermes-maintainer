---
name: hermes-contributor
description: Use when contributing to hermes-agent. Load landing facts.
version: 1.0.0
author: hermes-maintainer contributors
metadata:
  hermes:
    tags: [hermes-agent, contributing, code-review, github, evidence, triage]
    category: software-development
    related_skills: [github, test-driven-development, systematic-debugging]
    requires_toolsets: [terminal]
---

# Hermes contributor

Non-obvious context for planning, reviewing or measuring a contribution to
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). Upstream
files at the current head always win over this skill; this skill tells you which
files to read, what the project's landing mechanics are, and what evidence a
maintainer acts on.

Community guidance from the independent
[hermes-maintainer](https://github.com/kvnloo/hermes-maintainer) knowledge base.
It is not NousResearch policy and grants no authority to write upstream.

## When to Use

- Planning a fix, feature or test for hermes-agent (pick work, avoid duplicates).
- Reviewing a hermes-agent PR or preparing one for review.
- Measuring anyone's contribution record, including your own.
- Offering help on a maintainer's open PR.

Do not use it for operating or configuring Hermes as a user; load the
`hermes-agent` skill for that.

## Canonical facts (re-verify, then rely on them)

1. **Work lands by maintainer salvage.** Maintainers usually cherry-pick a
   contributor's commits into their own carrier PR, keep the original author on
   each commit, merge the carrier and close the contributor PR. A PR shown as
   "closed, not merged" often means the code shipped. Root `AGENTS.md` lists
   "salvage by cherry-pick so authorship survives" as wanted behaviour.
2. **Impact = commits on `main` authored by the person.** Never report
   PR-merge counts as impact on this repo; they are close to meaningless here.
   Commands: `references/how-work-lands.md`.
3. **The highest-yield channel is an add-on commit on a maintainer's open PR**,
   offered early, with red/green evidence pinned to SHAs. Community PRs and
   issue comments convert far less often. Pattern below.
4. **Tests run through `scripts/run_tests.sh`** (or `just test <paths>`), never
   bare `pytest`. Lint is `python scripts/check` (`just check`).
5. **Two design invariants** decide most reviews: per-conversation prompt
   caching is sacred, and the core is a narrow waist (new capability arrives as
   CLI + skill, service-gated tool or plugin, not a new core tool).

Any figure older than a week (counts, rates, rankings) must be re-measured
before you quote it.

## Context-load procedure

Run this before writing code or a review. Record the SHA you read.

1. Pin upstream: `git fetch origin main && git rev-parse origin/main` (or
   `gh api repos/NousResearch/hermes-agent/commits/main --jq .sha`).
2. Read at that SHA: root `AGENTS.md` (contribution rubric, footprint ladder),
   `CONTRIBUTING.md` (test environment, skill/plugin rules), `SECURITY.md`
   (§3.1 findings go private, never into a public issue, PR or commit).
3. Read the **nearest area `AGENTS.md`** for every directory you touch
   (`agent/`, `tools/`, `hermes_cli/`, `gateway/`, `plugins/`, `tests/`,
   `skills/`, `cron/`, `tui_gateway/`, `web/`, `apps/desktop/`, ...). They load
   automatically in Hermes sessions but not in other harnesses.
4. Check intent before calling something a bug: `git log -p -S "<symbol>"` on
   the line in question. Isolation and absences are often deliberate.
5. Search **all-state** PRs and issues; merged work often closes an open issue
   late:
   ```bash
   gh pr list -R NousResearch/hermes-agent --state all --search "<keywords>" --limit 50
   gh issue list -R NousResearch/hermes-agent --state all --search "<keywords>" --limit 50
   gh search commits --repo NousResearch/hermes-agent "<keywords>" --limit 30
   ```
6. **Find the maintainer carrier** before opening anything. Look for an open
   maintainer PR in the same area or one that already cherry-picks the
   relevant contributor PR (`references/how-work-lands.md` § Finding the
   carrier). If one exists, contribute to it instead of opening a competing PR.
7. Check sibling entry points of the same invariant (CLI, TUI, gateway, ACP,
   desktop, platform adapters), not only the reporter's path.

## Evidence standard

A maintainer acts on a receipt, not a description. Minimum:

- **Pinned SHAs:** exact upstream base SHA and exact candidate head SHA.
- **RED on base:** a behavioural test that fails on the base SHA for the right
  reason, run with `scripts/run_tests.sh <path>`.
- **GREEN on head:** the same command passes on the candidate head.
- **Removal control:** revert only the production change on head (keep the
  test); the test goes red again. This proves the test detects the fix, not an
  incidental change.
- **NOT_RUN:** platforms or suites you could not execute, stated plainly. A
  synthetic fixture is not native platform proof.

Tests use real imports and a temp `HERMES_HOME`; mock only at a real network
edge; no source-text assertions or change-detector tests. Full ladder and the
receipt template: `references/evidence-standard.md`.

## Add-on commit on a maintainer PR

1. Fetch the carrier head: `gh pr checkout <N> -R NousResearch/hermes-agent`
   and note `git rev-parse HEAD`.
2. Add one small commit on top: the missing test, the sibling-path fix, or the
   review item. Keep your own author identity; never rewrite theirs.
3. Produce the receipt (RED on carrier head without your commit, GREEN with it,
   removal control).
4. Push the branch to your fork and leave one comment on the carrier PR with
   the compare link (or a `git format-patch` attachment), the pinned SHAs and the
   receipt. Offer, do not demand; maintainers cherry-pick what fits.
5. Offer early: offers made within about a day of the carrier opening are the
   most likely to be adopted. Do not re-ping.

## Pitfalls

- Reporting "PRs merged" as someone's impact. Use commits on `main`.
- Opening a competing PR when a carrier or contributor PR already owns the fix.
  Donate the test or fix atom to it instead.
- Choosing work from an issue title. The title is not a spec; reproduce on
  current `main` first.
- Copying a green check from another revision. Re-run on the exact head.
- Adding `HERMES_*` env vars for non-secret config, a new core tool, or a
  "fix" that disables the feature it secures. Root `AGENTS.md` rejects these.
- Posting security-relevant repros publicly. Follow `SECURITY.md`.
- Treating this skill's figures as current. Re-measure.

## Verification

Before you report or publish, confirm you can state: upstream SHA and date
checked; files read; all-state PR/issue search done; carrier found or confirmed
absent; RED/GREEN/removal-control commands with results; NOT_RUN list; and that
nothing was written to NousResearch/hermes-agent without explicit authorization.
Source and authority order: `references/sources.md`.
