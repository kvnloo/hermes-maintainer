# Master execution plan

## North star

Hermes-maintainer continuously maintains a model of:

```text
main + candidate fix atoms + evidence + conflicts + dependencies -> best next integration tree
```

The product should make it cheaper to integrate existing good work than to generate another
competing implementation.

## Phase 0: bootstrap

1. Create repository `hermes-maintainer` from this scaffold.
2. Run `scripts/bootstrap.sh`.
3. Configure a read-only `GITHUB_TOKEN`.
4. Run a deep scan.
5. Inspect the first campaigns in the local dashboard.
6. Commit the initial generated database only if you intentionally want a snapshot fixture. By
   default `.data/` remains local.

## Phase 1: establish truth before autonomy

Implement stack identity and CI evidence first. These are prerequisites for reliable backlog
compression. Without them, a stacked child can look like a huge independent PR and an unrun check
can look like success.

## Phase 2: measure triage

Build the human-reviewed relation evaluation set. Run lexical retrieval as baseline. Add semantic
reranking only when it improves measured retrieval without unacceptable false links.

## Phase 3: coordinate cloud agents

Expose work packets from campaign gaps. Good parallel tasks are different evidence seams:

- Linux reproduction;
- Windows reproduction;
- macOS reproduction;
- source audit of sibling callers;
- security boundary review;
- performance benchmark;
- current-main integration.

Bad parallelism is five agents writing five full implementations of the same acceptance criterion.

## Phase 4: integration optimizer

Once requires/conflicts and exact-head evidence exist, enable CP-SAT to search larger candidate
sets. The optimizer may propose a tree. It never certifies the tree. Verification does that.

## Phase 5: repository feedback loop

In shadow mode, generate suggested GitHub links and campaign comments for maintainers to review.
Only after measured precision is high should a restricted publisher be considered.

## Initial Hermes campaigns to seed

Use `seed/audit/campaign_seeds.json` and revalidate against current repository state. Early useful
families from the audit include:

- CI verdict integrity;
- MCP OAuth issuer relay;
- profile subprocess provenance/isolation;
- unified session ownership/gateway campaign;
- bot-screen stack and follow-up fixes;
- cross-process locking/checkpoint corruption;
- polling/single-flight/backoff performance debt.

## First week target

A good first week is not "close 5,000 issues". It is:

- a trustworthy local graph over all open work;
- correct stack identity for open PRs;
- exact-head CI evidence;
- 20-50 high-confidence campaigns manually spot-checked;
- the first cloud-agent work packets generated from missing evidence;
- one real campaign integrated more efficiently because the graph existed.
