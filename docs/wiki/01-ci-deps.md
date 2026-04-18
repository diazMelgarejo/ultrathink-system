# 01. CI Dependencies — pip extras + hatchling guard

**TL;DR:** Never replace `pip install pkg1 pkg2 pkg3` with `pip install ".[extras]"` without first auditing that every removed package is listed in the target extras group. `hatchling` must always be in `[test]` extras.

---

## Root Cause

Two cascading failures from a single CI refactor (2026-04-06):

1. `ModuleNotFoundError: No module named 'fastapi'` — `[test]` extras not yet added to `pyproject.toml` when the install command was changed
2. `Backend 'hatchling.build' is not available` — `hatchling` was in the old explicit install but silently dropped when extras were added; `python -m build` needs it pre-installed in the active env (not just `build-system.requires`, which only applies to isolated builds)

---

## Fix

`pyproject.toml`:
```toml
[project.optional-dependencies]
test = [
  "pytest>=8.0.0",
  "pytest-asyncio>=0.23.0",
  "hatchling>=1.26.0",
  "build>=1.2.0",
  "tomli>=2.0.0",
]
```

CI workflow:
```yaml
- name: Install dependencies
  run: pip install ".[test]" build
```

Pre-commit guard (`scripts/check_ci_deps.py`): verifies all 8 required modules are importable before commit.

---

## Verification

```bash
# All 8 must import cleanly
python -c "import fastapi, httpx, uvicorn, pydantic, slowapi, pytest, hatchling, build"

# Build must succeed
python -m build --no-isolation
```

---

## Rules

1. **Never replace explicit `pip install` with `.[extras]` without auditing** every dropped package into the extras group
2. **`hatchling` MUST always be in `[project.optional-dependencies] test`**
3. **CI workflow files MUST use `pip install ".[test]"` pattern** — never bare `pip install pytest ...`
4. **Pre-commit `check_ci_deps.py`** runs on every `.py`, `.yaml`, `.toml` change

---

## Related

- [Session log 2026-04-06](../LESSONS.md#2026-04-06--claude--ci-modulenotfounderror-for-fastapi--hatchling-backend-missing)
- Commits: `f078c8a` (gap), `9653cfc` (guard), `710fc47` (fix)
