# Contributing to spec-flow

Thanks for your interest! spec-flow is intentionally small and sharp — contributions
that keep it that way are very welcome.

## Ground rules
- Use spec-flow on itself: open a spec under `specs/` for non-trivial changes.
- Keep the workflow fast for the common case; resist feature bloat.
- The engine must stay pure standard-library Python (3.8+), no third-party deps.

## Local development
```bash
cd plugins/spec-flow/scripts
python3 -m unittest test_specflow -v
```
Run the engine against the bundled example:
```bash
cd plugins/spec-flow/examples
python3 ../scripts/specflow.py --root . status
```

## Testing your changes in Claude Code
```bash
/plugin marketplace add /absolute/path/to/spec-flow
/plugin install spec-flow
# restart Claude Code, then exercise /spec → /plan → /build → /verify
```

## Pull requests
- Add a CHANGELOG entry under "Unreleased".
- Add or update tests for engine changes.
- Keep command/agent prompts concise and concrete.
