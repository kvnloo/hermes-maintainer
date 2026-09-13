# Task 01: stack and patch identity

## Goal

Make PR ancestry and contribution identity accurate enough that stacked child PRs do not
massively double-count inherited commits.

## Deliverables

- ingest commit SHAs for open PRs into `pr_commits`;
- fetch refs into the local mirror where needed;
- compute stable patch IDs for commit candidates;
- identify likely inherited prefix commits when a PR targets a feature branch;
- add `stacked_on`, `patch_equivalent`, and `incorporates_commit` relation generation;
- tests with synthetic git repositories covering branch stacks and cherry-picks;
- do not add embeddings or UI changes.

## Acceptance

A test modeled after Bot Screen must show that a test-only child targeting a feature branch is not
scored as a 50+ commit independent implementation.
