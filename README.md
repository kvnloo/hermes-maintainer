# hermes-maintainer

**A contributor knowledge base and chat-first Hermes ACP companion.** Learn the source, triage a problem family, or prepare a reviewable contribution without needing somebody else's private memory.

- [Start here](knowledge/START_HERE.md) — newcomer path.
- [Hermes architecture and public intent](knowledge/HERMES_INTENT.md) — invariants and subsystem entry points.
- [Run a triage wave](knowledge/TRIAGE_WAVES.md) — live research, overlap, exact-head receipts and disposition.
- [Review evidence](knowledge/REVIEW_EVIDENCE.md) — red→green tests, native platforms, author credit.
- [Public cases](knowledge/PUBLIC_CASES.md) — historical real examples.
- [Current public work radar](knowledge/CURRENT_PUBLIC_WORK.md) — dated open reports, continuity themes, and historical proposals; **not** an official roadmap.
- [Source / freshness / privacy rules](knowledge/SOURCE_POLICY.md) — authoritative vs inferred.

The home page at `http://127.0.0.1:8766/` is now a single conversation search bar with **Learn, Triage, Contribute** modes. The prior backlog dashboard and xyflow graph remain available at `/board` and `/graph`. In a static GitHub Pages deployment, the same search bar discovers *public guides*; it does not instantiate a privileged model or claim to execute commands.

`hermes-maintainer` is a local-first maintenance intelligence system for
`NousResearch/hermes-agent`.

Its goal is not to create more review comments. Its goal is to continuously turn the live
repository into a durable **backlog graph** that answers:

- Which issues and PRs describe the same underlying problem?
- Which PRs are survivors, donors, superseded implementations, or stacked children?
- Which minimal commit or fix-atom set closes the most verified acceptance criteria?
- Which recurring bug classes indicate missing shared primitives in Hermes itself?
- Where is maintainer attention actually blocked: reproduction, integration, permissions,
  platform evidence, CI, or product policy?

The system is designed around frequent batched scans, a local git mirror, a GitHub metadata
snapshot, SQLite/FTS5 analytics, typed graph edges, campaign construction, evidence tracking,
and an optional optimization layer.

## Principles

1. **Problem families, not issue counts.** An issue is an observation. A PR is a candidate
   implementation. Neither is the unit of truth.
2. **Fix atoms, not whole PRs.** Stacked PRs and salvage PRs must not be double-counted.
3. **Evidence before closure.** `duplicate_of`, `same_root_cause`, `partially_addresses`, and
   `verified_fixed_on` are different relationships.
4. **Read-only reasoning, restricted writes.** The MVP has no GitHub mutation path.
5. **Deterministic core first.** Git, SQLite, FTS5, and explicit relations are the source of
   truth. Embeddings and solver support are optional accelerators.
6. **Optimize integration, not output volume.** The system should redirect agents toward
   missing evidence and integration work rather than generate another implementation.

## Live chat with Hermes over ACP (local, opt-in)

Hermes itself is the language model, tool runtime and session owner, **not** a new agent implemented in this project. The Python web server acts as a local ACP stdio client using `hermes acp` and creates a fresh ACP session when you submit a new chat. The interface displays streaming messages and asks for **one-time** approval when Hermes requests a dangerous action.

Prerequisites: install and configure Hermes, enable its ACP optional package through the [official ACP setup instructions](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/acp.md), and check `hermes acp --check`. Choose the least-privileged working directory (ideally an expendable authorized fork clone).

```bash
# In the hermes-maintainer checkout, after pip install -e '.[dev]'
export HERMES_MAINTAINER_ACP_ENABLED=1
export HERMES_MAINTAINER_ACP_WORKSPACE="$HOME/src/hermes-agent-fork"
# Optional: export HERMES_MAINTAINER_ACP_COMMAND="hermes acp"
hermes-maintainer serve
# Visit http://127.0.0.1:8766/
```

**Security:** This is a **trusted single-user local interface**, not a public multi-tenant service or a hardened execution sandbox. ACP may expose terminal, code execution, plugins and Git credentials available on the Hermes host. Never bind it to a public interface, reverse-proxy it for strangers, or expose it without real identity/authorization and process isolation. A guide prompt and approval UI are **not a security barrier**; configure Hermes toolsets and OS/Git credentials accordingly. Only work on a downstream fork with explicit authorization; no default branch pushes or upstream writes. See [ACP security and limits](docs/ACP_WEBAPP.md).

`HERMES_MAINTAINER_ACP_ENABLED` defaults off; the repo's own GitHub graph/analytics API remains read-only. The local bridge does **not** publish GitHub mutations; a user with separately authorized Hermes tools may elect to write in their own fork after deliberate approval.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# export GITHUB_TOKEN=...  # recommended but optional for public low-volume scans

