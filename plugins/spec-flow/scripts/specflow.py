#!/usr/bin/env python3
"""spec-flow engine — deterministic tracking for spec-driven development.

This is the source of truth for spec/plan state. The LLM is unreliable at
counting; this script parses the artifacts and reports real numbers.

Subcommands:
  new <slug> [--title T]   Scaffold specs/<slug>/spec.md and plan.md from templates.
  list                     List all specs (one slug per line).
  status                   Table of all specs with progress; marks the active one.
  progress <slug>          Detailed progress for one spec.
  validate <slug>          Lint a spec/plan; non-zero exit if problems found.
  hook-context             Emit a SessionStart additionalContext JSON (or nothing).

Global: --root PATH (default: cwd), --json where supported.
Pure standard library; works on Python 3.8+.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

SPEC_FILE = "spec.md"
PLAN_FILE = "plan.md"
SPECS_DIR = "specs"

CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+\S")
HEADER_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

# Required sections for validation (matched by normalized substring).
SPEC_REQUIRED = ["problem", "goals", "nongoals", "requirements", "acceptance"]
PLAN_REQUIRED = ["approach", "steps", "testplan"]

EMBEDDED_SPEC_TEMPLATE = """# Spec: {{TITLE}}

> Status: draft · Slug: `{{SLUG}}` · Created: {{DATE}}

## Problem
<!-- What user problem does this solve, and why now? 2-4 sentences. -->

## Goals
<!-- What success looks like. -->
-

## Non-goals
<!-- What we explicitly will NOT do. -->
-

## Requirements
<!-- Numbered, testable functional requirements. -->
1.

## Acceptance criteria
<!-- Verifiable conditions that mean "done". /verify checks these. -->
- [ ]

## Open questions
-
"""

EMBEDDED_PLAN_TEMPLATE = """# Plan: {{TITLE}}

> Spec: `specs/{{SLUG}}/spec.md` · Created: {{DATE}}

## Approach
<!-- Chosen strategy and why; note one rejected alternative. -->

## Files to change
| Path | Change | Why |
|------|--------|-----|
|      |        |     |

## Steps
<!-- Small, independently verifiable steps. -->
- [ ]

## Test plan
<!-- Which tests prove each acceptance criterion; new tests to add. -->
-

## Risks & rollback
-
"""


def _norm(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())


def count_checkboxes_section(text: str, keyword: str):
    """Count (checked, total) checkbox items under the first header whose
    normalized title contains `keyword`. Section ends at the next header of
    the same or higher level. Returns (0, 0) if the section is absent."""
    keyword = _norm(keyword)
    lines = text.splitlines()
    headers = []  # (line_index, level, title)
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if m:
            headers.append((i, len(m.group(1)), m.group(2)))

    for idx, (line_no, level, title) in enumerate(headers):
        if keyword in _norm(title):
            end = len(lines)
            for (l2, lev2, _t2) in headers[idx + 1:]:
                if lev2 <= level:
                    end = l2
                    break
            checked = total = 0
            for ln in lines[line_no + 1:end]:
                m = CHECKBOX_RE.match(ln)
                if m:
                    total += 1
                    if m.group(1).lower() == "x":
                        checked += 1
            return checked, total
    return 0, 0


def load_session_state(state_path: Path, session_id: str) -> dict:
    """Load `.spec-flow/session-state.json`. Reset to a fresh state if the file
    is missing, unparseable, or its session_id doesn't match the current one."""
    fresh = {"session_id": session_id, "warned": []}
    try:
        data = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return fresh
    if not isinstance(data, dict) or data.get("session_id") != session_id:
        return fresh
    warned = data.get("warned")
    if not isinstance(warned, list):
        return fresh
    return {"session_id": session_id, "warned": [str(w) for w in warned]}


def save_session_state(state_path, state: dict) -> None:
    """Write session state atomically: write to a unique per-PID temp file then
    os.replace. Per-PID suffix prevents two concurrent invocations (e.g. a
    MultiEdit batch) from racing on the same `<path>.tmp` name — the loser
    of the race would otherwise hit FileNotFoundError on rename."""
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, p)


WHITELIST_BASENAMES = frozenset({
    ".gitignore", "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE",
    "package.json", "package-lock.json", "pyproject.toml", "requirements.txt",
})


