# hermes-maintainer

`hermes-maintainer` is a local-first maintenance intelligence toolkit for agents contributing to **any GitHub repository**. This checkout still defaults to `NousResearch/hermes-agent`; pass `--repo owner/name` to target another origin.

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
4. **Read-only reasoning, restricted writes.** GitHub ingest is GET-only. Origin writes fail closed until `origin-preflight` returns an explicit allow.
5. **Deterministic core first.** Git, SQLite, FTS5, and explicit relations are the source of
   truth. Embeddings and solver support are optional accelerators.
6. **Optimize integration, not output volume.** The system should redirect agents toward
   missing evidence and integration work rather than generate another implementation.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# export GITHUB_TOKEN=...  # recommended but optional for public low-volume scans

hermes-maintainer init
hermes-maintainer scan --mode fast
hermes-maintainer scan --repo owner/name --mode fast
hermes-maintainer origin-preflight --repo owner/name
hermes-maintainer analyze
hermes-maintainer serve
```

Open `http://127.0.0.1:8766`. The dashboard uses the Hermes Teal theme (switchable to the other built-in Hermes palettes) and an xyflow campaign graph. Agents can start from [`llms.txt`](./llms.txt) or `http://127.0.0.1:8766/llms.txt`.

Public snapshot (GitHub Pages): https://kvnloo.github.io/hermes-maintainer/ (`llms.txt`, docs, and the dashboard on audit seed campaigns). The live graph still needs a local scan.

For continuous operation:

```bash
hermes-maintainer daemon
```

The daemon keeps the local git mirror fresh, runs fast metadata scans frequently, performs
deeper PR enrichment less often, rebuilds relations and campaigns, and updates health metrics.

## Maintainer permissions

Driving `NousResearch/hermes-agent` to **0 open issues (~14k) and PRs (~28k)** requires
maintainer or triage rights on that repository. `kvnloo` has **pull-only** access: GitHub
returns **403** on foreign ticket closes. This account can comment and post tables; it cannot
mass-close. Authors can still close their own tickets.

The live close table (duplicate / invalid rows already labeled, waiting on a maintainer) is
https://github.com/NousResearch/hermes-agent/issues/109552. See `BACKLOG-CLOSE.md` for the
play: close labeled copies, do not merge the 28k PRs, and leave `needs-repro` / `P0` / Bot
Screen follow-ups alone.

## Project map

```text
src/hermes_maintainer/
  github/       GitHub REST ingestion and normalization
  git/          mirror/fetch, ancestry, patch-id helpers
  graph/        SQLite-backed typed backlog graph
  analysis/     similarity, campaigns, evidence, root-cause mining
  optimizer/    greedy baseline and optional CP-SAT selection
  scheduler/    frequent batched scan loop
  api/          local FastAPI dashboard/API (`/api/graph`, campaign explorer, `/llms.txt`)
  ui/           Hermes-themed static dashboard + bundled xyflow graph
  agents/       prompts and agent work contracts

docs/           PRD, architecture, security, operations, schemas, execution plan
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

Protect `main` and `dev` (PR required, no worker merge). `preview` and `nightly` stay loose
under the default rolling scheme (`.verified-oss-loop/rollout.yml`).

## Seed context

`seed/audit/HERMES_TRIAGE_AUDIT.md` contains the initial repo dynamics audit, comparison with
OpenCode/Gemini CLI/Goose, and initial campaign seeds. The code does not treat these conclusions
as permanent truth. They are seed evidence that should be revalidated against current repository
state.
