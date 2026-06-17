---
name: spec-driven-development
description: Use when implementing a non-trivial feature, change, or bugfix in a codebase. Enforces a disciplined Spec -> Plan -> Build -> Verify workflow instead of jumping straight to code. Trigger when the user asks to "build", "implement", "add a feature", or "refactor" something that spans more than a trivial edit.
---

# Spec-Driven Development

A disciplined workflow that prevents "vibe coding": never jump straight from a vague request to code. Move through four phases, each producing a written, tracked artifact.

## When to apply

Apply for any change beyond a one-line or obviously trivial edit. For tiny, unambiguous fixes, skip the ceremony and just do it.

## The four phases

1. **Spec** — capture *what* and *why* before *how*. Write a short spec: problem, goals, non-goals, testable requirements, and a checklist of acceptance criteria. Harden it with the `spec-reviewer` subagent. Resolve ambiguity with the user here, not later.
2. **Plan** — turn the spec into *how* via the `planner` subagent: explore the real codebase, list files to change, break work into small verifiable steps, and map every acceptance criterion to a step or test.
3. **Build** — implement the plan one step at a time, running tests after each step and checking off steps in `plan.md`. No work outside the plan; if the plan is wrong, stop and revise it.
4. **Verify** — the `verifier` subagent adversarially checks the result against the acceptance criteria with real evidence and updates the criteria checkboxes. Never claim done without passing tests.

## Tooling (deterministic state)

Progress is tracked by parsing the artifacts, not by guessing. Use the engine:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" status            # all specs + progress
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" new <slug> --title "..."
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" progress <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/specflow.py" validate <slug>
```

## Artifacts & conventions

- Artifacts live in `specs/<slug>/spec.md` and `specs/<slug>/plan.md`.
- Acceptance criteria and plan steps are checkboxes (`- [ ]`) so progress is real and verifiable.
- Slash commands: `/spec`, `/plan`, `/build`, `/verify`, `/spec-status`.

## Principles

- Specs are testable, not prose. Prefer "returns 404 for unknown id" over "handles errors well".
- Small steps beat big leaps — each step should be independently verifiable.
- Honesty in verification: PASS requires evidence; report gaps plainly.
- Respect non-goals; scope creep is the enemy.
