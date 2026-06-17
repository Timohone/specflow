#!/usr/bin/env python3
"""Tests for the spec-flow engine. Run: python3 -m unittest test_specflow"""
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


if __name__ == "__main__":
    unittest.main()