def is_whitelisted(repo_rel_path: str) -> bool:
    """Return True if drift-check should silently allow this repo-relative path.
    Whitelist (hard-coded for v0.3.0): anything under `specs/`, plus a small set
    of dev/config basenames."""
    p = repo_rel_path
    if p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    if p == "specs" or p.startswith("specs/"):
        return True
    base = p.rsplit("/", 1)[-1]
    return base in WHITELIST_BASENAMES


def _normalize_plan_path(s: str) -> str:
    """Normalize a plan-entry path: strip whitespace, strip surrounding
    backticks, strip leading './', collapse repeated '/'. No case folding."""
    s = s.strip()
    if len(s) >= 2 and s[0] == "`" and s[-1] == "`":
        s = s[1:-1].strip()
    if s.startswith("./"):
        s = s[2:]
    while "//" in s:
        s = s.replace("//", "/")
    return s


def parse_files_to_change(plan_text: str) -> list:
    """Extract repo-relative paths from the 'Files to change' table in plan.md.
    Returns [] if the section is missing. Skips the markdown header row and the
    `|---|` separator row. Empty first cells are skipped."""
    lines = plan_text.splitlines()
    headers = []
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if m:
            headers.append((i, len(m.group(1)), m.group(2)))

    section_start = section_end = None
    for idx, (line_no, level, title) in enumerate(headers):
        if "files" in _norm(title):
            section_start = line_no + 1
            section_end = len(lines)
            for (l2, lev2, _t2) in headers[idx + 1:]:
                if lev2 <= level:
                    section_end = l2
                    break
            break
    if section_start is None:
        return []

    table_rows = [ln for ln in lines[section_start:section_end] if ln.lstrip().startswith("|")]
    # Skip header row + separator row.
    data_rows = table_rows[2:] if len(table_rows) >= 2 else []
    paths = []
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if not cells:
            continue
        first = _normalize_plan_path(cells[0])
        if first:
            paths.append(first)
    return paths


def has_section(text: str, keyword: str) -> bool:
    keyword = _norm(keyword)
    for line in text.splitlines():
        m = HEADER_RE.match(line)
        if m and keyword in _norm(m.group(2)):
            return True
    return False


def specs_root(root: Path) -> Path:
    return Path(root) / SPECS_DIR


def spec_info(spec_dir: Path) -> dict:
    spec_path = spec_dir / SPEC_FILE
    plan_path = spec_dir / PLAN_FILE
    info = {
        "slug": spec_dir.name,
        "has_spec": spec_path.exists(),
        "has_plan": plan_path.exists(),
        "criteria_done": 0,
        "criteria_total": 0,
        "steps_done": 0,
        "steps_total": 0,
        "mtime": 0.0,
    }
    mtimes = []
    if spec_path.exists():
        t = spec_path.read_text(encoding="utf-8", errors="replace")
        info["criteria_done"], info["criteria_total"] = count_checkboxes_section(t, "acceptance")
        mtimes.append(spec_path.stat().st_mtime)
    if plan_path.exists():
        t = plan_path.read_text(encoding="utf-8", errors="replace")
        info["steps_done"], info["steps_total"] = count_checkboxes_section(t, "steps")
        mtimes.append(plan_path.stat().st_mtime)
    info["mtime"] = max(mtimes) if mtimes else 0.0
    return info


def all_specs(root: Path) -> list:
    d = specs_root(root)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.iterdir()):
        if p.is_dir() and ((p / SPEC_FILE).exists() or (p / PLAN_FILE).exists()):
            out.append(spec_info(p))
    return out


def active_spec(specs: list):
    return max(specs, key=lambda s: s["mtime"]) if specs else None


def _frac(done: int, total: int) -> str:
    return f"{done}/{total}" if total else "-/-"


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def _load_template(name: str, fallback: str) -> str:
    p = _templates_dir() / name
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return fallback


def _fill(tpl: str, slug: str, title: str) -> str:
    today = _dt.date.today().isoformat()
    return (tpl.replace("{{TITLE}}", title)
               .replace("{{SLUG}}", slug)
               .replace("{{DATE}}", today))


# ---- commands ----

