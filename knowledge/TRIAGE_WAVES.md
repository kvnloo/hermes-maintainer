# The repeatable Hermes wave

This playbook distills lessons from many downstream attempts. It is **community process guidance**, not authority to write to NousResearch/hermes-agent. A wave should reduce unique unresolved problems and reviewer load, not maximize issue/PR count.

## Input contract

State the target area, time budget, repository/revision, allowed write scope, verification hosts, and desired output. If any authority is uncertain, treat the upstream as read-only. Pin both the current main commit and candidate PR head; re-fetch after long-running work.

## Wave algorithm

1. **Orient.** Read upstream AGENTS, CONTRIBUTING, SECURITY, area AGENTS, source and recent owner discussions. Check whether the defect is intentional by searching the relevant git history and design decision.
2. **Find demand.** Search recent real user reports, exceptions and regressions. Search *all* issue/PR states, sibling bug titles and existing fixes. Avoid choosing tasks from an issue title alone.
3. **Cluster by invariant.** Group reports by shared root cause while keeping different symptoms and acceptance criteria distinct. Link possible_duplicate, same_root_cause, complements, supersedes and partial coverage separately; confidence is not proof.
4. **Rank by integration leverage.** First reviewer-requested fixes or red CI; then repairs of active contributor-owned PRs; then reproducible high-impact user bugs; speculative feature ideas last. Prefer donating tests/fixes to original authors rather than competing.
5. **Reproduce and falsify.** Explain expected vs observed behavior; locate the ownership-boundary line. Use a current-main negative test and inspect sibling ingress paths (CLI, TUI, gateway, ACP, Desktop, platform adapters).
6. **Build one minimal fix.** Preserve intended capability; respect prompt-cache stability, plugin boundaries and profile/session ownership. Use the repo's real test runner, area test imports, platform markers and isolated HERMES_HOME.
7. **Verify on exact revisions.** Prove regression RED on base and GREEN on candidate; document environment, command, current-head CI and what was NOT run. A green synthetic fixture is not native platform proof. Check no concurrent change supersedes the work.
8. **Review before publication.** Independent challenger: user intent, negative paths, races, concurrency, security, backward compatibility, provenance, scope, release/docs impact. Never claim maintainer acceptance from a draft.
9. **Publish within the allowed lane.** Write to the authorized downstream fork only by default; one scoped branch and Draft PR. No upstream issues, comments, reviews or merges without specific authorization. Credit reporter, PR donor, reviewers.
10. **Handoff.** Produce one evidence packet for the next human/agent. Record disposition and *next action*; do not keep a worker running solely to create activity.

## Triage disposition model

- **PROMOTE:** actual reproduction, unique scope, candidate fix, exact-head native evidence, no competing implementation, reviewer or human gate satisfied.
- **UNDRAFT_READY:** candidate appears ready to ask for review, but only authorized human changes its status.
- **HOLD:** missing reproduction, failing platform test, owner decision, unresolved reviews, conflict or competing PR; specify one clear unblock.
- **DROP / SALVAGE:** superseded or wrong premise, but preserve useful tests and authored atoms where possible; donor and carrier are not identical to failure.

These labels describe *our decision support*, not GitHub issue states or maintainer verdicts.

## Required wave output (small enough to hand off)

    Issue / user symptom:
    Checked main SHA + date:
    Current source / intent citation:
    Related issues + PRs (all states):
    Root cause and sibling-path assessment:
    Acceptance behavior:
    Candidate / donor authorship:
    Base failing command/result:
    Head passing command/result:
    Native OS/CI evidence or NOT_RUN:
    Risks / competing head / conflict:
    Disposition (PROMOTE | UNDRAFT_READY | HOLD | DROP/SALVAGE):
    Owner + next action:
    Authorized write scope:

## Parallel work without duplicated patches

Separate *evidence seams*, not five full implementations: Linux vs Windows vs macOS native reproduction, source audit of sibling entry points, safety adversary, performance baseline, current-main integration. Have a single canonical problem statement and one survivor patch. Stop on a live owner claim or conflicting head.

## “Do a wave” starter prompt

“Read the current Hermes AGENTS/CONTRIBUTING and this guide; use current upstream main, not memory. Search active and merged competing PRs. Group the top reproducible user-impact problem families in [area]. For each show issue, current head, ownership boundary, test strategy, maintainer/reviewer demand, author/provenance, and one of PROMOTE/HOLD/DROP. Work only in [authorized fork]; never upstream, merge or publish without permission. Return citations and exact verification commands.”
