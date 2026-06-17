# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

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
