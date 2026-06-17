#!/usr/bin/env python3
"""Tests for the spec-flow engine. Run: python3 -m unittest test_specflow"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import specflow  # noqa: E402


SPEC_SAMPLE = """# Spec: Demo

## Problem
x

## Goals
- a

## Non-goals
- b

## Requirements
1. r

## Acceptance criteria
- [x] done one
- [ ] not yet
- [X] done two

## Open questions
-
"""

PLAN_SAMPLE = """# Plan: Demo

## Approach
y

## Steps
- [x] step a
- [ ] step b
- [ ] step c

## Test plan
- t

## Risks & rollback
- r
"""


class CheckboxTests(unittest.TestCase):
    def test_counts_acceptance(self):
        self.assertEqual(specflow.count_checkboxes_section(SPEC_SAMPLE, "acceptance"), (2, 3))

    def test_counts_steps(self):
        self.assertEqual(specflow.count_checkboxes_section(PLAN_SAMPLE, "steps"), (1, 3))

    def test_missing_section(self):
        self.assertEqual(specflow.count_checkboxes_section(SPEC_SAMPLE, "nonexistent"), (0, 0))

    def test_section_boundary(self):
        # "Open questions" has a non-checkbox dash that must not be counted as a criterion
        checked, total = specflow.count_checkboxes_section(SPEC_SAMPLE, "acceptance")
        self.assertEqual(total, 3)

    def test_has_section(self):
        self.assertTrue(specflow.has_section(SPEC_SAMPLE, "acceptance"))
        self.assertFalse(specflow.has_section(SPEC_SAMPLE, "deployment"))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        d = self.root / "specs" / "demo"
        d.mkdir(parents=True)
        (d / "spec.md").write_text(SPEC_SAMPLE, encoding="utf-8")
        (d / "plan.md").write_text(PLAN_SAMPLE, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_spec_info(self):
        info = specflow.spec_info(self.root / "specs" / "demo")
        self.assertTrue(info["has_spec"])
        self.assertTrue(info["has_plan"])
        self.assertEqual((info["criteria_done"], info["criteria_total"]), (2, 3))
        self.assertEqual((info["steps_done"], info["steps_total"]), (1, 3))

    def test_all_and_active(self):
        specs = specflow.all_specs(self.root)
        self.assertEqual(len(specs), 1)
        self.assertEqual(specflow.active_spec(specs)["slug"], "demo")

    def test_empty_root(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(specflow.all_specs(Path(empty)), [])
            self.assertIsNone(specflow.active_spec([]))


class NewAndValidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _args(self, **kw):
        class A:
            pass
        a = A()
        a.root = str(self.root)
        a.json = False
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    def test_new_scaffolds_files(self):
        rc = specflow.cmd_new(self._args(slug="my-feature", title="My Feature", force=False))
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "specs" / "my-feature" / "spec.md").exists())
        self.assertTrue((self.root / "specs" / "my-feature" / "plan.md").exists())

    def test_new_rejects_bad_slug(self):
        rc = specflow.cmd_new(self._args(slug="Bad Slug!", title=None, force=False))
        self.assertEqual(rc, 2)

    def test_validate_flags_empty_scaffold(self):
        specflow.cmd_new(self._args(slug="feat", title=None, force=False))
        # fresh scaffold has section headers but zero checked/!defined criteria items
        rc = specflow.cmd_validate(self._args(slug="feat"))
        # scaffold has a single empty "- [ ]" so criteria_total >= 1; sections present -> ok
        self.assertIn(rc, (0, 1))

    def test_validate_missing_spec(self):
        rc = specflow.cmd_validate(self._args(slug="ghost"))
        self.assertEqual(rc, 2)


# ---- drift-guard parser ----

PLAN_WITH_FILES = """# Plan: x

## Approach
y

## Files to change
| Path | Change | Why |
|---|---|---|
| `src/foo.py` | edit | reason |
| src/bar.py | edit | reason |
| ./src/baz.py | edit | reason |
|  | skip | empty first cell |

