---
description: Turn a feature idea into a reviewed, testable spec (Spec phase)
argument-hint: [short feature description]
---

You are running the **Spec** phase of spec-driven development. Do NOT write implementation code.

Feature request: $ARGUMENTS

Steps:

1. If the request is ambiguous or underspecified, ask the user 2-4 sharp clarifying questions BEFORE writing the spec. Otherwise proceed.
2. Choose a short kebab-case slug. Scaffold the files deterministically:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" new <slug> --title "<short title>"
   ```
   This creates `specs/<slug>/spec.md` and `plan.md` from the templates. (If python3 is unavailable, create `specs/<slug>/spec.md` by hand using `${CLAUDE_PLUGIN_ROOT}/templates/spec.md` as the structure.)
3. Fill in `specs/<slug>/spec.md`: Problem, Goals, Non-goals, Requirements, and especially **Acceptance criteria** as a checklist (`- [ ]`) of objectively verifiable conditions. Prefer "returns 404 for unknown id" over "handles errors well".
4. **Harden it**: use the `spec-reviewer` subagent to critique the draft, then address its feedback (rewrite vague criteria, add missing non-goals).
5. Validate structure:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" validate <slug>
   ```
   Fix anything it reports.
6. Summarize the spec in 3 lines, ask the user to review, and tell them to run `/plan <slug>`.

End after the spec is written and validated. No planning or coding.
