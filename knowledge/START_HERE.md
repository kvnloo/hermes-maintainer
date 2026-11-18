# Start here: become useful to Hermes in one session

**Who this is for:** a newcomer, an issue triager, a reviewer, or a coding agent. You do not need the history of anybody else's prior sessions.

**This repository is an independent contributor knowledge base, not an official NousResearch policy or a maintainer endorsement.** The upstream repository, not this guide, wins if the two disagree.

## Your first 10 minutes

1. Read the live [Hermes README](https://github.com/NousResearch/hermes-agent/blob/main/README.md), [CONTRIBUTING](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md), [AGENTS](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md), and [Security](https://github.com/NousResearch/hermes-agent/blob/main/SECURITY.md).
2. Identify the *user-visible symptom* and its actual intended behavior. Never treat an issue title as a specification.
3. Search current source, issues, and **all-state PRs**, including already merged work. GitHub issue state can lag main.
4. Inspect the area-specific AGENTS.md and git history for the affected invariant; check sibling entry points, not just the reporter's path.
5. Before opening work, find an existing contributor to help. Salvage tests, credit original authors, and avoid competing patches.
6. On a pinned base SHA, make an executable regression fail; on a pinned candidate SHA, make it pass using the repo's native test runner.
7. Produce a short evidence receipt, identify an owner-side next action, and leave publication or merge to an authorized human.

**Start with [TRIAGE_WAVES.md](./TRIAGE_WAVES.md) for repeatable research; [REVIEW_EVIDENCE.md](./REVIEW_EVIDENCE.md) for proof; [HERMES_INTENT.md](./HERMES_INTENT.md) for architecture and public direction; [PUBLIC_CASES.md](./PUBLIC_CASES.md) for real examples; [CURRENT_PUBLIC_WORK.md](./CURRENT_PUBLIC_WORK.md) for a dated, publicly sourced issue radar.**

## Find your level

- **Learn:** Ask where a feature enters, which component owns it, and why its invariant exists. Read the answer's *source and SHA*, not a free-floating summary.
- **Triage:** Run a bounded wave: group reports by root cause, compare overlapping PRs, and recommend *next evidence*, not mass closures.
- **Contribute:** Select one unique gap; patch on an authorized fork/worktree; run exact commands; open a Draft PR only after checking ownership and review constraints. No upstream writes or merges by default.
- **Review:** Challenge the baseline reproduction, platform fidelity, data boundaries, sibling callers, negative tests, and whether the code changes the intended feature into a no-op.

## What this knowledge base deliberately adds

Upstream docs say what is supported. Here we capture **how to decide**, **where waves get stuck**, **what evidence changes a maintainer decision**, and **how to hand off a problem family**. Unlike an agent's memory, these are versioned, reviewable and linked to publicly checkable facts.

The live issue/PR graph is **not an authority**: similar text is only a retrieval hint. The issue/PR or current source is the authority for the claim. For a dynamic answer say “checked at [SHA] on [date]” and distinguish OBSERVED, INFERRED and PROPOSED.

## Start with real public entry points

- [Hermes source](https://github.com/NousResearch/hermes-agent)
- [Current issues](https://github.com/NousResearch/hermes-agent/issues)
- [All pull requests](https://github.com/NousResearch/hermes-agent/pulls?q=is%3Apr)
- [Developer guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/developer-guide)
- [ACP integration guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/programmatic-integration.md)
- [Hermes-maintainer campaign graph](../README.md)

## Data safety

Keep personal notes, private factory tracking, tokens, screenshots with secrets, and unpublished maintainer messages **out of this public repository**. Generalize a lesson; cite only public primary sources. Security vulnerabilities subject to upstream SECURITY.md private reporting rules never enter public examples.