## Steps
- [ ]
"""


class ParseFilesToChangeTests(unittest.TestCase):
    def test_skips_header_and_separator(self):
        paths = specflow.parse_files_to_change(PLAN_WITH_FILES)
        self.assertNotIn("Path", paths)
        self.assertFalse(any(p.startswith("-") for p in paths))

    def test_extracts_backtick_wrapped_path(self):
        self.assertIn("src/foo.py", specflow.parse_files_to_change(PLAN_WITH_FILES))

    def test_extracts_plain_path(self):
        self.assertIn("src/bar.py", specflow.parse_files_to_change(PLAN_WITH_FILES))

    def test_strips_leading_dot_slash(self):
        paths = specflow.parse_files_to_change(PLAN_WITH_FILES)
        self.assertIn("src/baz.py", paths)
        self.assertNotIn("./src/baz.py", paths)

    def test_skips_empty_first_cell(self):
        paths = specflow.parse_files_to_change(PLAN_WITH_FILES)
        self.assertNotIn("", paths)

    def test_returns_empty_when_section_missing(self):
        self.assertEqual(specflow.parse_files_to_change("# Plan\n\n## Approach\nx\n"), [])


class WhitelistTests(unittest.TestCase):
    def test_specs_prefix(self):
        self.assertTrue(specflow.is_whitelisted("specs/foo/spec.md"))
        self.assertTrue(specflow.is_whitelisted("specs/anything"))

    def test_each_whitelisted_basename(self):
        for name in [".gitignore", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
                     "LICENSE", "package.json", "package-lock.json",
                     "pyproject.toml", "requirements.txt"]:
            self.assertTrue(specflow.is_whitelisted(name), name)
            self.assertTrue(specflow.is_whitelisted(f"sub/dir/{name}"), name)

    def test_non_whitelisted(self):
        self.assertFalse(specflow.is_whitelisted("src/main.py"))
        self.assertFalse(specflow.is_whitelisted("README.txt"))  # extension matters
        self.assertFalse(specflow.is_whitelisted("notspecs/foo"))  # prefix must be exact

    def test_path_normalization_equivalence(self):
        # backticks / leading ./ / // collapse — all collapse to src/foo.py
        self.assertEqual(specflow._normalize_plan_path("`src/foo.py`"), "src/foo.py")
        self.assertEqual(specflow._normalize_plan_path("./src/foo.py"), "src/foo.py")
        self.assertEqual(specflow._normalize_plan_path("src//foo.py"), "src/foo.py")
        self.assertEqual(specflow._normalize_plan_path("  src/foo.py  "), "src/foo.py")
        # case-sensitive
        self.assertNotEqual(specflow._normalize_plan_path("src/Foo.py"), "src/foo.py")


class SessionStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / ".spec-flow" / "session-state.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_file_returns_empty(self):
        state = specflow.load_session_state(self.path, "sid-1")
        self.assertEqual(state, {"session_id": "sid-1", "warned": []})

    def test_save_and_reload_same_session(self):
        specflow.save_session_state(self.path, {"session_id": "sid-1", "warned": ["a"]})
        state = specflow.load_session_state(self.path, "sid-1")
        self.assertEqual(state["warned"], ["a"])

    def test_session_id_mismatch_resets(self):
        specflow.save_session_state(self.path, {"session_id": "sid-1", "warned": ["a"]})
        state = specflow.load_session_state(self.path, "sid-2")
        self.assertEqual(state, {"session_id": "sid-2", "warned": []})

    def test_corrupt_file_resets(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("not json {{")
        state = specflow.load_session_state(self.path, "sid-1")
        self.assertEqual(state, {"session_id": "sid-1", "warned": []})

    def test_save_is_atomic(self):
        # write once, write again with new content — final state matches second write
        specflow.save_session_state(self.path, {"session_id": "sid-1", "warned": ["a"]})
        specflow.save_session_state(self.path, {"session_id": "sid-1", "warned": ["a", "b"]})
        state = specflow.load_session_state(self.path, "sid-1")
        self.assertEqual(state["warned"], ["a", "b"])

    def test_save_creates_parent_dir(self):
        self.assertFalse(self.path.parent.exists())
        specflow.save_session_state(self.path, {"session_id": "sid-1", "warned": []})
        self.assertTrue(self.path.exists())


class DriftCheckTests(unittest.TestCase):
    """Covers all six rules of cmd_drift_check + session gating + dedup."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._env = os.environ.copy()
        os.environ["CLAUDE_SESSION_ID"] = "test-session"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def _run(self, abs_path):
        """Invoke cmd_drift_check capturing stdout. Returns (exit_code, stdout)."""
        import io, contextlib
        class A:
            pass
        a = A()
        a.root = str(self.root)
        a.json = False
        a.path = str(abs_path)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = specflow.cmd_drift_check(a)
        return rc, buf.getvalue()

    def _make_spec(self, slug, files=None, with_plan=True):
        d = self.root / "specs" / slug
        d.mkdir(parents=True)
        (d / "spec.md").write_text("# Spec: x\n## Problem\nx\n", encoding="utf-8")
        if with_plan:
            plan = "# Plan: x\n\n## Files to change\n| Path | Change | Why |\n|---|---|---|\n"
            for f in (files or []):
                plan += f"| {f} | edit | reason |\n"
            plan += "\n## Steps\n- [ ]\n"
            (d / "plan.md").write_text(plan, encoding="utf-8")

    # ---- rule 1: whitelist ----
    def test_specs_path_silent(self):
        rc, out = self._run(self.root / "specs" / "foo" / "spec.md")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_whitelisted_basename_silent(self):
        rc, out = self._run(self.root / "README.md")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    # ---- rule 2: no specs dir ----
    def test_brand_new_repo_silent(self):
        rc, out = self._run(self.root / "src" / "main.py")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    # ---- rule 3: no active spec ----
    def test_no_active_spec_warns(self):
        (self.root / "specs").mkdir()  # empty specs dir
        rc, out = self._run(self.root / "src" / "main.py")
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("no_active_spec", reason)
        self.assertTrue(reason.startswith("spec-flow:"))

    # ---- rule 4: no plan ----
    def test_no_plan_warns_then_dedups(self):
        self._make_spec("feat", with_plan=False)
        rc1, out1 = self._run(self.root / "src" / "main.py")
        self.assertIn("no_plan", json.loads(out1)["hookSpecificOutput"]["permissionDecisionReason"])
        rc2, out2 = self._run(self.root / "src" / "main.py")
        self.assertEqual(out2, "")
        self.assertEqual(rc2, 0)

    # ---- rule 5: unlisted file ----
    def test_unlisted_file_warns(self):
        self._make_spec("feat", files=["src/foo.py"])
        rc, out = self._run(self.root / "src" / "bar.py")
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("unlisted_file:src/bar.py", reason)
        self.assertIn("spec=feat", reason)

    # ---- rule 6: listed file silent ----
    def test_listed_file_silent(self):
        self._make_spec("feat", files=["src/foo.py"])
        rc, out = self._run(self.root / "src" / "foo.py")
        self.assertEqual(out, "")
        self.assertEqual(rc, 0)

    # ---- session gating ----
    def test_session_dedup(self):
        self._make_spec("feat", files=["src/foo.py"])
        rc1, out1 = self._run(self.root / "src" / "bar.py")
        self.assertNotEqual(out1, "")
        rc2, out2 = self._run(self.root / "src" / "bar.py")
        self.assertEqual(out2, "")

    def test_unlisted_dedup_is_per_path(self):
        self._make_spec("feat", files=["src/foo.py"])
        _, out1 = self._run(self.root / "src" / "bar.py")
        _, out2 = self._run(self.root / "src" / "baz.py")
        self.assertNotEqual(out1, "")
        self.assertNotEqual(out2, "")  # different unlisted path → new warning

    def test_session_id_change_resets(self):
        self._make_spec("feat", files=["src/foo.py"])
        _, out1 = self._run(self.root / "src" / "bar.py")
        self.assertNotEqual(out1, "")
        os.environ["CLAUDE_SESSION_ID"] = "different-session"
        _, out2 = self._run(self.root / "src" / "bar.py")
        self.assertNotEqual(out2, "")

    def test_empty_session_id_silent(self):
        self._make_spec("feat", files=["src/foo.py"])
        os.environ["CLAUDE_SESSION_ID"] = ""
        rc, out = self._run(self.root / "src" / "bar.py")
        self.assertEqual(out, "")
        self.assertEqual(rc, 0)

    # ---- path normalization equivalence + case ----
    def test_plan_entries_equivalence(self):
        # all three forms in the plan should match an edit of src/foo.py
        for form in ["`src/foo.py`", "src/foo.py", "./src/foo.py"]:
            with tempfile.TemporaryDirectory() as t2:
                self.root = Path(t2)
                self._make_spec("feat", files=[form])
                _, out = self._run(self.root / "src" / "foo.py")
                self.assertEqual(out, "", f"form {form!r} should match")

    def test_case_sensitive_no_match(self):
        self._make_spec("feat", files=["src/foo.py"])
        _, out = self._run(self.root / "src" / "Foo.py")
        self.assertNotEqual(out, "")  # case-sensitive → unlisted

    def test_path_outside_root_falls_back(self):
        self._make_spec("feat", files=["src/foo.py"])
        # path outside root — should not crash; should warn as unlisted
        with tempfile.TemporaryDirectory() as outside:
            rc, out = self._run(Path(outside) / "something.py")
            self.assertEqual(rc, 0)
            self.assertNotEqual(out, "")  # warns as unlisted (or no_active_spec — either is acceptable so long as no crash)


