# Hermes repository coordination audit

**Read-only research snapshot: September 12, 2026, America/Chicago**

## Decision

Improve the existing maintenance system with a shared evidence index and an explicit implementation-admission process. Do not add independent bots that repeatedly review the same work and open competing fixes. The unit of work should be a verified problem family, with contributor patches treated as possible implementation material.

The first pilot should be the CI-verdict family around issue #98557. It already has competing implementations, a source-confirmed defect, and a larger composite addressing sibling failure paths. It is also a prerequisite for trusting an automated merge-selection system.

## Scope and evidence boundaries

Hermes main was pinned to `205645ee424163c7b6cfc032c331c3557797497b`. OpenCode dev was pinned to `95daf90670b7c039c436c85537da5fbfe2205b41`. Gemini CLI and Goose source-search snapshots were pinned to `9c1b0a610534d6f8120964cf2672c07807d8fc90` and `50666ae0b9a51e260b52b7efbab2e4e020346e94` respectively.

The Hermes workflow filename inventory covers 35 entries and came from a non-truncated Git tree response. Content review was selective: repository policy, central CI, review-label handling, rerun behavior, and the live CI-comment workflow. Competing CI patches were inspected, along with selected descriptions in other consolidation families. This was not a complete crawl of every issue, comment, commit, or source file. The public deployment code for the existing Hermes sweeper was not located in the inspected paths. Effective branch-protection rules were not established. A full local clone could not be obtained because container network access was unavailable.

The included 16 passing checks are isolated predicate probes, a reduced YAML parser test, and synthetic pagination counterexamples. They are not Hermes's test suite, live Actions runs, or certification of an integration branch. Nothing was posted, merged, closed, or deployed.

An earlier count of still-open items created within a date interval measures the surviving cohort, not total incoming work. Net repository dynamics require actual creation, merge, closure, and reopening events.

## Observed Hermes dynamics

### H1. Desired policy already exists

`AGENTS.md` already instructs contributors to solve whole bug classes, preserve authorship, and avoid duplicate infrastructure. It explicitly recommends a common abstraction when multiple PRs implement the same category. Its sweeper policy narrowly constrains automatic closures and reserves taste-based scope decisions for humans. A duplicate label alone is neither proof of equivalent behavior nor permission to close. [H_POLICY]

The missing work is making this policy executable and discoverable at the moment a contributor or agent selects a task.

### H2. The verification signal needs repair before it can drive automation

The central aggregate gate blocks only a literal `failure` result. Its predicate accepts `cancelled` and unrecognized result strings. The local probe reproduces that predicate behavior and demonstrates the allowlist alternative. This is a source-level finding, not a claim that a particular untested PR actually merged. [H_CI]

The orchestrator also disables the Desktop E2E lane with `if: false`. Other tests and separate workflows exist; the finding is specifically about this default lane. CI consumers must distinguish an intentional inapplicable skip from missing verification. [H_CI]

### H3. One defect already has several different patch shapes

| PR | Inspected contribution | Consequence for consolidation |
|---|---|---|
| #98563 | Small success/skipped allowlist predicate; inspected head `68ca8e5b9ea2ec6be9fb4eecafef67ff2cd5896f`; API reported conflicts | Useful minimal donor, not an immediately merge-ready recommendation |
| #98684 | A failure/cancelled/empty denylist plus a separate model-pricing change in the returned patch | Do not treat the entire PR as a CI-only fix atom |
| #108055 | Narrow cancelled-state predicate; inspected head `c907c76a4fae8aaef29158ba8fb9041ccaade233` contains an unindented assignment outside its YAML block scalar | A reduced source-fragment parser test fails; repairing indentation makes the control parse |
| #103195 | Aggregate-gate changes, reusable-workflow concurrency, review-comment verdict handling, and tests | Existing composite campaign to reconcile, rather than opening another competing PR |

Sources: [PR98563], [PR98684], [PR108055_SOURCE], [PR103195].

The composite's additional behaviors are not automatically redundant with a one-line predicate. Its broader scope and current conflicts still require review. No whole-PR merge recommendation is established by these probes.

### H4. Fork contributors are omitted from one useful feedback surface

The live CI-summary workflow deliberately excludes fork PRs. It safely checks out trusted default-branch automation, but the fork exclusion means that this particular summary does not explain those contributors' verification state. The replacement should keep the trusted publisher while reading only verified API metadata for forks. It must never execute the fork head or treat a downloaded artifact as executable trusted input. [H_COMMENT]

