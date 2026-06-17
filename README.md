# spec-flow

**Spec-driven development for Claude Code.** Stop vibe-coding: turn vague ideas into testable specs, codebase-grounded plans, disciplined builds, and *honestly verified* results.

```
/spec   →   /plan   →   /build   →   /verify
 what?       how?        do it        prove it
```

Unlike a bag of prompt commands, spec-flow ships a real workflow engine: specialized **subagents** for planning and adversarial verification, a **deterministic progress tracker** (no LLM guesswork about what's done), **templates**, and a **SessionStart hook** that reminds you of your active spec.

---

## Why

LLM coding is fast but drifts in three predictable ways: it starts coding before the problem is clear, invents scope, and declares victory without proof. spec-flow installs a lightweight discipline that catches all three — while staying out of the way for trivial edits.

Every phase produces a small, reviewable artifact in your repo (`specs/<slug>/spec.md`, `plan.md`) with checkboxes, so progress is visible, diffable, resumable across sessions, and counted by code rather than vibes.

## What's inside

| Component | What it does |
|---|---|
| **5 slash commands** | `/spec` `/plan` `/build` `/verify` `/spec-status` drive the workflow. |
| **3 subagents** | `spec-reviewer` hardens specs, `planner` writes codebase-grounded plans, `verifier` checks results adversarially with evidence. |
| **Progress engine** | `scripts/specflow.py` parses artifacts and reports real done/total counts; powers status, validation, and the hook. |
| **Templates** | Consistent `spec.md` / `plan.md` structure every time. |
| **SessionStart hook** | Surfaces your active spec + progress at the start of each session. |
| **Skill** | `spec-driven-development` applies the discipline automatically for non-trivial work, even without a command. |

## Install

```bash
# 1. Add this repo as a marketplace
/plugin marketplace add Timohone/specflow

# 2. Install the plugin
/plugin install spec-flow

# 3. Restart Claude Code
```

(Requires `python3` on your PATH for the progress engine; the workflow still works without it, just without deterministic counts.)

## Quick start

```bash
/spec add rate limiting to the public API
# review specs/rate-limiting/spec.md (spec-reviewer will critique it), then:
/plan rate-limiting       # planner explores the codebase and writes the plan
/build rate-limiting      # implement step by step, tests after each
/verify rate-limiting     # verifier proves it against the acceptance criteria
/spec-status              # deterministic progress across all specs
```

Slug is optional for `/plan`, `/build`, `/verify`, `/spec-status` — it defaults to the active (most recently modified) spec.

See [`plugins/spec-flow/examples/`](plugins/spec-flow/examples/) for a complete worked spec + plan.

## How verification stays honest

The `verifier` subagent assumes the code is wrong until evidence proves otherwise. It runs your real test suite, marks each acceptance criterion PASS/FAIL/UNCERTAIN with concrete evidence (never PASS without it), hunts for edge cases and regressions, and updates the spec's checkboxes to match reality. `/verify` then shows deterministic counts from the engine — so "done" means done.

## Repo layout

```
spec-flow/
├── .claude-plugin/marketplace.json     # makes this repo an installable marketplace
└── plugins/spec-flow/
    ├── .claude-plugin/plugin.json
    ├── commands/        # /spec /plan /build /verify /spec-status
    ├── agents/          # spec-reviewer, planner, verifier
    ├── skills/spec-driven-development/SKILL.md
    ├── scripts/         # specflow.py engine + tests + session hook
    ├── templates/       # spec.md, plan.md
    ├── hooks/hooks.json # SessionStart → active spec
    └── examples/        # worked example
```

## Development

```bash
cd plugins/spec-flow/scripts
python3 -m unittest test_specflow -v
```

## Roadmap

- Optional MCP backend for shared/team specs and cross-repo spec history (paid tier).
- `/spec-archive` to move completed specs out of the way.
- A `PreToolUse` guard that nudges when large edits happen with no active spec.

## License

MIT © Timo Haldi — see [LICENSE](LICENSE).
