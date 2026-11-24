# hermes-maintainer

Independent community notes on how [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) actually works: the rules reviewers apply, how contributions land, who merges what, and where newcomers waste time. It also includes a read-only backlog graph of the repo's issues and PRs. This is **not** official Nous Research policy, and nobody here speaks for the maintainers. Every claim links to upstream source at a pinned SHA or to a `gh` query you can re-run. If upstream disagrees, upstream wins.

*Facts last re-measured 2026-11-24 against hermes-agent main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0).*

## Things about Hermes that aren't obvious

- **[Prompt caching is sacred, and the core is a narrow waist](knowledge/INVARIANTS.md).** Mid-conversation changes defer to the next session. New capability goes in a skill, plugin or service-gated tool before a core tool. Paths are profile-aware. Behaviour goes in `config.yaml`; `.env` is for secrets only.
- **[Never run bare `pytest`](knowledge/TESTING.md).** `scripts/run_tests.sh` isolates each file and blanks credentials. `tests/conftest.py` swaps in a throwaway `HERMES_HOME` so tests can't touch your real `~/.hermes`.
- **[The approval prompt isn't a security boundary](knowledge/SECURITY_AND_CI.md).** Per SECURITY.md, only OS isolation is. Approval-gate bypasses are public hardening work, not advisories. Your first fork PR's CI waits for a maintainer to approve it.
- **[Merged PRs undercount contributors](knowledge/HOW_WORK_LANDS.md).** Maintainers cherry-pick contributor commits into carrier PRs. 51% of the 11,400 commits on `main` in the last 30 days were committed by someone other than their author. Measure commits on `main`, not PRs merged.
- **[Who merges which area, and when](knowledge/WHO_MAINTAINS_WHAT.md).** 4,229 merges in 30 days, in every hour of the day. One maintainer merged 80% of them, mostly plugin-catalog entries.
- **[The plugin catalog is a list of SHA pins, plus a dozen sibling repos](knowledge/PLUGINS_AND_REPOS.md).** Shows who merges each repo and which are dormant.
- **[The board is huge, so evidence beats new PRs](knowledge/CURRENT_PUBLIC_WORK.md).** 19,810 open issues and 34,392 open PRs. Includes a dated radar of open ACP and reliability issues.
- **[How to run a triage wave](knowledge/TRIAGE_WAVES.md), [what makes a PR reviewable](knowledge/REVIEW_EVIDENCE.md), and [real public cases](knowledge/PUBLIC_CASES.md).**
- [Architecture routing](knowledge/HERMES_INTENT.md) · [Source and privacy rules for this repo](knowledge/SOURCE_POLICY.md) · [Start here](knowledge/START_HERE.md) has the full reading order.

## The backlog graph (optional tool)

`hermes-maintainer` also turns the live repo into a typed graph of problem families, so you can tell duplicates, same-root-cause reports, survivors, donors and superseded PRs apart. Its GitHub access is read-only; it has no mutation path.

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.11+
pip install -e '.[dev]'
export GITHUB_TOKEN=...   # optional for low-volume public scans
hermes-maintainer init && hermes-maintainer scan --mode fast && hermes-maintainer analyze
hermes-maintainer serve   # http://127.0.0.1:8766  (/graph for the xyflow canvas)
```

Static snapshot: <https://kvnloo.github.io/hermes-maintainer/> (guide search at the root, graph demo at `graph.html`, `llms.txt` for agents). `hermes-maintainer daemon` keeps a local mirror and scans fresh. Design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PRD.md](docs/PRD.md), [docs/ROADMAP.md](docs/ROADMAP.md).

### Optional: local chat with Hermes over ACP

The home page can talk to your own Hermes via `hermes acp`. It is off by default and listens on loopback only:

```bash
export HERMES_MAINTAINER_ACP_ENABLED=1
export HERMES_MAINTAINER_ACP_WORKSPACE="$HOME/src/hermes-agent-fork"   # an expendable clone
hermes-maintainer serve
```

This is a trusted single-user interface, not a sandbox. Hermes keeps whatever terminal, file and Git access you configured, and the approval UI is not a security barrier. Never expose it beyond localhost. See [docs/ACP_WEBAPP.md](docs/ACP_WEBAPP.md).

## Contributing to these notes

PRs welcome on this repo: see [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). Workers open PRs and never merge `main`. Fix a stale number by re-running the query shown next to it and updating the date and SHA. Cite only public sources. Nothing here writes to `NousResearch/hermes-agent`.

Older September 2026 working notes are in [archive/](archive/README.md), kept for history only. `seed/audit/` is the original September audit; the demo graph still loads its `campaign_seeds.json`.