### H5. Authorization and build outcomes are coupled unnecessarily

The review-label workflow checks for the presence of `ci-reviewed`. The inspected check does not bind that authorization to an exact reviewed diff. The label-rerun workflow can wait for CI completion and then rerun every failed job, not only the approval gate. [H_LABEL] [H_RERUN]

Proposed change: issue a reviewer-approved record bound to relevant changed-path digests and a policy revision. Reevaluate the permission gate separately from rerunning tests. This proposal does not claim that no other external automation revokes stale labels today.

### H6. Other families need typed relationships, not blanket deduplication

PR #109093 explicitly names several overlapping OAuth issuer-relay proposals. That is a useful candidate set, not proof that every proposed implementation covers every callback route. Build a route-by-invariant coverage matrix before selecting a survivor. [PR109093]

PR #91293 describes #94878 as a previously selected composite survivor while retaining #91293 as a source/provenance carrier. It explicitly warns that its refreshed donor results do not certify the other head. Preserve that distinction in the graph. [PR91293]

The earlier #106742 review also exposes the difference between incorporated companion commits and remaining standalone-runtime gaps. A PR containing some absorbed commits can still contain useful unabsorbed work. [PR106742]

## Peer repository comparison

### OpenCode: quiet intake and aggressive queue cleanup

OpenCode's issue-open automation checks actionable content and searches existing issues. It combines compliance and possible-duplicate findings into one comment and otherwise stays silent. Its separate triage agent is restricted to a custom ownership-assignment tool; the prompt routes to a team and instructs it not to add labels. [O_DUPLICATES] [O_TRIAGE]

Its contribution guide requires an existing issue for a PR. This provides a stable problem identity before code is submitted. [O_ISSUE_FIRST]

The policies are substantially more aggressive than Hermes's current sweeper contract. The compliance system gives a two-hour correction window. A scheduled PR cleanup uses creation age greater than a month and fewer than two positive reactions, with a workflow batch cap of 50. These are workload-management rules, not verification of defect resolution. [O_COMPLIANCE] [O_CLOSE_PRS_WORKFLOW] [O_CLOSE_PRS]

The issue-cleanup script uses a 60-day inactivity cutoff, with author exemptions. Its implementation pages through a changing open-item collection while closing earlier results. The included synthetic model shows how 250 eligible records with 100-item pages can leave 100 unprocessed in one pass. This does not establish a particular production incident. [O_CLOSE_ISSUES]

The same script does not filter the `pull_request` marker in the inspected response-processing path. GitHub documents that its Issues endpoints can include PRs. That means the issue-cleanup path is not intrinsically issue-only and can overlap the separate PR policy. [O_CLOSE_ISSUES] [GH_ISSUES_API]

Adopt quiet, combined feedback and early problem identity. Do not import popularity-based resolution, prose-based guesses about AI authorship, or a two-hour deadline as a universal quality policy. Validate the deterministic scripts as carefully as the model prompt.

### Gemini CLI: turn a report into an executable work specification

The caretaker triage prompt sequences quality assessment, source exploration, effort estimation, and specification generation. It returns structured metadata plus a workable specification. The worker claims the issue in a persistent store, validates the returned JSON, and applies downstream actions through explicit egress helpers. [G_ORCHESTRATOR] [G_WORKER]

Its evaluation suite compares candidate specifications against golden specifications, including target files, root-cause accuracy, implementation plan, and testing strategy. This is a useful pattern for evaluating triage rather than trusting a model's self-reported confidence. A golden-spec match still does not prove the resulting program correct. [G_JUDGE]

Do not copy its feature-classification-to-auto-close behavior into Hermes without a maintainer policy decision. Hermes explicitly welcomes new capability at the edges. [G_WORKER] [H_POLICY]

### Goose: coordinate before implementation

Goose's contribution guide makes the issue the primary contribution record. It requires external implementation to wait until an issue is Ready, then requires scope alignment and verification against the issue's plan. It recognizes substantial work before the patch and discourages opening many PRs simultaneously. Urgent security and specified maintenance work have exemptions. [S_POLICY]

This is the strongest process idea to adapt: send additional agents toward missing evidence and integration work instead of another full implementation of an already-claimed fix.

## Proposed maintenance architecture

