# spec-flow (plugin)

Spec-driven development workflow for Claude Code: `/spec → /plan → /build → /verify`, backed by subagents and a deterministic progress engine.

See the [repository README](../../README.md) for full documentation, install instructions, and a worked example.

## Commands
- `/spec <idea>` — write & review a testable spec (problem, goals, non-goals, acceptance criteria).
- `/plan <slug>` — `planner` subagent writes a codebase-grounded plan mapped to the criteria.
- `/build <slug>` — implement the plan one verifiable step at a time.
- `/verify <slug>` — `verifier` subagent adversarially checks the result with evidence.
- `/spec-status` — deterministic progress across all specs.

## Subagents
- `spec-reviewer` — hardens draft specs (testability, scope, completeness).
- `planner` — turns a spec into a grounded implementation plan.
- `verifier` — adversarial verification against acceptance criteria.

## Engine
`scripts/specflow.py` — deterministic tracking (`new`, `list`, `status`, `progress`, `validate`, `hook-context`). Tests: `python3 -m unittest test_specflow`.

## Skill
- `spec-driven-development` — applies the discipline automatically for non-trivial work.

Artifacts live in `specs/<slug>/spec.md` and `plan.md` in the user's repo.
