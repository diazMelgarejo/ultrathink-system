# Lessons — Shared Knowledge Base

> **Canonical path**: `.claude/lessons/LESSONS.md`
> **Purpose**: GitHub-auditable persistent memory across all ECC, AutoResearcher, and Claude sessions.
>
> **Rules**:
> - Read this file at the start of every session
> - Append new learnings before ending a session
> - Keep entries dated and agent-tagged

## continuous-learning-v2

This repo uses [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).
Instincts: `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`
Import command: `/instinct-import .claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`

---

## Sessions Log

<!-- Append entries below. Format:
## YYYY-MM-DD — <agent: ECC | AutoResearcher | Claude> — <brief topic>
### What was learned
### Decisions made
### Open questions
-->

---

## 2026-04-06 — Claude — CI: ModuleNotFoundError for fastapi / hatchling backend missing

### What Went Wrong
Two cascading CI failures caused by a single refactor of the CI dependency install step:

**Failure 1 — `ModuleNotFoundError: No module named 'fastapi'`**
- The original install step was: `pip install . pytest hatchling build tomli`
- This was refactored to `pip install ".[test]" build` to consolidate deps via `[test]` extras
- BUT `[test]` extras had not yet been added to `pyproject.toml` at that point
- Result: fastapi, uvicorn, slowapi, httpx were all missing on the CI runner

**Failure 2 — `Backend 'hatchling.build' is not available`**
- When `[test]` extras were added on the next commit, `hatchling` was not included
- The old `pip install .` step had `hatchling` listed explicitly; the refactor silently dropped it
- `python -m build` needs `hatchling` pre-installed in the active env (not just in `build-system.requires`, which only applies to isolated builds)
- Result: build step failed immediately after test step passed

### Root Cause
**Refactoring a pip install line without first verifying the target extras group contains ALL previously explicit packages.**
The pattern: replacing `pip install pkg1 pkg2 pkg3` with `pip install ".[extras]"` carries an implicit assumption that `[extras]` lists everything `pkg1 pkg2 pkg3` provided. That assumption was not verified.

### Prevention Rules (encoded in `scripts/check_ci_deps.py` + `.pre-commit-config.yaml`)

1. **Never replace an explicit `pip install` with `.[extras]` without first auditing every removed package into the extras group.**
2. **`hatchling` MUST always be in `[project.optional-dependencies] test`** — it is required for `python -m build` to run outside of isolated mode, which is what `test-package-install.py` does with `--no-isolation`.
3. **`pyproject.toml` MUST have a `[project.optional-dependencies]` section with a `test` group** — verified by `scripts/check_ci_deps.py` on every commit touching `.py`, `.yaml`, or `.toml` files.
4. **CI workflow files MUST use `pip install ".[test]"` pattern** — never bare `pip install pytest ...` which bypasses package-declared deps.
5. **All 8 required modules must be importable at commit time**: `fastapi`, `httpx`, `uvicorn`, `pydantic`, `slowapi`, `pytest`, `hatchling`, `build`.

### What Was Added
- `scripts/check_ci_deps.py` — pre-commit guard that enforces all 5 rules above
- `.pre-commit-config.yaml` — `ci-deps-guard` hook runs on every Python/YAML/TOML change
- `pyproject.toml` — `[project.optional-dependencies] test` now includes `hatchling>=1.26.0` and `build>=1.2.0`

### Commit Trail
- `f078c8a` — introduced the gap (refactored install, dropped hatchling implicitly)
- `9653cfc` — added ci-deps-guard pre-commit hook
- `710fc47` — added hatchling+build to [test] extras (final fix)

---
