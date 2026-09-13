#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
hermes-maintainer init
printf '\nReady. Next:\n  source .venv/bin/activate\n  hermes-maintainer scan --mode fast\n  hermes-maintainer analyze\n  hermes-maintainer serve\n'
