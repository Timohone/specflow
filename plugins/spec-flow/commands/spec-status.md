---
description: Show the status and progress of all specs in this repo
allowed-tools: Bash
---

Run the spec-flow engine and present its output verbatim, then add a one-line interpretation (what to do next):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" status
```

The table shows, per spec: whether `spec.md`/`plan.md` exist, acceptance criteria done/total, and plan steps done/total. The `*` marks the active (most recently modified) spec. Make no code changes.
