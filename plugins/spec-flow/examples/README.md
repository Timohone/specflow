# Worked example

A complete spec + plan for a small feature, so you can see the format `spec-flow`
produces before running it yourself.

- [`specs/api-rate-limit/spec.md`](specs/api-rate-limit/spec.md) — the spec (note the testable acceptance criteria).
- [`specs/api-rate-limit/plan.md`](specs/api-rate-limit/plan.md) — the plan (every criterion maps to a step/test).

In a real project these live under `specs/<slug>/` in your repo root. This folder
mirrors that layout, so you can point the engine at it with `--root .`:

```bash
# from this examples/ directory
python3 ../scripts/specflow.py --root . status
python3 ../scripts/specflow.py --root . progress api-rate-limit
python3 ../scripts/specflow.py --root . validate api-rate-limit
```

Expected: `api-rate-limit` shows `2/5` acceptance criteria and `2/6` plan steps —
counted deterministically from the checkboxes, not guessed.
