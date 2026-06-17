#!/usr/bin/env bash
# SessionStart hook: surface the active spec and its progress into context.
# Degrades silently if python3 is unavailable or there are no specs.
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"}"
PROJECT="${CLAUDE_PROJECT_DIR:-"$PWD"}"

if command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/scripts/specflow.py" --root "$PROJECT" hook-context 2>/dev/null || true
fi
