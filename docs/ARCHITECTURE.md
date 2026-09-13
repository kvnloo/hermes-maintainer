# Architecture

## System shape

```text
                     GitHub API                    git remote
                         |                             |
                         v                             v
                   metadata ingest               bare mirror
                         |                             |
                         +-------------+---------------+
                                       v
                              normalization layer
                                       |
                                       v
                             SQLite backlog graph
                      +----------------+----------------+
                      |                |                |
                      v                v                v
                explicit refs    similarity engine   git analysis
                      |                |                |
                      +----------------+----------------+
                                       v
                                  campaigns
                                       |
                                       v
                                   fix atoms
                                       |
                     +-----------------+------------------+
                     |                                    |
                     v                                    v
                evidence engine                    merge-set optimizer
                     |                                    |
                     +-----------------+------------------+
                                       v
                                  local API/UI
                                       |
                                       v
                            agent work packet generator
```

## Durable core

SQLite is the source of truth for repository-derived maintenance state. FTS5 is used for lexical
retrieval. The git mirror is the source for ancestry and patch content. GitHub remains the source
for live issue/PR metadata.

The graph uses ordinary tables because most operations are simple joins and bounded traversals.
A graph database is only justified if measured query or traversal complexity requires one.

## Scan classes

### Fast scan

Target cadence: every 15 minutes.

- fetch/freshen git mirror;
- ingest recently updated issues and PRs;
- parse explicit relationships;
- recompute cheap lexical similarity candidates;
- rebuild affected campaigns;
- update health metrics.

### Deep scan

Target cadence: every 6 hours.

- everything in fast scan;
- enrich open/high-value PRs with changed files and commits;
- compute patch hashes and patch IDs;
- calculate code-overlap edges;
- refresh CI/evidence receipts;
- re-extract fix atoms;
- run optimizer;
- emit bounded work packets for unresolved campaign gaps.

### Historical backfill

One-time or low-priority batches:

- crawl older closed/merged work;
- infer historical resolution patterns;
- establish known donor/survivor relationships;
- build evaluation datasets for triage quality.

## Relationship ontology

The system must preserve different meanings instead of converting them into `duplicate`.

| Relation | Semantics |
|---|---|
| `duplicate_of` | Same defect and acceptance criteria; no unique unresolved scope |
| `possible_duplicate` | Similarity candidate requiring verification |
| `same_root_cause` | Different symptoms caused by the same underlying mechanism |
| `complements` | Adds missing behavior or evidence to another implementation |
| `depends_on` | Requires another change to function |
| `stacked_on` | Git or feature-branch dependency |
| `fixes` | Author claims the source resolves the target |
| `partially_addresses` | Only some acceptance criteria are satisfied |
| `supersedes` | Source is intended to replace target work |
| `incorporates_commit` | Specific donor commit is present in survivor history |
| `patch_equivalent` | Stable patch-ID or stronger evidence suggests equivalent patch content |
| `conflicts_with` | Cannot be selected together without reconciliation |
| `verified_fixed_on` | Acceptance verified on a pinned commit/tree |
| `regresses` | Reintroduces a previously fixed acceptance criterion |

## Campaigns

A campaign is a coordination object centered on a problem family, not a GitHub primitive. A
campaign can contain multiple issues, competing PRs, donor commits, test-only follow-ups, and one
or more integration candidates.

Campaign roles:

- canonical problem;
- active survivor candidate;
- donor implementation;
- provenance carrier;
- test/evidence donor;
- stacked child;
- superseded implementation;
- unresolved alternative design.

## Fix atoms

A fix atom is the smallest reviewable unit that can participate in selection.

MVP atoms are PR-level. The target model is commit/hunk-aware:

```text
FixAtom
  id
  source_pr
  commits[]
  affected_symbols[]
  acceptance_criteria[]
  closes[]
  supersedes[]
  requires[]
  conflicts[]
  evidence_receipts[]
  cost
  risk
  value
```

Whole PRs should never be treated as indivisible if they mix unrelated fixes.

## Optimizer

Correctness and policy are hard constraints. Only then should the system optimize coverage.

Illustrative objective:

```text
maximize
  verified_issue_weight
+ superseded_pr_weight
+ architecture_debt_removed
+ measured_performance_gain
- review_cost
- conflict_cost
- dependency_cost
- new_dependency_cost
```

The greedy solver is the baseline because it is transparent and cheap. CP-SAT becomes useful once
requires/conflicts and alternative implementation groups are populated reliably.

## Agent architecture

Agents are workers around the graph, not owners of repository truth.

- Mapper: proposes typed relationships.
- Reproducer: tries to turn a report into a pinned failure receipt.
- Specifier: converts a family into acceptance criteria.
- Integrator: assembles donor atoms on current main.
- Challenger: searches for counterexamples and sibling callers.
- Performance auditor: benchmarks candidate vs baseline.
- Security auditor: reviews privilege and sensitive-data boundaries.

Every agent returns structured evidence. None of these roles needs GitHub mutation authority.
