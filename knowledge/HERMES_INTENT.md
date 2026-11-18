# Hermes architecture and publicly observable direction

**Checked 2026-11-18 against NousResearch/hermes-agent main f7e2898aaefc8f967dbf7345e3999a65672fe60e.** This is a date-stamped guide, not a promise about future releases. Upstream AGENTS.md and CONTRIBUTING.md are authoritative.

## Public mission (documented, not inferred)

The upstream [README](https://github.com/NousResearch/hermes-agent/blob/main/README.md) describes a self-improving personal agent with memory and skills that can run with different providers, on low-cost or local infrastructure, through CLI, TUI, desktop, messaging, and gateway surfaces. It emphasizes deployment flexibility and the learning loop.

The upstream [development guide](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md) makes two architecture constraints explicit:

1. **Per-conversation prompt-cache preservation.** A stable tool list and system-prompt prefix matter; new skills and state should not silently mutate a running conversation. Compression is a deliberate exception. For any mid-session config change, check whether it applies only to the next session or needs an explicit --now path.
2. **Narrow agent core; broad edges.** Put integration-specific capabilities into an existing API, CLI command+skill, service-gated tool or plugin. A new core tool has a high review bar because every tool costs context on every API call. Follow the footprint ladder in AGENTS.md.

Both are intended architectural rules, not just our preferences. Changing the prompt/tool surface triggers a snapshot and core-owner review. Read the current tests and policy before touching either.

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

Root [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md) routes each area. Read the *nearest* AGENTS file at the **current head**, not an old snippet.

## Cross-cutting invariants newcomers miss

- A gateway can multiplex profiles. Background callbacks, subprocesses, boot probes and RPC paths must bind the correct profile explicitly; the process environment is not automatically the session's profile.
- An ACP viewer is not a second independent conversation authority. Current ACP startup projects through a profile gateway; session ownership, durable history and admission policy live there. Do not duplicate the owner in a frontend bridge.
- Model aliases and custom endpoints resolve with specific provider identity. Do not preserve credentials/base URLs while switching providers without proof they still belong together.
- Error handling must cover *all transports* at the ownership boundary: REST-only fixes miss SSE, WebSocket and gateway paths.
- Security “fixes” that remove an intended feature, break profile boundaries, or swallow a failure without surfacing it are not acceptable fixes.
- Configuration behavior belongs in config.yaml, while .env is for secrets; Hermes paths are profile-aware, not hardcoded to ~/.hermes.
- New internal module layout follows a facade and topic modules; importing a module must not trigger unrequested I/O or environment changes.

These are starting hypotheses to verify per issue. They are **not** proof any particular bug exists.

## Public direction and how to read it responsibly

**Confirmed, documented:** cross-platform compatibility, correctness, security, performance/robustness and broadly useful skills are prioritized in [CONTRIBUTING](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md). Extensibility via skills/plugins and shared agent core are in current documentation.

**Public issue-level proposals, not a team commitment:**
- [#143717 ACP discovery of gateway conversations](https://github.com/NousResearch/hermes-agent/issues/143717) (open when checked).
- [#141919 duplicated ACP transformed final response](https://github.com/NousResearch/hermes-agent/issues/141919) (open when checked).
- [#157176 ACP image parts in provider clients](https://github.com/NousResearch/hermes-agent/issues/157176) (state must be rechecked).
- [Historical roadmap proposal #35917 for plugins-as-apps](https://github.com/NousResearch/hermes-agent/issues/35917) (closed, not an active task list).

For a broader *dated* issue radar see [CURRENT_PUBLIC_WORK.md](./CURRENT_PUBLIC_WORK.md). Do **not** infer team priorities, upcoming releases or maintainer approvals solely from issue volume, a proposal's title, or the fact it was closed. Refresh live source/threads on every wave; link your snapshot and revision.