hermes-maintainer init
hermes-maintainer scan --mode fast
hermes-maintainer analyze
hermes-maintainer serve
```

Open `http://127.0.0.1:8766/` for guide search, or `/graph` for the existing Hermes Teal xyflow dashboard. Agents can start from [`llms.txt`](./llms.txt) or the served `/llms.txt`.

Public snapshot (GitHub Pages): https://kvnloo.github.io/hermes-maintainer/ (static public guide search at root, graph demo at `graph.html`, and `llms.txt`). ACP requires a locally installed and enabled Hermes process and is **not** available on GitHub Pages. The live graph still needs a local scan.

For continuous operation:

```bash
hermes-maintainer daemon
```

The daemon keeps the local git mirror fresh, runs fast metadata scans frequently, performs
deeper PR enrichment less often, rebuilds relations and campaigns, and updates health metrics.

## Maintainer permissions

`hermes-maintainer` is **not** an official NousResearch account, maintainer, or upstream publisher. Current repository-scoped authorization must be checked for every action; fork write access is not upstream write access. Historical backlog counts in seed audits must never be presented as live counts. See `BACKLOG-CLOSE.md` for a dated triage case, not a standing authority to mass-close tickets. Newcomer success means verified accepted work, not shrinking an issue counter by force.

## Project map

```text
src/hermes_maintainer/
  github/       GitHub REST ingestion and normalization
  git/          mirror/fetch, ancestry, patch-id helpers
  graph/        SQLite-backed typed backlog graph
  analysis/     similarity, campaigns, evidence, root-cause mining
  optimizer/    greedy baseline and optional CP-SAT selection
  scheduler/    frequent batched scan loop
  api/          local FastAPI UI/API, graph and ACP conversation bridge
  acp_bridge.py local Hermes ACP stdio JSON-RPC session transport
  ui/           chat-first interface + Hermes-themed xyflow graph
  agents/       prompts and agent work contracts

knowledge/      public onboarding, architecture, wave, evidence and cases
docs/           PRD, architecture, security, operations, ACP integration, schemas
tasks/          parallel Codex/Cursor work packets
seed/audit/     the prior Hermes repository coordination audit and seed campaigns
llms.txt        agent-oriented map of this repository
BACKLOG-CLOSE.md  kvnloo close-table play for #109552 (label audit; 403 on close)
```

## MVP status

The scaffold is intentionally useful before any model is connected. It can:

- mirror/fetch the repository;
- ingest GitHub issues and PRs;
- parse explicit relationships such as `fixes`, `closes`, `supersedes`, and `related`;
- build lexical similarity candidates;
- persist typed graph edges;
- form connected campaign candidates;
- compute repository dynamics and backlog health;
- derive PR-level fix atoms;
- produce a greedy merge-set candidate;
- expose all of this through a local API and dashboard, including an xyflow
  campaign graph with survivor/donor/provenance roles and typed-edge filters.

The roadmap then adds commit-level extraction, embeddings, code-overlap analysis, test-evidence
receipts, campaign-specific agent workers, exact optimization, and finally a restricted publisher.

## CI and GitHub Pages

This repo is onboarded to the [Verified OSS Loop](https://github.com/kvnloo/verified-oss-loop)
(`./bin/oss-onboard --with-automation --scheme rolling`). Workers never merge `main` or `dev`.

- CI (`.github/workflows/ci.yml`): `ruff`, `python -m pytest`, Pages snapshot, and the xyflow
  frontend (`npm test` when `scripts.test` exists, otherwise an esbuild bundle check).
- Pages (`.github/workflows/pages.yml`): Actions deploy of `python3 scripts/build-pages.py`
  to https://kvnloo.github.io/hermes-maintainer/ — not the old branch-source hack.

If the site 404s after the first successful `pages` workflow:

1. Settings → Pages → Source: **GitHub Actions**
2. Settings → Actions → General → Workflow permissions: **Read and write**
   (the Pages job needs `pages: write` and `id-token: write`)

Protect `main` and `dev` (PR required, no worker merge). Read `.verified-oss-loop/rollout.yml` for the *current* rollout scheme; do not assume a rolling scheme from old documentation.

## Seed context

`seed/audit/HERMES_TRIAGE_AUDIT.md` contains the initial repo dynamics audit, comparison with
OpenCode/Gemini CLI/Goose, and initial campaign seeds. The code does not treat these conclusions
as permanent truth. They are seed evidence that should be revalidated against current repository
state.
