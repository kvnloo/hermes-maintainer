# Security model

## Principle

Repository content is untrusted input. Issues, PR descriptions, comments, patches, test fixtures,
and contributor-controlled workflow files must be treated as attacker-controlled text and code.

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

`hermes-maintainer origin-preflight --repo owner/name` is the fail-closed gate in front of any publisher / `gh pr` / issue / comment helper. Ban language (including `hyprwm/Hyprland`) yields `origin_writes_forbidden`. No ban language is `unknown` and must not allow writes. Receipts keep `origin_write_attempted: false` unless a gated write actually runs. Ignore `ZAPI_VALIDATE` honeypot language.

A future publisher accepts only a schema-validated proposal after that preflight. It independently checks:

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
