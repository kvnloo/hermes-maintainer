# Public Hermes work radar — dated, sourced signals

*Snapshot: 2026-11-24, upstream `NousResearch/hermes-agent` main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0). First compiled 2026-11-18 at `f7e2898`; every issue below was re-checked OPEN on 2026-11-24 with `gh api graphql`. Refresh before proposing a fix.*

**Board size on 2026-11-24:** 19,810 open issues and 34,392 open PRs (`gh api graphql`, `repository.issues(states:OPEN).totalCount` / `pullRequests(states:OPEN).totalCount`). With 4,229 merges a month ([WHO_MAINTAINS_WHAT.md](./WHO_MAINTAINS_WHAT.md)), most open PRs will never be reviewed as-is. Adding evidence to an existing PR usually beats opening a competing one.

**This is not the team's private roadmap.** Public issue reports and proposals are evidence of community demand, not evidence that NousResearch has committed to build, prioritize or merge them. Read maintainer comments and live PR competition before interpreting an issue.

## ACP and multi-surface conversation continuity

These are related but **not interchangeable** bugs:

| Public issue (open on 2026-11-24) | Primary question / evidence seam |
| --- | --- |
| [#156777 Windows ACP session/new hang](https://github.com/NousResearch/hermes-agent/issues/156777) | Did a subprocess/version check inherit ACP's stdin reader? Verify on native Windows, not a `sys.platform` patch |
| [#156173 ACP viewer exit leaves turn running](https://github.com/NousResearch/hermes-agent/issues/156173) | Who owns the admitted turn when viewer process disconnects? How is it safely resumed/cancelled? |
| [#141919 duplicate transformed final stream](https://github.com/NousResearch/hermes-agent/issues/141919) | Preserve message identity and single visible terminal reply across transform and streaming |
| [#149922 Desktop→ACP session live rendering](https://github.com/NousResearch/hermes-agent/issues/149922) | Broadcast events to all attached viewers rather than delivery only to the submitting client |
| [#143717 ACP catalog includes gateway sessions](https://github.com/NousResearch/hermes-agent/issues/143717) | Separate session lookup/permission from persistent transcript ownership |
| [#146721 ACP session/list omits source-local ACP sessions](https://github.com/NousResearch/hermes-agent/issues/146721) | How are session source labels normalized and which do editors enumerate? |
| [#157176 image-part support in ACP provider clients](https://github.com/NousResearch/hermes-agent/issues/157176) | Capability negotiation, multipart forwarding, and wire test coverage |
| [#137069 ACP subagent updates](https://github.com/NousResearch/hermes-agent/issues/137069) | Delegation event projection, independent of actual subagent execution |
| [#127870 ACP /retry /undo /title](https://github.com/NousResearch/hermes-agent/issues/127870) | Does command routing preserve the gateway's canonical session semantics? |
| [#147987 include clarify in ACP toolset](https://github.com/NousResearch/hermes-agent/issues/147987) | Existing toolset policy and editor UX for human clarification |

**Start with** [ACP internals](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/acp-internals.md), `acp_adapter/gateway_server.py`, `gateway/session_acp_lifecycle.py`, and relevant `tests/acp_adapter/`. Do not create a parallel owner or call an open proposal an approved design.

## Reliability, learning, and developer experience

- [#147010 spool recovery ordering](https://github.com/NousResearch/hermes-agent/issues/147010) (open): user data ordering/consistency matters even when a retry eventually succeeds. Reproduce queue head failure and inspect sibling recovery paths.
- [#137961 malformed config root accepted as empty](https://github.com/NousResearch/hermes-agent/issues/137961) (open): config validation should fail visibly rather than quietly discard user intent.
- [#136931 skill self-improvement regressing good workflows](https://github.com/NousResearch/hermes-agent/issues/136931) (open): durable learning vs temporary workaround or task-local instruction deserves a behaviorally testable boundary.
- [#99773 TUI attention budget and first paint](https://github.com/NousResearch/hermes-agent/issues/99773) (open): an observable UX experiment, not permission to redesign the entire UI.
- [#118010 first-class device nodes](https://github.com/NousResearch/hermes-agent/issues/118010) (open): a contributor proposal for mobile/device integration, not an announced shipping timeline.

## Historical public direction, not live promises

Several broad "Roadmap:" tracking issues were **closed** by May 2026, including [durable workflows #35916](https://github.com/NousResearch/hermes-agent/issues/35916), [plugin apps #35917](https://github.com/NousResearch/hermes-agent/issues/35917), [gateway platforms #35918](https://github.com/NousResearch/hermes-agent/issues/35918), [evals #35919](https://github.com/NousResearch/hermes-agent/issues/35919) and [memory governance #35920](https://github.com/NousResearch/hermes-agent/issues/35920). Their historical scope is useful context; closure alone proves neither delivery nor current intent.

For **documented** priorities, use [CONTRIBUTING.md](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md): correctness, cross-platform compatibility, security, robustness, then targeted extensions. For **documented** goals, use the current [README](https://github.com/NousResearch/hermes-agent/blob/main/README.md): a flexible self-improving assistant with skills, memory, broad models and deployment surfaces.

## How to refresh the radar before making a recommendation

1. Re-fetch current upstream main SHA and the area AGENTS.md.
2. Search current issues and **all-state PRs** (open, draft, merged, closed), plus owner reviews and relevant commits.
3. Confirm the observed behavior still exists on main; issue OPEN does not prove broken code.
4. Record one linked receipt with `checked_at`, target issue/PR, base SHA, own tested head, competing fix authors and next human gate.
5. Update this guide only with public links and status-at-time, and clearly label inferences. Do not expose private team notes, user memory or unreleased plans.
