#!/usr/bin/env bash
# One-command, idempotent setup: check tools, install, build the UI, load demo data,
# run the fast tests, print the next command.
#
#   scripts/setup.sh            full setup (safe to re-run)
#   scripts/setup.sh --check    doctor only (no installs, no writes)
#   SKIP_TESTS=1 / SKIP_UI=1    skip the pytest run / the UI rebuild
#   PYTHON=/path/to/python3.x   pick the interpreter (default: newest python3.11+ on PATH)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VENV="${VENV:-$ROOT/.venv}"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

say() { printf '\n==> %s\n' "$*"; }
missing=()
optional=()

py_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; }
pick_python() {
  if [ -n "${PYTHON:-}" ]; then py_ok "$PYTHON" && { echo "$PYTHON"; return; }; return 1; fi
  for c in python3.14 python3.13 python3.12 python3.11 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && py_ok "$(command -v "$c")"; then command -v "$c"; return; fi
  done
  return 1
}

say "checking tools"
PY="$(pick_python || true)"
[ -n "$PY" ] && echo "python: $PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))" \
  || missing+=("python>=3.11 (set PYTHON=... if it is not on PATH)")
command -v git >/dev/null 2>&1 && echo "git: $(git --version)" || missing+=("git")
NODE_OK=0
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 \
  && node -e 'process.exit(parseInt(process.versions.node) >= 18 ? 0 : 1)'; then
  NODE_OK=1; echo "node: $(node --version), npm $(npm --version)"
else
  optional+=("node>=18 + npm (rebuilds the xyflow bundle; the committed bundle is used without it)")
fi
UV="$(command -v uv || true)"
[ -n "$UV" ] && echo "uv: $UV" || optional+=("uv (faster installs; pip is used without it)")
[ -n "${GITHUB_TOKEN:-}" ] && echo "GITHUB_TOKEN: set" \
  || optional+=("GITHUB_TOKEN (scans work without it at 60 req/h; use 'scan --limit N')")

if [ ${#optional[@]} -gt 0 ]; then printf 'optional, not found:\n'; printf '  - %s\n' "${optional[@]}"; fi
if [ ${#missing[@]} -gt 0 ]; then
  printf '\nMISSING (required):\n'; printf '  - %s\n' "${missing[@]}"; exit 1
fi

if [ "$CHECK_ONLY" = 1 ]; then
  if [ -x "$VENV/bin/hermes-maintainer" ]; then exec "$VENV/bin/hermes-maintainer" doctor; fi
  echo "not installed yet: run scripts/setup.sh"; exit 1
fi

say "python environment ($VENV)"
if [ -x "$VENV/bin/python" ] && ! py_ok "$VENV/bin/python"; then
  echo "existing venv is older than 3.11; recreate it with: mv .venv .venv.old && scripts/setup.sh"
  exit 1
fi
if [ -n "$UV" ]; then
  [ -x "$VENV/bin/python" ] || "$UV" venv -q -p "$PY" "$VENV"
  "$UV" pip install -q -p "$VENV/bin/python" -e '.[dev]'
else
  [ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q -e '.[dev]'
fi

if [ "$NODE_OK" = 1 ] && [ -z "${SKIP_UI:-}" ]; then
  say "building the xyflow UI bundle"
  ./scripts/build-ui.sh
else
  say "skipping UI build; using the committed bundle"
fi

say "initializing the local database with demo seed campaigns"
# No git mirror here: it is a multi-GB clone of the target repo. `scan --mirror` fetches it later.
"$VENV/bin/hermes-maintainer" init --no-fetch-git --demo

if [ -z "${SKIP_TESTS:-}" ]; then
  say "fast tests"
  "$VENV/bin/python" -m pytest -q
fi

say "doctor"
"$VENV/bin/hermes-maintainer" doctor

cat <<EOF

Ready. Next:
  .venv/bin/hermes-maintainer serve        # http://127.0.0.1:8766 (demo campaigns load now)

Live data (read-only GitHub REST; GITHUB_TOKEN optional):
  .venv/bin/hermes-maintainer scan --mode fast --limit 50
  .venv/bin/hermes-maintainer analyze
EOF
