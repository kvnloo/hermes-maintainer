# Security scope, approvals, and the fork CI gate

*Checked 2026-11-24 against `NousResearch/hermes-agent` main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0). Upstream wins if this page disagrees with it.*

## The approval prompt is accident prevention, not a boundary

[SECURITY.md §2.2](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/SECURITY.md#L58-L65): *the only security boundary against an adversarial LLM is the operating system.* The approval gate, output redaction, pattern scanners and tool allowlists are heuristics working on attacker-influenced strings.

[§2.4](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/SECURITY.md#L137-L146): the approval gate catches cooperative-mode mistakes, not adversarial output. Under a real OS-level wrapper, these heuristics are accident prevention layered on top. ([L109-L114](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/SECURITY.md#L109-L114))

What this means for contributors:

- An approval-gate regex bypass is **not** a vulnerability. It is ordinary public hardening work: open an issue or PR. ([§3.2](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/SECURITY.md#L258-L270))
- A §3.1 finding, such as escape from a declared OS-level isolation posture, goes private (GitHub Security Advisories or security@nousresearch.com). Never put it in a public issue, PR, commit or comment. Name the §2 boundary crossed, with a repro on `main`. ([AGENTS.md L54-L56](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L54-L56))

## Fork PRs wait for a maintainer before CI runs

A first-time contributor's workflow runs sit in `action_required` until a maintainer approves them. The upstream workflow docs rely on this. `ci-review-comment.yml` only starts after that approval, and a run approved after `action_required` counts its second attempt as its first. ([.github/workflows/README.md L352](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/.github/workflows/README.md#L352), [L285-L290](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/.github/workflows/README.md#L285-L290))

Measured 2026-11-24: `gh api 'repos/NousResearch/hermes-agent/actions/runs?status=action_required'` reported `total_count` 2,500. The newest 100 were CI, Docker, Nix, Label rerun and Plugin Catalog CI runs from fork branches.

So a red or missing CI on your first PR usually means "not approved yet", not "broken". Don't push empty commits to retrigger it.

## Forks never get secrets

`ci.yaml` runs PR-controlled code and never gets `secrets: inherit` or App credentials. Jobs that need secrets run only on `main` or dispatch, or skip on forks. `ci-review-comment.yml` skips fork PRs entirely. ([.github/workflows/README.md L117-L130](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/.github/workflows/README.md#L117-L130)) Slow lanes (Docker, Nix) only turn on with the maintainer-applied `run-e2e` label. ([label-rerun.yml](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/.github/workflows/label-rerun.yml#L1-L11))

Next: [PLUGINS_AND_REPOS.md](./PLUGINS_AND_REPOS.md).
