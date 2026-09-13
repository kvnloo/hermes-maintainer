# Contributing

Hermes-maintainer optimizes coordination, so its own development must avoid duplicate parallel
implementation.

- Claim one task packet from `tasks/`.
- Keep unrelated roadmap items out of the same change.
- Prefer standard-library and already-declared dependencies.
- Preserve deterministic fallbacks when adding model-powered analysis.
- A similarity score is a retrieval hint, not a repository disposition.
- Tests should exercise behavior and evidence contracts.
- No GitHub mutation code belongs in the early milestones.

Run:

```bash
PYTHONPATH=src pytest -q
ruff check .
./scripts/build-ui.sh   # only if you change ui/graph-src
```
