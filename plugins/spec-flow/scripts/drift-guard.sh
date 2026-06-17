#!/usr/bin/env bash
# PreToolUse drift guard. Reads tool input JSON from stdin, extracts the file
# path, asks the engine whether this edit drifts from the active plan, and
# forwards the engine's JSON payload to stdout (where Claude Code consumes it).
#
# Degrades silently when python3 is missing, when no file_path is present, or
# when running outside Claude Code (no $CLAUDE_SESSION_ID).
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"}"
PROJECT="${CLAUDE_PROJECT_DIR:-"$PWD"}"

command -v python3 >/dev/null 2>&1 || exit 0

INPUT="$(cat || true)"
[ -z "$INPUT" ] && exit 0

FILE_PATH="$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get("tool_input", {}).get("file_path", ""))' 2>/dev/null || true)"
[ -z "$FILE_PATH" ] && exit 0

python3 "$ROOT/scripts/specflow.py" --root "$PROJECT" drift-check "$FILE_PATH" 2>/dev/null || true
