# Security model

## Principle

Repository content is untrusted input. Issues, PR descriptions, comments, patches, test fixtures,
and contributor-controlled workflow files must be treated as attacker-controlled text and code.

## New: optional local Hermes ACP session bridge

The read-only graph and public website remain unchanged in their authority. A separate **opt-in** bridge spawns `hermes acp` locally for a trusted user's conversations. The application itself has no GitHub write endpoint, token publisher or merge function, but Hermes' existing tools (terminal, code execution, file edits, plugins and Git credentials) may still be capable of side effects. Prompts, ACP permission dialogs, local-only HTTP checks and its session's default “ask” edit mode **do not form a sandbox**.

Use a dedicated least-privileged OS account and disposable authorized fork checkout for code-writing sessions; configure Hermes toolsets to exclude tools/credentials not intended for the use case. Do not expose the ACP-enabled server publicly, tunnel it or add a reverse proxy without a proper authenticated, isolated service design and threat-model review. A real public hosted version needs per-user identity, workspace/container isolation, scopes, egress policy, auditing, quotas and explicit per-action authorization before enabling contributes.

Browser routes restrict private chat to loopback clients, require an opt-in request header, and reject foreign Origin values. That is a local accidental-exposure mitigation, **not** a defense against malware or untrusted local processes. Responses are no-store; no chat transcripts are written to the graph by this bridge. Hermes may itself persist its own sessions depending on its configuration.

## Trust zones

### Zone 1: untrusted analysis

Can read:

- GitHub issue/PR metadata;
- cloned repository content;
- contributor patches;
- public CI metadata.

Cannot:

- use a GitHub write token;
- access production secrets;
- run contributor code on a privileged host;
- execute shell commands emitted by an LLM.

### Zone 2: isolated verification

May execute a pinned candidate tree in an ephemeral environment with:

- no repository write token;
- no production credentials;
- restricted outbound network;
- explicit resource/time limits;
- fresh caches or carefully scoped read-only caches.

### Zone 3: publisher

Not implemented in v0.1.

A future publisher accepts only a schema-validated proposal. It independently checks:

- expected repository identity;
- expected target SHA/revision;
- allowed mutation type;
- evidence freshness;
- label/comment allowlists;
- maintainer authorization where required;
- rate budget and kill switch.

The publisher must never execute arbitrary command text from a model response.

## Token strategy

Scanning uses a read-only fine-grained GitHub token where possible. A future write integration
should use a separate token/app installation and a different process boundary.

## Prompt injection

Prompt delimiters and instructions are not a security boundary. Model output is a proposal only.
Deterministic code must decide what data is fetched, what tests are run, and what mutations are
allowed.
