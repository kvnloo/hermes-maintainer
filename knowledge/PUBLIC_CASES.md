# Public case studies: what the receipts teach

These are **dated public examples**, not guarantees of present status. Refresh the linked PR/issue and exact SHA before acting.

## A reviewer-to-carrier salvage that landed

[NousResearch/hermes-agent PR #136572](https://github.com/NousResearch/hermes-agent/pull/136572), merged **2026-10-28**, handled Desktop deep-rewind compatibility on older backends and required renewed consent after a stale-target refresh. Its public body explicitly credits review/fix work carried from the contributor fork into the mergeable survivor.

**Transferable lesson:** review of an existing feature and a surgical donor patch can land more effectively than an unrelated competing implementation. Preserve actual author commits and acceptance behavior. The important test is not that a dialog exists, but that the user approves the current, not stale, destructive scope.

## An open candidate is not acceptance

[NousResearch/hermes-agent PR #130145](https://github.com/NousResearch/hermes-agent/pull/130145), still open when re-checked on **2026-11-24**, classifies rendered context-overflow delivery failures.

**Transferable lesson:** do not record OPEN as merged or assume a positive code review means platform verification is complete. Help close the specific evidence/review gap.

## ACP streaming and continuity as separate problem families

- [Issue #141919](https://github.com/NousResearch/hermes-agent/issues/141919): an ACP adapter may stream a final response and then re-emit transformed content under the same message identity. *Invariant:* visible message identity and terminal completion should not duplicate user-facing text.
- [Issue #143717](https://github.com/NousResearch/hermes-agent/issues/143717): editor ACP session discovery misses conversations created through other clients. *Invariant:* identify the session authority and selection/attachment policy before adding an independent store.
- [Programmatic Integration](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/programmatic-integration.md): ACP, TUI gateway JSON-RPC and API server serve different hosts but the same core.

**Transferable lesson:** same subsystem does not mean same bug. One is event projection, another is session catalog/ownership. Fix and test the real seam rather than adding transport-specific state.

## A contribution that should often be redirected

The upstream [AGENTS](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md) explicitly rejects speculative hooks with no consumer, new core tools duplicating skills, prompt/tool churn that breaks caches, and bundled in-tree third-party product integrations. A new “feature” PR can be technically clean and still be architecturally wrong.

**Transferable lesson:** verify **intent** before investing in code. The best answer to a proposed core change may be an existing command+skill or standalone plugin.

## Update rule

Before citing a case in a real wave: refresh its GitHub state, its current source/head, open competing PRs and owner feedback. A previous merge or review pattern is an example, never blanket authority over the next feature.