```text
GitHub events and periodic reconciliation
                  |
          durable event ingestion
                  |
      shared item / evidence / patch index
                  |
      candidate retrieval and typed links
                  |
   canonical problem + acceptance specification
                  |
    maintained implementation-admission policy
                  |
      existing contributor work and fix atoms
                  |
       disposable exact-tree verification
                  |
       trusted deterministic publication gate
                  |
     one updated coordination record on GitHub
```

A single shared index does not require a new graph database or another general-purpose scheduler. Prefer extending the existing sweeper where it runs. Keep this maintenance capability outside the core agent tool schema. GitHub remains the collaboration record; local analysis state is rebuildable except for explicitly retained receipts and human decisions.

### Four responsibilities

**Linker.** Retrieve related items using exact references, normalized errors, component signals, and lexical similarity. Add semantic retrieval only when evaluation shows incremental recall. Down-weight templates and bot boilerplate rather than allowing them to dominate matching. Include open and recently closed reports to detect regressions and already-landed fixes.

**Triage/reproduction worker.** Produce an acceptance specification with affected environment and expected behavior. Missing credentials, an unsupported OS, an unavailable dependency, or a flaky reproduction produces an explicit unresolved evidence state, not proof that the report is false.

**Campaign coordinator.** Keep one selected implementation effort per overlapping acceptance slice by default. A lightweight claim expires unless renewed with relevant progress. Alternative designs can be explicitly authorized; security work has an expedited path. Additional contributors can supply platform tests, counterexamples, benchmarks, or integration repairs. Claims allocate work; they do not confer merge authority or permanent ownership.

**Verification/publishing worker.** Assemble proposed donor commits in a disposable worktree, run trusted acceptance checks, and record the exact result. A separate policy-controlled publisher applies permitted labels and updates one stable comment. Closures and merges remain separately authorized actions.

### Relationship semantics

Use separate edge types for `candidate_related`, `same_root_cause`, `duplicate_of`, `overlaps`, `complements`, `depends_on`, `incorporates_commit`, `superseded_by`, `partially_addresses`, `verified_fixed_on`, and `regresses`.

Do not make a semantic-similarity connected component an equivalence class. A is similar to B and B to C does not establish that A and C describe the same defect. Preserve counterevidence and permit cluster splits.

Every actionable edge should retain source item revisions, relevant code SHA or path digest, evidence source, evidence level, and the human/policy decision permitting its use. A PR author's claim of a duplicate is a candidate relationship. A test passing on an unrelated donor is not an integration receipt.

### Minimal persistent model

Store `items`, `item_revisions`, `relations`, `campaigns`, `acceptance_criteria`, `patch_atoms`, `receipts`, `work_claims`, and `published_actions`. Index source text separately from bot-produced summaries. Store exact commits and source URLs rather than only untraceable prose.

Use event delivery identity for deduplication and expected item/head revisions for publication. Re-read the current item immediately before a mutation. A changed head invalidates affected evidence. An unrelated documentation-only change can reuse unaffected evidence if its dependency footprint was recorded.

### Permission boundary

Untrusted issue text, PR descriptions, comments, and candidate source must not control repository write credentials. Prompt delimiters help readability but are not a security boundary.

The model proposes a schema-validated decision. The publisher checks the current repository identity, allowed action, permitted labels, expected revision, evidence validity, and rate budget. No shell command from model output is executed by the publisher. Limit the publisher's token to the required repository and operations. Maintain an audit log, a kill switch, and an easy human correction route.

Run untrusted candidate tests in disposable, secret-free environments with restricted egress. Do not share privileged caches or production state. Fetch trusted verification policy from the pinned maintenance branch, not from the candidate's modified workflow files.

## Reuse plan

| Need | Reuse first | Constraint |
|---|---|---|
| Event orchestration and checks | Existing GitHub Actions and the existing sweeper | Avoid a parallel ownership system |
| Agent reasoning with bounded writes | GitHub Agentic Workflows architecture and safe outputs | Pin a patched release; review generated workflow and engine compatibility |
| Text search and relation storage | SQLite FTS5 plus ordinary relational tables | Start with a single writer; do not put a shared WAL database on unsupported network storage |
| Commit-equivalence candidates | Git patch IDs and ancestry analysis | Patch-ID equality is a hint, not proof; stable mode ignores whitespace |
| Acceptance execution | Existing Hermes per-file runner and JS test infrastructure | Compare baseline and candidate under the same environment and trusted policy |
| Later constrained selection | OR-Tools CP-SAT when the candidate graph justifies it | Optimize only over measured input; a solver cannot repair missing correctness evidence |

