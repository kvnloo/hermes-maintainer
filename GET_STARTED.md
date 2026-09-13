# Get started in 10 minutes

## Local

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
export GITHUB_TOKEN=ghp_or_fine_grained_read_token
hermes-maintainer scan --mode deep
hermes-maintainer analyze
hermes-maintainer serve
```

Open `http://127.0.0.1:8766`. Use the Graph tab for the xyflow campaign explorer
(seed canvas works before the first scan). `GET /llms.txt` is the agent map.

## Parallel cloud implementation

Give every agent `docs/CLOUD_AGENT_MASTER_PROMPT.md` plus exactly one task packet from `tasks/`.
Start with tasks 01-04 in parallel. Do not start the publisher milestone yet.

## Publish as a repository

After reviewing the scaffold:

```bash
./scripts/publish_repo.sh hermes-maintainer
```

It defaults to a private GitHub repository. Set `VISIBILITY=public` if desired.

## Highest priority engineering order

1. Stack and patch identity
2. CI evidence
3. Similarity evaluation
4. Dashboard campaign explorer
5. Acceptance criteria and commit-level atoms
6. Agent coordination packets
7. Integration worktrees and exact optimizer
8. Restricted publisher, only after shadow-mode accuracy is established
