# Hermes Maintainer · Feature PRD library

A living, versioned product-specification website for **individual features** being developed around Hermes. The backlog graph is still the main maintainer application. These are public, linkable **feature requirements**, not replacement tickets or canonical merge queues.

- **Library**: \`features/index.html\` → \`https://kvnloo.github.io/hermes-maintainer/features/\`
- **Feature 001**: \`features/hermes-tern/index.html\` → \`https://kvnloo.github.io/hermes-maintainer/features/hermes-tern/\`
- **Shared style**: \`features/assets/prd.css\` (no JS frameworks/CDN)
- **Build**: \`python3 scripts/build-pages.py --out site\` copies \`features/\` to \`site/features/\`.
- **Deployment**: \`.github/workflows/pages.yml\` builds/deploys on allowed preview/main pushes after source PR review; only report a live URL after verifying Actions deployment.

## Adding a feature

1. Make a new, stable slug: \`features/<feature-slug>/index.html\`. Use \`../assets/prd.css\`; link home using \`../\`, the dashboard using \`../../\`.
2. Add a card to \`features/index.html\`, including keywords for client-side filtering. Do not add a fake product, progress percentage, or claimed launch.
3. The minimum PRD sections are: product problem, user journeys, behavior and constraints, system/ownership architecture, implementation/reuse opportunities, acceptance gates, decision register, source links, authorship/provenance, and the snapshot date.
4. Keep current issue/PR states in the **linked GitHub source**. Mark the website's status as a dated snapshot.
5. Preserve licensing/credit for implementation donors. Keep Hermes runtime/agent authority out of frontend ownership. Do not infer from a mock or unit test that a real host test passed.
6. Test static links, responsive layout and accessibility. Verify \`site/features/index.html\`, \`site/features/<slug>/index.html\` and their asset paths exist after the builder runs.

## Source boundaries

The feature library can link to [kvnloo/hermes-agent](https://github.com/kvnloo/hermes-agent), [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) and other original authors without being authorized to write to those repositories. Follow \`AGENTS.md\`: no autonomous merge into \`main\` or \`dev\`.

The original graphic is a dated vector reconstruction under \`docs/assets/hermes-tern-overview.svg\`. It is one supporting artifact inside the PRD; the PRD itself is a separate multi-section website.

## Source-backed RFC atlas (October 20, 2026)

The original Hermes × Tern PRD is handcrafted in `features/hermes-tern/index.html`. Other initiatives are declarative records stored under `features/specs/*.json`.

- `systems.json`: Labs, routing, RLM, memory, computer use and formal verification.
- `applications.json`: cross-owner collaboration, voice, plugins, dashboards, reliability, security, autonomy and public-interest scenarios.
- `frontier.json`: a research-only index for the nine independent Beyond-Agent hypotheses.
- `scripts/build_feature_atlas.py`: validates exact slug, required evidence fields and GitHub source links, then generates fully standalone HTML at `site/features/<slug>/index.html`, plus a searchable categorized index.
- `tests/test_feature_rfc_atlas.py`: validates categories, research status, safe URLs, actual build outputs and collision/unsafe-path handling.

### Adding a new initiative

1. Prefer an existing public RFC, branch or issue. Add a record with a unique slug, category, stage, user problem, proposed outcomes, journeys, authority boundaries, execution phases, acceptance criteria, metrics, risks, original human credit and direct public sources.
2. Use `Research only` for unproven hypotheses. A theory needs a falsifiable discriminator and kill case, not a shipping claim.
3. Run `ruff check . && python -m pytest -q && python3 scripts/build-pages.py --out /tmp/hermes-pages-site`. Confirm `/tmp/hermes-pages-site/features/<slug>/index.html` exists and the searchable index includes it.
4. Never paste private user traces, secrets, credentials, local absolute paths or unpublished work into these public specs.
5. All stages and source links are a dated research snapshot. Current status lives in upstream issues/PRs; do not auto-merge upstream or infer native hardware acceptance from source presence.

Each area may grow its own PRD pages and source records without adding another application framework or requiring a second GitHub Pages site.
