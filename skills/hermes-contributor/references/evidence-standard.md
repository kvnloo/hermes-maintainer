# Evidence standard for hermes-agent changes

A small, owner-boundary patch with executable native evidence and preserved
human credit is worth more than many unverified branches.

## Proof ladder

| Level | Claim | Does not mean |
|---|---|---|
| Reported | A user reported a symptom | Bug reproduced |
| Source-confirmed | Source suggests the mechanism | Observed on a host |
| Reproduced | Pinned base fails a behavioural test | The patch works |
| Candidate-verified | Pinned head passes, base failed | Merged or approved |
| Integration-verified | Combined tree passes the acceptance set | Present in main |
| Main-verified | Landed SHA and current main pass | Guaranteed forever |

Say which level you reached. Do not round up.

## RED / GREEN / removal control

```bash
BASE=$(git rev-parse origin/main)          # or the carrier PR head
HEAD_SHA=$(git rev-parse HEAD)             # your candidate
T=tests/<area>/test_<topic>.py

# RED: the new test against base production code, in a separate worktree
git worktree add --detach ../hermes-base $BASE
git show $HEAD_SHA:$T > ../hermes-base/$T
(cd ../hermes-base && scripts/run_tests.sh $T -q)   # expect: fails for the right reason

# GREEN: same command on the candidate head
scripts/run_tests.sh $T -q                           # expect: passes

# Removal control: revert only the production change, keep the test
git diff --name-only $BASE $HEAD_SHA -- . ':!tests' | xargs git checkout $BASE --
scripts/run_tests.sh $T -q                           # expect: fails again
git checkout $HEAD_SHA -- .                          # restore the candidate
git worktree remove ../hermes-base
```

Use the repo's runner (`scripts/run_tests.sh` / `just test <paths>`); it sets
the hermetic environment and per-file isolation CI uses. Run
`python scripts/check` before asking for review.

## Test quality

- Behavioural: real imports, temp `HERMES_HOME`, mock only at a real network edge.
- No source-text assertions, no change-detector tests, no faked `sys.platform`
  as proof of another OS.
- Cover sibling entry points of the same invariant, not only the reported path.
- Prompt-surface changes need the committed `scripts/ci/prompt_surface.py render`
  snapshot (see root `AGENTS.md`).

## Receipt template

```
Upstream main SHA + date checked:
Base SHA (main or carrier head):
Candidate head SHA:
Files read (AGENTS/CONTRIBUTING/SECURITY/area AGENTS):
Related issues + PRs (all states), carrier:
Root cause line + sibling paths checked:
RED command + result (base):
GREEN command + result (head):
Removal control command + result:
python scripts/check result:
CI URL for this exact head, or NOT_RUN:
NOT_RUN (platforms/suites) and why:
Credit (reporter, donor PR authors, reviewers):
Next action + owner:
```

## Ownership and credit

- **Merge intact:** the original author's PR has the needed behaviour.
- **Donor:** its commits/tests are carried in someone else's surviving PR.
- **Carrier:** an integration PR preserving credited changes from others.
- **Superseded:** behaviour landed independently; cite the landing SHA.
- **Parked:** unverified or waiting on a platform or owner.

Prefer cherry-picks that keep authorship over re-creating an equivalent patch
under a different author. A draft PR on a fork is not an upstream merge; human
authorization, branch policy and unresolved review threads are gates.
