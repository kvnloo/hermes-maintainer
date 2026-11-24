#!/usr/bin/env bash
# Prove the repo works from a fresh clone with an empty HOME (no dependence on this machine):
# git clone -> scripts/setup.sh -> serve on a free loopback port -> curl key routes.
#   scripts/fresh-clone-check.sh [ref]     (default: HEAD of this checkout)
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="$(pwd)"
REF="${1:-HEAD}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/hm-fresh.XXXXXX")"
echo "work dir: $WORK"
git clone -q --no-hardlinks "$SRC" "$WORK/repo"
git -C "$WORK/repo" checkout -q "$(git rev-parse "$REF")"
mkdir -p "$WORK/home"
cd "$WORK/repo"
env -u GITHUB_TOKEN -u HERMES_MAINTAINER_CONFIG -u HERMES_MAINTAINER_DATA_DIR \
  HOME="$WORK/home" XDG_CONFIG_HOME="$WORK/home/.config" XDG_CACHE_HOME="$WORK/home/.cache" \
  bash scripts/setup.sh
env -u GITHUB_TOKEN HOME="$WORK/home" .venv/bin/python scripts/smoke-serve.py
echo "fresh-clone-check: OK ($WORK)"
