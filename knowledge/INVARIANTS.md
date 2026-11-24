# The rules upstream reviews against

*Checked 2026-11-24 against `NousResearch/hermes-agent` main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0). Upstream wins if this page disagrees with it.*

Hermes's root [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md) is short and every line is load-bearing. These are the parts newcomers most often miss. Each links to the line at a pinned SHA.

## 1. Prompt caching is sacred

Mutating past context, swapping toolsets, reloading memories or rebuilding the system prompt mid-conversation breaks the cached prefix and multiplies the user's cost. Context compression is the one exception. A slash command that changes system-prompt state takes effect next session, with an opt-in `--now`. ([AGENTS.md L18-L21](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L18-L21))

Any change to the stock system prompt or `tools[]` fails `tests/ci/test_prompt_surface.py` until you commit the re-rendered snapshot, and that snapshot needs a `hermes-agent-core` approval. ([L26-L28](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L26-L28))

## 2. Narrow core, capability at the edges

Every model tool is sent on every API call, so a new core tool has a high bar. Take the highest rung that solves the problem ([L58-L61](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L58-L61)):

1. extend existing code
2. CLI command + skill
3. service-gated tool (`check_fn` answers reachability or opt-in, never per-session surface)
4. plugin
5. MCP server in the catalog
6. new core tool, only if fundamental, broadly useful and unreachable otherwise

Plugins use only the published plugin API; core never imports a bundled plugin. `scripts/boundary_lint.py` fails the suite on new crossings. ([L140-L142](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L140-L142))

## 3. Paths are profile-aware

Never hardcode `~/.hermes`. Use `get_hermes_home()` for paths and `display_hermes_home()` for text (lint rule HX001). ([L125-L126](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L125-L126))

One process serves many profiles. Code that runs outside a turn (boot probes, tickers, deferred callbacks, RPC methods, thread hops, child spawns) must bind the owning profile explicitly. `os.environ` and module globals hold the *launch* profile, so an unbound read silently leaks the default profile. ([L127-L131](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L127-L131))

Profiles are islands on purpose. Before calling isolation a bug, check intent with `git log -p -S "<symbol>"`. ([L50-L52](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L50-L52))

## 4. `config.yaml` for behaviour, `.env` for secrets

A new `HERMES_*` env var for non-secret config is rejected even when well built. Behaviour goes in `config.yaml`. ([L43-L44](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L43-L44), [L91-L92](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L91-L92)) A new config key or slash command ships with its docs, or `tests/ci/test_docs_drift.py` fails. ([L143](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L143))

## 5. Rejected even when well built

Hooks with no consumer; a core tool that terminal + file or a skill already covers; `offset`/`limit` pagination on instructional tools; "fixes" that destroy the feature they secure; telemetry without opt-in; change-detector tests; plugins that touch core files; third-party products in the core tree (ship a standalone plugin repo). ([L43-L48](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L43-L48))

## 6. Smaller rules that still fail CI

- Dependencies carry upper bounds. After editing `pyproject.toml`, run `hermes pm lock` and commit `uv.lock`. Don't mutate a Hermes environment with raw pip or uv. ([L133-L135](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L133-L135))
- Rebase onto `main` before merging. A squash from a stale branch silently reverts newer fixes. ([L144-L145](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L144-L145))
- New functions: CC ≤ 20, ≤ 300 lines; files ≤ 2,000 lines; units already over may only shrink. ([L108-L109](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L108-L109))
- Importing a module has no side effects except tool registration. ([L110-L111](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L110-L111))
- Each area has its own `AGENTS.md`. Read the nearest one before editing ([routing table](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L150-L171)).

Next: [TESTING.md](./TESTING.md).