FTS5 provides full-text search and ranking. Git patch IDs are explicitly designed to locate likely duplicate commits. The whitespace caveat is especially relevant to Python and YAML. GitHub Agentic Workflows separates read-only agent jobs from validated write jobs, but its own documentation warns that safety still depends on configuration and supervision. [SQLITE_FTS5] [GIT_PATCH_ID] [GH_AW] [CP_SAT]

Hermes is not listed as a built-in engine in the inspected gh-aw README. Treat direct compatibility as an implementation question, not an existing integration. Keep deterministic Actions for deterministic checks. [GH_AW_README]

## Commit-selection objective

First enforce correctness and policy constraints. Then maximize distinct verified acceptance criteria resolved within a reviewer/compute budget. Use expected review effort and lifecycle cost as costs, not line count alone. Track performance against a fixed environment and workload; count an unavailable benchmark as unknown.

PR count reduction is a secondary accounting result. Otherwise the system is rewarded for creating redundant PRs and later closing them. Security/data-loss criteria must not be outweighed by a large number of cosmetic reports.

Use dependency-closed fix atoms. If a useful hunk sits inside a mixed commit, obtain an authored split or create an explicitly attributed integration change and validate it. Preserve semantic dependencies as well as Git ancestry. Test the assembled tree, not only each PR independently. Pairwise clean merges do not prove higher-order compatibility.

For the CI pilot, the proposed campaign is the invariant and useful non-overlapping work already represented by #103195. The narrow predicate in #98563 is useful provenance. Do not import #98684's unrelated pricing hunk. Do not import #108055's malformed YAML. The exact donor commit list remains unselected because the combined tree has not been built and tested.

## Rollout and acceptance gates

### M0: trustworthy verdicts

Reconcile the existing CI-verdict workstream. Gate and comment must agree about every known result. Cancelled/unknown/missing required checks cannot pass. Legitimate path-based skips remain valid. Verify subworkflow concurrency across separate main pushes. Report disabled E2E explicitly. Obtain CI-sensitive maintainer review on the exact candidate.

If a merge queue is introduced, wire the required workflows to `merge_group`; the inspected central Hermes workflow does not include that event. GitHub documents it as necessary for Actions checks used by merge queues. [H_CI] [GH_MERGE_QUEUE]

### M1: link-only operation

Backfill a paginated corpus, freezing candidate identities before any cleanup mutations. Record coverage and gaps. Evaluate retrieval against human-reviewed same-defect pairs and difficult nonduplicates, split by family and time to avoid future-information leakage. Publish no closures. Use one stable, editable summary per item, and no comment for an unremarkable event.

A useful initial evaluation sample is 200 human-reviewed pairs plus 50 historical resolution cases. These are proposed starting sizes, not completed measurements. Tune automation thresholds from measured precision and error costs, not an LLM confidence field.

### M2: coordinate active work

Add Ready/claimed/verification states with a low-friction exception route. Route new overlap to missing acceptance evidence. Distinguish waiting for contributor input from waiting for maintainer authorization, a native runner, or a dependency. Measure reviewer waiting time and duplicate implementation effort, not just the number of bot comments.

### M3: verified closure and integration assistance

Promote automated actions only after shadow-mode review. A verified-on-main closure must carry the landing commit and acceptance receipt. Duplicate consolidation must retain unique evidence and the canonical unresolved defect. Product rejection stays a human decision. A partly incorporated PR stays open or is split until its remaining work has an explicit disposition.

A user contesting an incorrect link should be able to request a relationship split without fighting repeated automatic reclosing. Bot-generated comments should not endlessly refresh inactivity clocks or retrigger new reviews of themselves.

## Measures of success

Keep separate dashboards for collaboration hygiene and product correctness. Track unique verified defect families resolved, false-link/false-closure corrections, escaped regressions, contributor waiting time, reviewer effort, wasted parallel implementations, and verification cost. Segment by platform and component so one popular area does not hide neglected low-volume bugs.

For a fixed backlog snapshot, every object should eventually have a defensible disposition. For the live repository, new work continues to arrive. A decreasing counter is useful only when unresolved defects and validation risk also decrease.

