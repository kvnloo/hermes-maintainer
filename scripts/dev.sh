#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export HERMES_MAINTAINER_CONFIG="${HERMES_MAINTAINER_CONFIG:-config/hermes-maintainer.toml}"
exec uvicorn hermes_maintainer.api.app:create_app --factory --reload --host 127.0.0.1 --port 8766
