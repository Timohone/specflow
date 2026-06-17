---
description: Turn an approved spec into a codebase-grounded implementation plan (Plan phase)
argument-hint: [slug]
---

You are running the **Plan** phase. Do NOT write implementation code yet.

Target slug: `$ARGUMENTS`. If empty, pick the active spec:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" status
```

Steps:

1. Confirm `specs/<slug>/spec.md` exists and is non-empty. If not, stop and tell the user to run `/spec` first.
2. Delegate the planning to the **`planner` subagent**. It will explore the real codebase and write `specs/<slug>/plan.md` with: Approach (+ one rejected alternative), Files to change, ordered Steps checklist, Test plan, and Risks & rollback — with every acceptance criterion mapped to a step or test.
3. When the planner returns, review the plan for traceability: is every acceptance criterion covered? Surface any gaps it flagged.
4. Validate structure:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" validate <slug>
   ```
5. Summarize, ask the user to approve, and tell them to run `/build <slug>`.

End after the plan is written. No implementation.