## Bundle contents

`scan_coverage.json` records what was and was not inspected. `campaign_seeds.json` contains hand-curated starting families with explicit evidence levels. `sources.json` preserves primary-source links. `offline_probes.py` reruns the isolated checks and rewrites `probe_results.json` and `probe_test_output.txt`.

Run the optional probes with Python 3.10+ and PyYAML installed:

```bash
python offline_probes.py
```

This package is an audit and implementation handoff, not an installed triage bot or a certified merge plan.

## Source references

[H_POLICY]: https://github.com/NousResearch/hermes-agent/blob/205645ee424163c7b6cfc032c331c3557797497b/AGENTS.md

[H_CI]: https://github.com/NousResearch/hermes-agent/blob/205645ee424163c7b6cfc032c331c3557797497b/.github/workflows/ci.yaml

[H_COMMENT]: https://github.com/NousResearch/hermes-agent/blob/205645ee424163c7b6cfc032c331c3557797497b/.github/workflows/ci-review-comment.yml

[H_LABEL]: https://github.com/NousResearch/hermes-agent/blob/205645ee424163c7b6cfc032c331c3557797497b/.github/workflows/review-labels.yml

[H_RERUN]: https://github.com/NousResearch/hermes-agent/blob/205645ee424163c7b6cfc032c331c3557797497b/.github/workflows/label-rerun.yml

[H_WORKFLOW_TREE]: https://api.github.com/repos/NousResearch/hermes-agent/git/trees/c2474998de03e4e12c8f1a6acff37531f8b4255a

[O_DUPLICATES]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/.github/workflows/duplicate-issues.yml

[O_TRIAGE]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/.opencode/agent/triage.md

[O_ISSUE_FIRST]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/CONTRIBUTING.md

[O_CLOSE_PRS_WORKFLOW]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/.github/workflows/close-prs.yml

[O_CLOSE_PRS]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/script/github/close-prs.ts

[O_CLOSE_ISSUES]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/script/github/close-issues.ts

[O_COMPLIANCE]: https://github.com/anomalyco/opencode/blob/95daf90670b7c039c436c85537da5fbfe2205b41/.github/workflows/compliance-close.yml

[G_ORCHESTRATOR]: https://github.com/google-gemini/gemini-cli/blob/9c1b0a610534d6f8120964cf2672c07807d8fc90/tools/caretaker-agent/cloudrun/triage-worker/.gemini/triage_orchestrator.md

[G_WORKER]: https://github.com/google-gemini/gemini-cli/blob/9c1b0a610534d6f8120964cf2672c07807d8fc90/tools/caretaker-agent/cloudrun/triage-worker/main.py

[G_JUDGE]: https://github.com/google-gemini/gemini-cli/blob/9c1b0a610534d6f8120964cf2672c07807d8fc90/tools/caretaker-agent/evals/triage/judge.md

[S_POLICY]: https://github.com/aaif-goose/goose/blob/50666ae0b9a51e260b52b7efbab2e4e020346e94/CONTRIBUTING.md

[GH_AW]: https://github.github.com/gh-aw/introduction/architecture/

[GH_AW_README]: https://github.com/github/gh-aw/blob/main/README.md

[GH_ISSUES_API]: https://docs.github.com/en/rest/issues/issues

[GH_MERGE_QUEUE]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue

[GIT_PATCH_ID]: https://git-scm.com/docs/git-patch-id

[SQLITE_FTS5]: https://www.sqlite.org/fts5.html

[CP_SAT]: https://developers.google.com/optimization/cp/cp_solver

[PR98563]: https://github.com/NousResearch/hermes-agent/pull/98563

[PR98684]: https://github.com/NousResearch/hermes-agent/pull/98684

[PR103195]: https://github.com/NousResearch/hermes-agent/pull/103195

[PR108055]: https://github.com/NousResearch/hermes-agent/pull/108055

[PR108055_SOURCE]: https://github.com/crazyief/hermes-agent/blob/c907c76a4fae8aaef29158ba8fb9041ccaade233/.github/workflows/ci.yaml

[PR109093]: https://github.com/NousResearch/hermes-agent/pull/109093

[PR91293]: https://github.com/NousResearch/hermes-agent/pull/91293

[PR106742]: https://github.com/NousResearch/hermes-agent/pull/106742
