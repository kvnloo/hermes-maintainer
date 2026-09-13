#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src/hermes_maintainer/ui/graph-src"
OUT_DIR="$ROOT/src/hermes_maintainer/ui/static"
cd "$SRC"
npm install --silent
cp node_modules/@xyflow/react/dist/style.css "$OUT_DIR/xyflow.css"
npx esbuild graph-app.jsx \
  --bundle \
  --format=iife \
  --outfile="$OUT_DIR/graph-app.js" \
  --minify \
  --jsx=transform
echo "wrote src/hermes_maintainer/ui/static/graph-app.js and xyflow.css"