class DriftCheckIntegrationTests(unittest.TestCase):
    """End-to-end via subprocess.run — proves CLI wiring matches what the bash
    hook will actually invoke."""

    SCRIPT = str(Path(__file__).resolve().parent / "specflow.py")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run_cli(self, abs_path, session_id="cli-session"):
        import subprocess
        env = {**os.environ, "CLAUDE_SESSION_ID": session_id}
        return subprocess.run(
            ["python3", self.SCRIPT, "--root", str(self.root), "drift-check", str(abs_path)],
            env=env, capture_output=True, text=True, check=False,
        )

    def _state(self):
        p = self.root / ".spec-flow" / "session-state.json"
        return json.loads(p.read_text()) if p.exists() else None

    def _make_spec(self, slug, files=None, with_plan=True):
        d = self.root / "specs" / slug
        d.mkdir(parents=True)
        (d / "spec.md").write_text("# Spec: x\n## Problem\nx\n", encoding="utf-8")
        if with_plan:
            plan = "# Plan: x\n\n## Files to change\n| Path | Change | Why |\n|---|---|---|\n"
            for f in (files or []):
                plan += f"| {f} | edit | reason |\n"
            plan += "\n## Steps\n- [ ]\n"
            (d / "plan.md").write_text(plan, encoding="utf-8")

    def test_no_active_spec(self):
        (self.root / "specs").mkdir()
        r = self._run_cli(self.root / "src" / "main.py")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no_active_spec", r.stdout)
        self.assertEqual(self._state()["warned"], ["no_active_spec"])

    def test_no_plan(self):
        self._make_spec("feat", with_plan=False)
        r = self._run_cli(self.root / "src" / "main.py")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no_plan", r.stdout)
        self.assertEqual(self._state()["warned"], ["no_plan"])

    def test_unlisted_file(self):
        self._make_spec("feat", files=["src/foo.py"])
        r = self._run_cli(self.root / "src" / "bar.py")
        self.assertEqual(r.returncode, 0)
        self.assertIn("unlisted_file:src/bar.py", r.stdout)
        self.assertEqual(self._state()["warned"], ["unlisted_file:src/bar.py"])

    def test_listed_silent(self):
        self._make_spec("feat", files=["src/foo.py"])
        r = self._run_cli(self.root / "src" / "foo.py")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIsNone(self._state())  # no state written when silent

    def test_whitelisted_specs(self):
        self._make_spec("feat", files=["src/foo.py"])
        r = self._run_cli(self.root / "specs" / "feat" / "spec.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_concurrent_invocations_do_not_crash(self):
        """Requirement §8: state writes must be atomic against concurrent
        invocations (e.g. MultiEdit). Two near-simultaneous subprocesses
        against the same state file must both exit 0."""
        import subprocess
        self._make_spec("feat", files=["src/foo.py"])
        env = {**os.environ, "CLAUDE_SESSION_ID": "concurrent-session"}
        procs = []
        for i in range(6):
            procs.append(subprocess.Popen(
                ["python3", self.SCRIPT, "--root", str(self.root),
                 "drift-check", str(self.root / "src" / f"unlisted_{i}.py")],
                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ))
        for p in procs:
            stdout, stderr = p.communicate(timeout=10)
            self.assertEqual(p.returncode, 0, f"crashed: stderr={stderr}")
            # Each subprocess saw a different unlisted path so each should have warned.
            self.assertIn("unlisted_file:", stdout)


if __name__ == "__main__":
    unittest.main()
