#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python)"
exec "$PY" "$SCRIPT_DIR/codex_strategy_review.py" "$@"
