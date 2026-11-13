#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -q
npm test
npm run build
npm --prefix mobile run check
