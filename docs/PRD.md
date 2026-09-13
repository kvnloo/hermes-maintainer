# Product requirements: hermes-maintainer

## Mission

Drive the Hermes Agent backlog toward a defensible zero by continuously converting raw GitHub
activity into a smaller set of verified problem families, coordinated implementation campaigns,
and integration-ready fix atoms.

`hermes-maintainer` is not a replacement maintainer. It is the repository's coordination and
analytics plane.

## Primary outcomes

1. Every open issue and PR has a current disposition or a reason it cannot yet have one.
2. Duplicate implementation work is detected before another full patch is written.
3. Existing patches are decomposed into useful donor atoms instead of merged or rejected only at
   whole-PR granularity.
4. Common root causes reveal missing Hermes primitives and opportunities to remove tech debt.
5. Maintainer attention is routed to the actual blocker: reproduction, product decision,
   integration, platform evidence, permissions, or CI.
6. A candidate future `main` can be evaluated as a dependency-closed set of fix atoms.

## Non-goals for v0.1

- autonomous merging or closing;
- executing untrusted PR code with secrets;
- replacing GitHub Actions;
- using an LLM's confidence as an authorization signal;
- a graph database migration before SQLite is proven insufficient;
- embeddings as the only duplicate detector.

## Core user stories

### Maintainer

- Show me the top campaigns by verified issue coverage and integration readiness.
- Show me which PRs overlap and how they differ.
- Show me the smallest donor set that covers the acceptance matrix.
- Show me which old PRs are already fully incorporated elsewhere.
- Show me which open issues appear fixed on current `main` but lack closure evidence.
- Show me repository mechanisms generating repeated bugs.

### Cloud coding agent

- Before implementing an issue, ask hermes-maintainer whether an active campaign already exists.
- Receive a bounded work packet such as "Windows reproduction" or "reconcile current main" instead
  of independently implementing the whole defect.
- Publish evidence back into the graph without gaining GitHub write authority.

### Repository analyst

- Query backlog dynamics over time.
- Compare creation, closure, merge, reopen, and supersession rates.
- Measure duplicate implementation effort and maintainer waiting time.

## Success metrics

Product correctness and collaboration hygiene must remain separate.

### Correctness metrics

- unique verified problem families resolved per week;
- reopened or escaped regressions;
- P0/P1 time-to-verification;
- accepted fix atoms with complete evidence receipts;
- candidate integration trees passing required acceptance matrices.

### Collaboration metrics

- overlapping PRs opened after a campaign already existed;
- implementation-hours redirected into missing evidence;
- median time from report to canonical problem family;
- median time waiting for maintainer vs contributor vs infrastructure;
- false duplicate links corrected;
- stale PRs resolved through incorporation, supersession, rejection, or refresh.

## Product states

### Node disposition

- `untriaged`
- `needs_reproduction`
- `canonical_problem`
- `active_implementation`
- `needs_integration`
- `needs_platform_evidence`
- `needs_maintainer_decision`
- `verified_fixed`
- `duplicate`
- `superseded`
- `wont_fix`

### Evidence levels

- `reported`: claim exists in issue/PR prose;
- `source_confirmed`: code inspection supports the claim;
- `reproduced`: failure observed on a pinned tree/environment;
- `verified_candidate`: proposed fix passes acceptance on its exact head;
- `verified_integration`: assembled campaign tree passes acceptance;
- `verified_main`: landing commit and current main satisfy acceptance.

These levels should never be collapsed into a boolean `fixed` field.