def cmd_new(args) -> int:
    slug = args.slug.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        print(f"error: invalid slug '{args.slug}' (use lowercase letters, digits, hyphens)", file=sys.stderr)
        return 2
    title = args.title or slug.replace("-", " ").title()
    d = specs_root(args.root) / slug
    d.mkdir(parents=True, exist_ok=True)
    spec_path = d / SPEC_FILE
    plan_path = d / PLAN_FILE
    created = []
    if not spec_path.exists() or args.force:
        spec_path.write_text(_fill(_load_template("spec.md", EMBEDDED_SPEC_TEMPLATE), slug, title), encoding="utf-8")
        created.append(str(spec_path))
    if not plan_path.exists() or args.force:
        plan_path.write_text(_fill(_load_template("plan.md", EMBEDDED_PLAN_TEMPLATE), slug, title), encoding="utf-8")
        created.append(str(plan_path))
    if args.json:
        print(json.dumps({"slug": slug, "created": created}))
    else:
        if created:
            print("created:\n  " + "\n  ".join(created))
        else:
            print(f"spec '{slug}' already exists (use --force to overwrite)")
    return 0


def cmd_list(args) -> int:
    specs = all_specs(args.root)
    if args.json:
        print(json.dumps([s["slug"] for s in specs]))
    else:
        for s in specs:
            print(s["slug"])
    return 0


def cmd_status(args) -> int:
    specs = all_specs(args.root)
    if args.json:
        act = active_spec(specs)
        for s in specs:
            s["active"] = bool(act and s["slug"] == act["slug"])
        print(json.dumps(specs, indent=2))
        return 0
    if not specs:
        print("No specs yet. Create one with /spec or: specflow.py new <slug>")
        return 0
    act = active_spec(specs)
    name_w = max(4, max(len(s["slug"]) for s in specs))
    header = "SPEC".ljust(name_w)
    print(f"  {header}  SPEC PLAN  CRITERIA  STEPS")
    for s in specs:
        mark = "*" if act and s["slug"] == act["slug"] else " "
        print(f"{mark} {s['slug'].ljust(name_w)}  "
              f"{'yes ' if s['has_spec'] else 'no  '} "
              f"{'yes ' if s['has_plan'] else 'no  '} "
              f"{_frac(s['criteria_done'], s['criteria_total']).ljust(8)} "
              f"{_frac(s['steps_done'], s['steps_total'])}")
    if act:
        print(f"\nactive: {act['slug']}")
    return 0


def cmd_progress(args) -> int:
    d = specs_root(args.root) / args.slug
    if not d.is_dir():
        print(f"error: no spec '{args.slug}'", file=sys.stderr)
        return 2
    info = spec_info(d)
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    print(f"spec: {info['slug']}")
    print(f"  spec.md: {'present' if info['has_spec'] else 'MISSING'}")
    print(f"  plan.md: {'present' if info['has_plan'] else 'MISSING'}")
    print(f"  acceptance criteria: {_frac(info['criteria_done'], info['criteria_total'])}")
    print(f"  plan steps:          {_frac(info['steps_done'], info['steps_total'])}")
    return 0


def cmd_validate(args) -> int:
    d = specs_root(args.root) / args.slug
    problems = []
    if not d.is_dir():
        print(f"error: no spec '{args.slug}'", file=sys.stderr)
        return 2
    spec_path = d / SPEC_FILE
    plan_path = d / PLAN_FILE

    if not spec_path.exists():
        problems.append("spec.md is missing")
    else:
        t = spec_path.read_text(encoding="utf-8", errors="replace")
        for key in SPEC_REQUIRED:
            if not has_section(t, key):
                problems.append(f"spec.md missing section: {key}")
        _, total = count_checkboxes_section(t, "acceptance")
        if total == 0:
            problems.append("spec.md has no acceptance criteria checkboxes")

    if not plan_path.exists():
        problems.append("plan.md is missing")
    else:
        t = plan_path.read_text(encoding="utf-8", errors="replace")
        for key in PLAN_REQUIRED:
            if not has_section(t, key):
                problems.append(f"plan.md missing section: {key}")
        _, total = count_checkboxes_section(t, "steps")
        if total == 0:
            problems.append("plan.md has no steps checkboxes")

    if args.json:
        print(json.dumps({"slug": args.slug, "ok": not problems, "problems": problems}, indent=2))
    else:
        if not problems:
            print(f"OK: '{args.slug}' is well-formed")
        else:
            print(f"{len(problems)} problem(s) in '{args.slug}':")
            for p in problems:
                print(f"  - {p}")
    return 0 if not problems else 1


