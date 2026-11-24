#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src/hermes_maintainer/ui/graph-src"
OUT_DIR="$ROOT/src/hermes_maintainer/ui/static"
cd "$SRC"
# npm ci keeps package-lock.json untouched so rebuilt bundles are reproducible.
if [ ! -f node_modules/.package-lock.json ] || [ package-lock.json -nt node_modules/.package-lock.json ]; then
  npm ci --silent --no-audit --no-fund
fi
cp node_modules/@xyflow/react/dist/style.css "$OUT_DIR/xyflow.css"
npx --no-install esbuild graph-app.jsx \
  --bundle \
  --format=iife \
  --outfile="$OUT_DIR/graph-app.js" \
  --minify \
  --jsx=transform
echo "wrote src/hermes_maintainer/ui/static/graph-app.js and xyflow.css"
