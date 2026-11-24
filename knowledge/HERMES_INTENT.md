# Hermes architecture and publicly observable direction

**Checked 2026-11-24 against NousResearch/hermes-agent main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0).** This is a date-stamped guide, not a promise about future releases. Upstream AGENTS.md and CONTRIBUTING.md are authoritative.

## Public mission (documented, not inferred)

The upstream [README](https://github.com/NousResearch/hermes-agent/blob/main/README.md) describes a self-improving personal agent with memory and skills that can run with different providers, on low-cost or local infrastructure, through CLI, TUI, desktop, messaging, and gateway surfaces. It emphasizes deployment flexibility and the learning loop.

The upstream [development guide](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L16-L24) names two invariants that shape almost every review: **per-conversation prompt caching is sacred**, and **the core is a narrow waist with capability at the edges**. See [INVARIANTS.md](./INVARIANTS.md) for both, plus the footprint ladder, profile-aware paths and the `config.yaml` vs `.env` rule, each with line links.

## Who owns what (source routing)

| Symptom / feature | Start looking |
| --- | --- |
| Tool call / step completion / compression / message persistence | agent/, run_agent.py, persistence/, agent/AGENTS.md |
| Slash commands / provider setup / profiles | hermes_cli/, cli.py, hermes_cli/AGENTS.md |
| Messaging or streaming adapter / token locks / profile isolation | gateway/, gateway/AGENTS.md |
| Tool schemas / registry / delegation | tools/, toolsets.py, tools/AGENTS.md |
| Plugins / memory providers | plugins/, plugins/AGENTS.md, plugin API; not arbitrary core edits |
| TUI, gateway RPC, sessions | tui_gateway/, ui-tui/, tui_gateway/AGENTS.md |
| Desktop UX / sessions / models | apps/desktop/, both desktop AGENTS files |
| ACP editor/host sessions | acp_adapter/, ACP Internals docs |
| CI, platforms and acceptance | tests/, scripts/, tests/AGENTS.md |

Root [AGENTS.md routing table](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L150-L171) routes each area. Read the *nearest* AGENTS file at the **current head**, not an old snippet.

## Cross-cutting invariants newcomers miss

- A gateway can multiplex profiles. Background callbacks, subprocesses, boot probes and RPC paths must bind the correct profile explicitly; the process environment is not automatically the session's profile.
- An ACP viewer is not a second independent conversation authority. Current ACP startup projects through a profile gateway; session ownership, durable history and admission policy live there. Do not duplicate the owner in a frontend bridge.
- Model aliases and custom endpoints resolve with specific provider identity. Do not preserve credentials/base URLs while switching providers without proof they still belong together.
- Error handling must cover *all transports* at the ownership boundary: REST-only fixes miss SSE, WebSocket and gateway paths.
- Security “fixes” that remove an intended feature, break profile boundaries, or swallow a failure without surfacing it are not acceptable fixes.

These are starting hypotheses to verify per issue. They are **not** proof any particular bug exists.

## Public direction and how to read it responsibly

**Confirmed, documented:** cross-platform compatibility, correctness, security, performance/robustness and broadly useful skills are prioritized in [CONTRIBUTING](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md). Extensibility via skills/plugins and shared agent core are in current documentation.

**Public issue-level proposals, not a team commitment:**
- [#143717 ACP discovery of gateway conversations](https://github.com/NousResearch/hermes-agent/issues/143717) (open on 2026-11-24).
- [#141919 duplicated ACP transformed final response](https://github.com/NousResearch/hermes-agent/issues/141919) (open on 2026-11-24).
- [#157176 ACP image parts in provider clients](https://github.com/NousResearch/hermes-agent/issues/157176) (open on 2026-11-24).
- [Historical roadmap proposal #35917 for plugins-as-apps](https://github.com/NousResearch/hermes-agent/issues/35917) (closed, not an active task list).

For a broader *dated* issue radar see [CURRENT_PUBLIC_WORK.md](./CURRENT_PUBLIC_WORK.md). Do **not** infer team priorities, upcoming releases or maintainer approvals solely from issue volume, a proposal's title, or the fact it was closed. Refresh live source/threads on every wave; link your snapshot and revision.
