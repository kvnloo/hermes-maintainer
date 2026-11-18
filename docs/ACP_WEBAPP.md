# Hermes ACP web client: setup, protocol and safety

**Status:** local single-user MVP, not a hosted contribution service. **Checked against** [Hermes ACP internals](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/acp-internals.md) and [programmatic integration](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/programmatic-integration.md) at upstream `f7e2898aaefc8f967dbf7345e3999a65672fe60e` on 2026-11-18.

## Product

`/` is a calm search-bar UI: send a question, and a **new ACP session** starts on the local Hermes profile. Three instructions modes: **Learn** (architecture), **Triage** (issues/PRs and root cause), **Contribute** (guide a verified patch in an authorized fork). Subsequent messages remain in the same session. `New conversation` closes the viewer subprocess and starts fresh. The background SQLite issue/PR graph remains at `/board` and `/graph`.

In the public GitHub Pages static build, the same UI searches reviewed markdown guides. **It cannot create conversations, run code or publish PRs.** The graph there is a dated seed demo, not live metrics.

## Architecture

```text
browser (same-origin local)
    -> FastAPI /api/chat, /events, /permission
    -> one subprocess "hermes acp" per new conversation
    -> ACP JSON-RPC 2.0 stdio (initialize -> session/new -> session/prompt)
    -> Hermes gateway session authority and existing AIAgent core
    <- session/update chunks and tool progress
    <- session/request_permission -> show Allow once / Deny -> ACP response
```

`src/hermes_maintainer/acp_bridge.py` handles the transport, framing, sequential request IDs, bounded event ring, prompt turns, cancellation, and permission requests. `src/hermes_maintainer/api/chat.py` handles request bounds and local client gate. `ui/static/chat.{html,js,css}` renders text safely (no HTML execution of agent content). Hermes' own ACP session mode defaults to `ask`; the bridge declines an ACP session that advertises a different current edit mode.

**What this bridge is not:** a reverse proxy to the Hermes REST API, an emulated ACP agent, a multi-tenant execution sandbox, a GitHub write publisher, or a connection that inherits the maintainer graph's read-only privilege.

## Run locally

1. Install Hermes normally and configure a provider with `hermes model`.
2. Enable ACP using the [official host integration setup](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/acp.md), then run `hermes acp --check`.
3. Clone a fork you are authorized to modify into a dedicated workspace; do not point the bridge at an upstream clone with push credentials.
4. Install the maintainer project dependencies: `python -m venv .venv; source .venv/bin/activate; pip install -e '.[dev]'`.
5. From the maintainer project root, run:

```bash
export HERMES_MAINTAINER_ACP_ENABLED=1
export HERMES_MAINTAINER_ACP_WORKSPACE="$HOME/src/hermes-agent-fork"
hermes-maintainer serve --host 127.0.0.1
```

Browse `http://127.0.0.1:8766/`; modes only change before starting a new chat. No extra inference credentials go into this project. The bridge uses the user's existing Hermes profile and configuration.

## Security and authorization model

**Do not expose this server to the internet.** A localhost gate and one-time ACP permission UI are **not** authorization for stranger-provided prompts, arbitrary file access or tool side effects. Any local user/process able to connect can submit prompts. Treat the service as trusted-single-user tooling.

- The bridge is disabled by default. The host validates loopback clients, a custom local-UI header and same-origin browser requests. Cross-site requests are rejected on Origin, but an untrusted local program could set headers itself.
- ACP clients may request permission for certain dangerous operations. The UI offers only `allow_once` and `deny` and cancels if unanswered. Other ACP client RPC methods are refused. **Other Hermes tool calls may be executable without this explicit approval**; the workspace and Hermes profile permissions matter most.
- Use a dedicated OS account/container with restricted filesystem, processes, egress and toolset for untrusted investigations. Never mount your personal secrets, GitHub PAT or open-source contributors' private information into it.
- Prefer fork-only coding, scoped Draft PRs and human review. No default-branch push, upstream issue/PR/comment writes or merge without explicit authenticated authority. A prompt cannot enforce these rights; OS and Git permissions must.
- No private factory notes, personal memory, or unpublished team plans go in public knowledge. Source verification is mandatory.
- No session store or token storage is added here; Hermes itself may persist sessions according to its existing profile. The bridge stores transient events in process memory (max 600) and closes subprocesses when chats are deleted or the web server exits.
- Requests are bounded (8k characters), server keeps at most four active processes, approval times out to deny; the bridge is nevertheless not hardened to prevent all denial-of-service or local threat vectors.

## Future production path (not implemented)

For a safe **public multi-user** webapp: authentication and per-user identity, tenancy isolation, ephemeral sandbox per session, read-only default, provenance and session citations, worktree/repo allowlists, GitHub App permissions narrowly scoped to a user's fork, branch/head leases, explicit approvals for each write and reviewer gates, audit logging, rate limits and budget controls, adversarial prompt injection tests, live-source indexing and background freshness checks. Never give an anonymously accessible page an ACP host with shell permissions.

## Protocol compatibility and tests

The bridge targets the Hermes ACP subset: initialize, session/new, session/prompt, session/update, session/request_permission and session/cancel. Hermes ACP is versioned separately; check [ACP Internals](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/acp-internals.md) and the actual current Hermes binaries when upgrading. Run `python -m pytest -q` and `ruff check .` in this project, then a local integration smoke test with a configured Hermes ACP provider. A mock ACP subprocess unit test is provided; it does not prove credentials or model inference on a real Hermes install.

## Why not build an LLM into FastAPI?

Hermes already owns the provider, context window, cached prefix, memory, tools, approvals and session state. Duplicating that in a web app would break the very invariants this project teaches. ACP reuses the existing agent.
