#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
REPO_NAME="${1:-hermes-maintainer}"
VISIBILITY="${VISIBILITY:-private}"
if ! command -v gh >/dev/null; then
  echo "gh CLI is required" >&2
  exit 1
fi
if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "feat: bootstrap hermes-maintainer"
fi
gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
