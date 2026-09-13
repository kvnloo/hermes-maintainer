# Roadmap

## M0: runnable local graph

Included in this scaffold:

- git mirror;
- GitHub issue/PR ingestion;
- typed explicit references;
- SQLite/FTS5 backlog graph;
- lexical similarity;
- campaign candidates;
- PR-level fix atoms;
- greedy optimizer;
- local dashboard;
- fast/deep daemon loop.

## M1: accurate commit and stack model

- ingest all open PR commit lists and file patches;
- compute stable patch IDs from the local mirror;
- detect base branches that target feature branches;
- infer stacked PR parent/child edges;
- distinguish inherited stack commits from new contribution commits;
- identify commits already landed in another PR or main.

## M2: evidence engine

- ingest check runs and workflow outcomes by exact head SHA;
- record fails-before/passes-after receipts;
- model disabled/missing checks distinctly from success;
- add platform coverage matrix;
- add acceptance criteria objects;
- add baseline-vs-candidate performance receipts.

## M3: high-quality semantic triage

- add optional embeddings provider;
- retrieve top lexical/code candidates first, then rerank semantically;
- add a relationship mapper agent in shadow mode;
- build a human-reviewed evaluation set;
- tune thresholds from measured false-link cost.

## M4: campaign coordination

- canonical problem specification;
- expiring implementation claims;
- agent work packet generator;
- separate tasks for reproduction, integration, security, performance, and platform evidence;
- one stable coordination summary per campaign.

## M5: exact integration planning

- commit-level/hunk-level atoms;
- requires/conflicts/alternative groups;
- CP-SAT solver;
- automatic temporary integration worktrees;
- campaign acceptance runners;
- candidate future-main comparison.

## M6: restricted publisher

Only after shadow-mode accuracy is demonstrated:

- propose labels/links/comments;
- require deterministic policy validation;
- bind writes to current SHA/revision;
- preserve contributor credit and unresolved unique scope;
- support easy human reversal;
- keep merge/close authority human by default.
