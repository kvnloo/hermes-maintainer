# What makes a Hermes contribution reviewable

The key transferable experience: **a small, owner-boundary patch with executable native evidence and preserved human credit is worth more than many unverified implementation branches.**

## Proof ladder

| Level | What the claim means | What it does not mean |
| --- | --- | --- |
| Reported | A real user/author reported a symptom | Bug reproduced |
| Source-confirmed | Source and design suggest the mechanism | Observed on a host |
| Reproduced | Exact pinned base fails the behavioral test | Proposed patch works |
| Candidate-verified | Exact candidate head passes and baseline failed | Merged or approved |
| Integration-verified | Combined tree passes the acceptance matrix | Present in main |
| Main-verified | Landed SHA plus current main passes | Guaranteed forever |

Source: [hermes-maintainer PRD](../docs/PRD.md) for evidence levels; upstream [AGENTS](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md) for executable tests and boundaries.

## Checklist before a PR is reviewed

- Is the current behavior genuinely wrong? Inspect actual logic, git log and upstream design discussions, not a conjectured absence.
- Can you quote the line or branch where it manifests? Include the sibling call sites, not only one reported path.
- Is there a test that is red at *current base* and green at the *exact changed head*?
- Is the test behavioral using real imports, temp runtime/profile and mock network only at a real dependency edge? No source-text grep assertions, no fake sys.platform pretending to prove Windows behavior.
- Run **scripts/run_tests.sh**, not bare pytest, for upstream Hermes ([TESTING.md](./TESTING.md)); run python scripts/check for all blocking lint checks. Note platform-specific suites and the commands you cannot execute.
- Does the patch preserve prompt-cache invariants, existing adapter behavior and strict profile isolation? Did it avoid widening core tools and adding configuration env vars?
- Does it require documentation changes, config drift tests, lockfile changes or prompt-surface snapshots? Follow area AGENTS.
- Scan fresh PRs and review comments again at the end. A competing fix or a stale branch changes the disposition.
- Record exact base/head SHA, actual commands, stdout/result, CI URL and NOT_RUN. Don't copy a green check from another revision.

## Ownership and credit

Review new PRs for overlap before writing code. If someone already owns the patch, send the missing reproduction, test, fix atom, or code review *through an authorized channel*. Prefer adoption/cherry-pick that retains authorship rather than recreating an equivalent PR under a different author. Distinguish:

- **Merge intact:** original author PR contains needed behavior/evidence.
- **Donor:** useful commits/tests are incorporated into someone else's survivor.
- **Carrier:** an integration PR preserving credited changes from another patch.
- **Superseded:** target behavior landed independently; close the loop with a traceable landing SHA.
- **Parked:** unverified or waiting on platform/owner; do not inflate “ready” counts.

Remember that a draft fork PR is not an upstream merge. Human authorization, branch policies, unresolved review threads, and slot/cadence limits are gates; never auto-merge or use broad permission as authority.

## Security and reviewer load

Follow upstream [SECURITY.md](https://github.com/NousResearch/hermes-agent/blob/main/SECURITY.md) for private reporting. Do not publicize private exploit instructions. Make bounded, substantive review comments only when requested or explicitly allowed; avoid unsolicited maintainer pings, generic bot praise, and issue spam.

**Success:** accepted behavior and protected user intent, not raw PR or comment volume.
