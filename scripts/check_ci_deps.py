#!/usr/bin/env python3
"""
scripts/check_ci_deps.py
========================
Pre-commit guard: prevents CI ModuleNotFoundError failures caused by
workflow files that skip the package's declared dependencies.

Checks:
  1. pyproject.toml has [project.optional-dependencies] with a 'test' group
  2. All GitHub Actions workflow files install via '.[test]' (not bare pytest/tomli)
  3. Key runtime modules that the test suite imports are importable right now

Run manually:  python scripts/check_ci_deps.py
Pre-commit:    configured in .pre-commit-config.yaml
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"

# ── Modules that MUST be importable for the test suite to run ─────────────────
REQUIRED_MODULES = [
    "fastapi",
    "httpx",
    "uvicorn",
    "pydantic",
    "slowapi",
    "pytest",
]

# ── Patterns that MUST appear in every workflow install step ──────────────────
FORBIDDEN_PATTERNS = [
    # Old pattern that bypasses pyproject.toml deps
    "pip install pytest pytest-asyncio tomli",
    "pip install pytest hatchling build tomli",
]
REQUIRED_PATTERN = ".[test]"

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"


def check_pyproject_test_extras() -> list[str]:
    """Ensure pyproject.toml declares [project.optional-dependencies] test group."""
    errors = []
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        with open(ROOT / "pyproject.toml", "rb") as f:
            cfg = tomllib.load(f)

        extras = cfg.get("project", {}).get("optional-dependencies", {})
        if "test" not in extras:
            errors.append(
                "pyproject.toml is missing [project.optional-dependencies] test group. "
                "Add: [project.optional-dependencies]\\ntest = [\"pytest>=8.0.0\", ...]"
            )
        else:
            print(f"  {PASS} pyproject.toml has [test] extras ({len(extras['test'])} packages)")
    except Exception as exc:
        errors.append(f"Could not parse pyproject.toml: {exc}")
    return errors


def check_workflow_install_patterns() -> list[str]:
    """Verify every workflow uses '.[test]' for pip install, not bare pytest."""
    errors = []
    if not WORKFLOWS_DIR.exists():
        return errors

    for yml in WORKFLOWS_DIR.glob("*.yml"):
        text = yml.read_text()
        for bad in FORBIDDEN_PATTERNS:
            if bad in text:
                errors.append(
                    f"{yml.name}: found forbidden install pattern '{bad}'. "
                    f"Replace with: pip install \".[test]\""
                )
        if "pip install" in text and REQUIRED_PATTERN not in text:
            # Only warn if it's doing a project install at all
            if 'pip install .' in text or 'pip install ".' in text or "pip install '." in text:
                errors.append(
                    f"{yml.name}: pip install step detected but '.[test]' pattern not found. "
                    f"Use: pip install \".[test]\" to ensure all deps are pulled."
                )
        else:
            if "pip install" in text:
                print(f"  {PASS} {yml.name}: uses '.[test]' install pattern")

    return errors


def check_importable_modules() -> list[str]:
    """Verify runtime modules the test suite depends on are importable."""
    errors = []
    for mod in REQUIRED_MODULES:
        if importlib.util.find_spec(mod) is None:
            errors.append(
                f"Module '{mod}' is NOT importable in current environment. "
                f"Run: pip install \".[test]\""
            )
        else:
            print(f"  {PASS} import {mod}")
    return errors


def main() -> int:
    print("=" * 60)
    print("CI Dependency Guard — pre-commit check")
    print("=" * 60)

    all_errors: list[str] = []

    print("\n[1/3] pyproject.toml test extras")
    all_errors += check_pyproject_test_extras()

    print("\n[2/3] GitHub Actions workflow install patterns")
    all_errors += check_workflow_install_patterns()

    print("\n[3/3] Runtime module imports")
    all_errors += check_importable_modules()

    print()
    if all_errors:
        print(f"\033[31m{'─' * 60}\033[0m")
        print(f"\033[31mFAILED — {len(all_errors)} issue(s) found:\033[0m")
        for i, err in enumerate(all_errors, 1):
            print(f"  {i}. {err}")
        print(f"\033[31m{'─' * 60}\033[0m")
        return 1

    print(f"\033[32m{'─' * 60}\033[0m")
    print("\033[32mPASSED — CI dependency guard: all checks green\033[0m")
    print(f"\033[32m{'─' * 60}\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
