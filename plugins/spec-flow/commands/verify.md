---
description: Adversarially verify the implementation against the spec's acceptance criteria (Verify phase)
argument-hint: [slug]
---

You are running the **Verify** phase — an honest, adversarial check.

Target slug: `$ARGUMENTS`. If empty, use the active spec (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" status`).

Steps:

1. Confirm `specs/<slug>/spec.md` and `plan.md` exist.
2. Delegate to the **`verifier` subagent**. It will run the test suite, check each acceptance criterion as PASS/FAIL/UNCERTAIN with concrete evidence, hunt for edge cases and regressions, confirm non-goals were respected, and update the criteria checkboxes in `spec.md` to reflect reality.
3. When it returns, show its verdict and the updated progress:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" progress <slug>
   ```
4. Report the final verdict plainly:
   - ✅ **Done** — all criteria pass with evidence, tests green.
   - ⚠️ **Not done** — exactly what is failing and the smallest next action.

Never claim success without evidence. If anything fails, say so plainly.
