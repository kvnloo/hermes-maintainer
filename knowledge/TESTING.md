# Running Hermes tests without hurting your own install

*Checked 2026-11-24 against `NousResearch/hermes-agent` main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0). Upstream wins if this page disagrees with it.*

## Use the runner, not bare pytest

Upstream says: always `scripts/run_tests.sh`, never bare `pytest`. ([AGENTS.md L146-L148](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L146-L148))

The runner ([scripts/run_tests.sh L1-L14](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/scripts/run_tests.sh#L1-L14)):

- runs each test file in its own `python -m pytest <file>` subprocess (no xdist)
- pins `TZ=UTC`, `LANG=C.UTF-8`, `PYTHONHASHSEED=0`
- blanks credential env vars

`just test <paths>` wraps it and refuses to start without a path. `just test-all` runs everything. ([CONTRIBUTING.md L274-L287](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/CONTRIBUTING.md#L274-L287)) `python scripts/check` runs every blocking lint CI runs, with CI's pinned tools. ([AGENTS.md L67-L69](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L67-L69))

## Isolated `HERMES_HOME` and the real-home guard

Tests never write to `~/.hermes/`. ([AGENTS.md L148](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L148)) `tests/conftest.py` enforces this before any test module is imported:

- If `HERMES_HOME` is unset or points at the production home, the session gets a throwaway temp home. Only a genuinely custom `HERMES_HOME` is honoured. ([conftest.py L86-L97](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/tests/conftest.py#L86-L97), [L161-L168](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/tests/conftest.py#L161-L168))
- It exists because importing `hermes_cli/main.py` attaches log handlers at import time. Without the early sandbox, test runs wrote into the operator's real `agent.log` and once landed fixture rows in a live `state.db`. ([L57-L71](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/tests/conftest.py#L57-L71))
- Temp dirs that resolve inside a guarded real home are stripped, so `tempfile` defaults can't trip the real-home tripwire. ([L150-L159](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/tests/conftest.py#L150-L159))

**Practical rule:** if your shell (or an agent's) exports `HERMES_HOME`, don't rely on that being safe. Use a disposable home for any manual dev instance. ([CONTRIBUTING.md L225](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/CONTRIBUTING.md#L225))

## Test shapes that get rejected

- Change-detector or source-reading tests (grepping the source for a string).
- Faking `sys.platform` to "prove" Windows or macOS behaviour. Use `@pytest.mark.platforms(...)` and run on that host. ([AGENTS.md L146-L148](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L146-L148))
- A fix without 1–2 invariant tests proven red on the base. ([L145](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L145))

Wanted instead: behaviour-contract tests and E2E with real imports against a temp `HERMES_HOME` for resolution, config, security and I/O changes. ([L37-L41](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L37-L41))

Next: [SECURITY_AND_CI.md](./SECURITY_AND_CI.md).
