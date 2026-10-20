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
