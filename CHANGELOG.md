# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [0.3.0] - 2026-06-17
### Added
- **Drift guard** — a `PreToolUse` hook (`drift-guard.sh` + `specflow.py drift-check`) that warns once per session, per drift type, when an `Edit`/`Write`/`MultiEdit` strays outside the active plan's "Files to change" table, or when there is no active spec in a repo that already uses spec-flow.
- Whitelist for paths that should never warn: anything under `specs/`, plus a small set of dev/config basenames (`.gitignore`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `package.json`, `package-lock.json`, `pyproject.toml`, `requirements.txt`).
- Per-session warning state at `.spec-flow/session-state.json` (gitignored). Resets automatically on `$CLAUDE_SESSION_ID` change or corrupt state. Writes are atomic against concurrent `MultiEdit`-style invocations (`os.replace` + per-PID temp filename).
- 36 new unit + integration tests covering every drift type, the parser, the whitelist, session-state I/O, path normalization, case sensitivity, and concurrency.
### Changed
- `hooks/hooks.json` now registers `PreToolUse` alongside the existing `SessionStart` entry.
- `.gitignore` includes `.spec-flow/` (runtime state) and `/specs/` (the repo's own dogfooding plans stay local).
### Non-goals (deferred)
- Hard blocking, `.spec-flow.toml` config, plan-reviewer subagent, `/spec-update`, and glob/regex plan-path matching — each is a follow-up spec.

## [0.2.0] - 2026-06-17
### Added
- `planner`, `verifier`, and `spec-reviewer` subagents for each workflow phase.
- Deterministic progress engine `scripts/specflow.py` (`new`, `list`, `status`, `progress`, `validate`, `hook-context`) with unit tests.
- `spec.md` / `plan.md` templates.
- SessionStart hook that surfaces the active spec and its progress.
- Worked example under `examples/`.
### Changed
- Commands now delegate to subagents, scaffold via the engine, and validate structure.
- Skill documents the engine and subagents.

## [0.1.0] - 2026-06-17
### Added
- Initial release: `/spec`, `/plan`, `/build`, `/verify`, `/spec-status` commands and the `spec-driven-development` skill.
