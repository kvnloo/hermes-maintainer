# Community autodevelop (needs-discussion)

Tracking: [PER-1597](https://linear.app/0ism/issue/PER-1597/formalize-hermes-autodevelop-personal-growth-vs-gated-community-report).
Protocol: [Verified OSS Loop](https://github.com/kvnloo/verified-oss-loop) `SPEC.md` §10. Do not invent a second loop.

Product ask (Kevin Rajan / @kvnloo, 13 Sep 2026) to Teknium: programmatic access so people using the Hermes app can complain about an issue, have Hermes find a fix, then post to GitHub — without turning that into spam.

## Two autodevelops

**Personal autodevelop** already exists in Hermes (skills, curator, memory, checkpoints, local growth with the user). Keep it. Do not reinvent it as a GitHub factory.

**Community autodevelop** is the in-app loop: complain → triage/repro → optional local fix → **gated** GitHub issue/PR.

## Ownership

| Layer | Owner | Must not own |
|---|---|---|
| Protocol / clutter policy / intake ladder | `kvnloo/verified-oss-loop` | Product UI; NousResearch writes |
| Hermes-manages-Hermes operations + this local inbox | **this repo** | Origin issues/PRs on `NousResearch/hermes-agent` |
| In-app/CLI `/report` (later) | `NousResearch/hermes-agent` thin command + skill | New core model tool; in-tree third-party product plugins |

GitHub writes from this repo stay on `kvnloo/hermes-maintainer`. Scanning origin Hermes is read-only.

## Gated flow

1. Capture locally (`hermes-maintainer report ingest`). Default disposition: `local_draft`.
2. Triage / reproduce against the relevant checkout. Dedupe; do not scrape-and-spray.
3. Promote to a public GitHub issue only when VOL §10 gates pass **and** this package is allowed to write (it is not, until M6 — and never to origin Hermes).
4. PR only from a claimed issue with an exact-head receipt. Workers never merge `main`/`dev`.

## This repo's first slice

```bash
hermes-maintainer report ingest --title "…" --body "…"
hermes-maintainer report list
hermes-maintainer report show <id>
hermes-maintainer report promote <id>
```

`performed_origin_write` is always false. A report whose target is `NousResearch/hermes-agent` cannot become `origin_issue_allowed` here.

## Non-goals

- Unsolicited public issues/comments/PRs on `NousResearch/hermes-agent`
- Robomp-style auto-implement on origin
- New core Hermes tools or `HERMES_*` non-secret env vars
- Replacing personal autodevelop with GitHub

Related: PER-1508 (optional self-report skill, origin PR #108879), PER-1499 (issue-completeness bot, not robomp).
