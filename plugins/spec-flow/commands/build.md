---
description: Implement the feature strictly following the approved plan, one step at a time (Build phase)
argument-hint: [slug]
---

You are running the **Build** phase.

Target slug: `$ARGUMENTS`. If empty, use the active spec (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" status`).

Rules:

1. Read both `specs/<slug>/spec.md` and `specs/<slug>/plan.md`. If the plan is missing, stop and tell the user to run `/plan` first.
2. Implement the plan **one step at a time**, in order. After each step:
   - make the change,
   - run or adjust the relevant tests,
   - check off the step (`- [x]`) in `plan.md`.
3. Do NOT add work outside the plan or spec. If you discover the plan is wrong or incomplete, STOP, explain, and propose a plan update before continuing.
4. Keep changes minimal and respect the spec's non-goals — no scope creep.
5. Track progress at any time with:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" progress <slug>
   ```
6. When all steps are checked off, run the full relevant test suite, report real results, and tell the user to run `/verify <slug>`.

Prefer correctness and small diffs over speed.
