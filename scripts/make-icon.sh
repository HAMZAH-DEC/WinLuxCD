#!/usr/bin/env bash
# Regenerate the PNG + ICO icons from scripts/make-icon.py.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/make-icon.py" "$ROOT/icons"
