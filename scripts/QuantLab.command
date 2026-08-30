#!/bin/bash
# Double-click launcher (macOS). Uses the project venv; does not hardcode a username path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ -f "$ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi
export QUANT_LAB_MODE="${QUANT_LAB_MODE:-research}"
exec python -m quantlab.ui