def cmd_hook_context(args) -> int:
    specs = all_specs(args.root)
    if not specs:
        return 0  # emit nothing
    act = active_spec(specs)
    parts = [
        f"spec-flow: active spec '{act['slug']}' — "
        f"{_frac(act['criteria_done'], act['criteria_total'])} acceptance criteria, "
        f"{_frac(act['steps_done'], act['steps_total'])} plan steps."
    ]
    others = [s for s in specs if s["slug"] != act["slug"]]
    if others:
        listing = ", ".join(
            f"{s['slug']} ({_frac(s['criteria_done'], s['criteria_total'])})" for s in others[:5]
        )
        parts.append(f"Other specs: {listing}.")
    parts.append("Run /spec-status for the full picture, and continue the spec→plan→build→verify flow.")
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": " ".join(parts),
        }
    }
    print(json.dumps(out))
    return 0


def _drift_payload(drift_type: str, slug: str, remedy: str) -> str:
    reason = f"spec-flow: {drift_type} [spec={slug}] — {remedy}"
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    })


def cmd_drift_check(args) -> int:
    """PreToolUse drift detector. Always exits 0 (never blocks); writes a JSON
    warning payload to stdout when drift is detected and not yet warned this
    session."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if not session_id:
        return 0  # untracked invocation (e.g. running outside Claude Code)

    root = Path(args.root)
    abs_path = Path(args.path)
    try:
        repo_rel = str(abs_path.relative_to(root))
    except ValueError:
        # path outside root → fall back to a normalized relative form
        repo_rel = os.path.relpath(str(abs_path), str(root))
    repo_rel = _normalize_plan_path(repo_rel)

    # rule 1: whitelist
    if is_whitelisted(repo_rel):
        return 0

    # rule 2: no specs/ dir → brand-new repo, stay silent
    specs_dir = specs_root(root)
    if not specs_dir.is_dir():
        return 0

    state_path = root / ".spec-flow" / "session-state.json"
    state = load_session_state(state_path, session_id)

    def _emit(drift_type: str, slug: str, remedy: str) -> int:
        if drift_type in state["warned"]:
            return 0
        state["warned"].append(drift_type)
        save_session_state(state_path, state)
        print(_drift_payload(drift_type, slug, remedy))
        return 0

    specs = all_specs(root)
    act = active_spec(specs)

    # rule 3: specs/ exists but no active spec
    if act is None:
        return _emit("no_active_spec", "-",
                     "run /spec before non-trivial edits, or whitelist this path")

    # rule 4: active spec but no plan.md
    if not act["has_plan"]:
        return _emit("no_plan", act["slug"],
                     f"run /plan {act['slug']} to ground the build in the codebase")

    # rule 5: file not in the plan's Files-to-change table
    plan_text = (specs_dir / act["slug"] / PLAN_FILE).read_text(encoding="utf-8", errors="replace")
    listed = set(parse_files_to_change(plan_text))
    if repo_rel not in listed:
        return _emit(f"unlisted_file:{repo_rel}", act["slug"],
                     f"add {repo_rel} to plan.md or stop and update the plan")

    # rule 6: listed file → silent allow
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="specflow", description="spec-flow engine")
    p.add_argument("--root", default=os.getcwd(), help="project root (default: cwd)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("new", help="scaffold a new spec")
    sp.add_argument("slug")
    sp.add_argument("--title", default=None)
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_new)

    sub.add_parser("list", help="list spec slugs").set_defaults(func=cmd_list)
    sub.add_parser("status", help="status table").set_defaults(func=cmd_status)

    pr = sub.add_parser("progress", help="progress for one spec")
    pr.add_argument("slug")
    pr.set_defaults(func=cmd_progress)

    va = sub.add_parser("validate", help="lint a spec/plan")
    va.add_argument("slug")
    va.set_defaults(func=cmd_validate)

    sub.add_parser("hook-context", help="SessionStart context JSON").set_defaults(func=cmd_hook_context)

    dc = sub.add_parser("drift-check", help="PreToolUse drift detector")
    dc.add_argument("path", help="absolute path of the file being edited")
    dc.set_defaults(func=cmd_drift_check)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
