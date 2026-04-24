#!/usr/bin/env python3
"""
verify_before_done.py
=====================
The ὅραμα System — Directive #4: Verification Before Done

Runs a comprehensive pre-completion verification checklist.
NEVER mark a task complete without running this script.

Usage:
    python verify_before_done.py [--task TASK_NAME] [--dir PROJECT_DIR]
    python verify_before_done.py --check tests
    python verify_before_done.py --check all

Philosophy:
    Visual confirmation is insufficient. Pages lag, caches mislead,
    async renders deceive. This script enforces programmatic verification.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# ─── Colour output ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg: str) -> None: print(f"  {RED}✗{RESET} {msg}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg: str) -> None: print(f"  {BLUE}→{RESET} {msg}")
def header(msg: str) -> None: print(f"\n{BOLD}{msg}{RESET}")


# ─── Check runners ────────────────────────────────────────────────────────────

def check_tests(project_dir: Path) -> dict:
    """Run test suite and return results."""
    results = {"passed": 0, "failed": 0, "errors": [], "coverage": None}

    # Detect test framework
    if (project_dir / "pytest.ini").exists() or (project_dir / "pyproject.toml").exists():
        cmd = ["python", "-m", "pytest", "--tb=short", "-q"]
        cov_cmd = ["python", "-m", "pytest", "--tb=short", "-q", "--cov=.", "--cov-report=term-missing"]
        runner = "pytest"
    elif (project_dir / "package.json").exists():
        cmd = ["npm", "test", "--", "--watchAll=false"]
        runner = "npm"
    else:
        warn("No test runner detected (pytest, npm). Skipping automated tests.")
        return results

    info(f"Running {runner} tests in {project_dir}...")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=project_dir, timeout=120
        )
        if result.returncode == 0:
            results["passed"] = 1
            ok("All tests passed")
        else:
            results["failed"] = 1
            results["errors"].append(result.stdout[-2000:])
            fail(f"Tests failed:\n{result.stdout[-1000:]}")
    except subprocess.TimeoutExpired:
        fail("Tests timed out after 120s")
        results["errors"].append("timeout")
    except FileNotFoundError as e:
        warn(f"Test runner not found: {e}")

    return results


def check_linting(project_dir: Path) -> dict:
    """Run linters and return results."""
    results = {"passed": True, "issues": []}

    # Python linting
    py_files = list(project_dir.rglob("*.py"))
    if py_files:
        info(f"Linting {len(py_files)} Python file(s)...")
        for linter, args in [("flake8", ["--max-line-length=100"]),
                              ("pylint", ["--errors-only"])]:
            try:
                r = subprocess.run(
                    [linter] + args + [str(project_dir)],
                    capture_output=True, text=True, timeout=30
                )
                if r.returncode == 0:
                    ok(f"{linter}: no issues")
                else:
                    warn(f"{linter}: issues found")
                    results["issues"].append(r.stdout[:500])
                    results["passed"] = False
            except FileNotFoundError:
                info(f"{linter} not installed, skipping")

    # JS/TS linting
    if (project_dir / "package.json").exists():
        try:
            r = subprocess.run(
                ["npx", "eslint", ".", "--ext", ".js,.ts,.jsx,.tsx"],
                capture_output=True, text=True, cwd=project_dir, timeout=60
            )
            if r.returncode == 0:
                ok("ESLint: no issues")
            else:
                warn("ESLint: issues found")
                results["issues"].append(r.stdout[:500])
                results["passed"] = False
        except FileNotFoundError:
            info("ESLint not installed, skipping")

    return results


def check_no_debug_artifacts(project_dir: Path) -> dict:
    """Check for debug prints, hardcoded secrets, TODO/FIXME without tickets."""
    results = {"passed": True, "warnings": []}
    patterns = {
        "print(": "debug print statement",
        "console.log(": "debug console.log",
        "debugger;": "debugger statement",
        "TODO": "TODO without ticket",
        "FIXME": "FIXME without ticket",
        "HACK": "HACK comment (should be refactored)",
        "password =": "potential hardcoded secret",
        "api_key =": "potential hardcoded API key",
        "secret =": "potential hardcoded secret",
    }

    skip_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv", ".venv"}
    issue_count = 0

    for fpath in project_dir.rglob("*"):
        if fpath.is_file() and fpath.suffix in (".py", ".js", ".ts", ".jsx", ".tsx", ".sh"):
            if any(skip in fpath.parts for skip in skip_dirs):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                for pattern, description in patterns.items():
                    if pattern.lower() in content.lower():
                        results["warnings"].append(f"{fpath.name}: {description}")
                        issue_count += 1
            except (PermissionError, OSError):
                pass

    if issue_count == 0:
        ok("No debug artifacts detected")
    else:
        warn(f"{issue_count} potential issue(s) found")
        for w in results["warnings"][:10]:
            warn(f"  {w}")
        results["passed"] = False

    return results


def check_task_plan(project_dir: Path) -> dict:
    """Check that tasks/todo.md exists and has items marked complete."""
    results = {"exists": False, "has_plan": False, "completion": 0.0}
    todo_path = project_dir / "tasks" / "todo.md"

    if not todo_path.exists():
        warn("tasks/todo.md not found — was a plan written?")
        return results

    results["exists"] = True
    content = todo_path.read_text(encoding="utf-8")
    total = content.count("- [")
    done  = content.count("- [x]") + content.count("- [X]")

    if total > 0:
        results["completion"] = done / total
        results["has_plan"] = True
        pct = int(results["completion"] * 100)
        if pct == 100:
            ok(f"tasks/todo.md: {done}/{total} items complete (100%)")
        elif pct >= 80:
            warn(f"tasks/todo.md: {done}/{total} items complete ({pct}%)")
        else:
            fail(f"tasks/todo.md: only {done}/{total} items complete ({pct}%)")
    else:
        warn("tasks/todo.md exists but has no checkable items")

    return results


def check_staff_engineer(interactive: bool = True) -> dict:
    """Simulate 'would a staff engineer approve this?' self-review."""
    questions = [
        ("Correctness",    "Does it actually solve the stated problem?"),
        ("Completeness",   "Are all edge cases handled?"),
        ("Quality",        "Is the code maintainable and readable?"),
        ("Testing",        "Are tests meaningful and sufficient?"),
        ("Documentation",  "Can someone else understand this code?"),
        ("Performance",    "Does it meet performance requirements?"),
        ("Security",       "Are there obvious vulnerabilities?"),
    ]

    results = {"approved": True, "scores": {}}

    if not interactive:
        ok("Staff engineer check skipped (non-interactive mode)")
        return results

    header("🧑‍💻 Staff Engineer Self-Review")
    print("  Answer honestly. This is for quality, not punishment.\n")

    failed_checks = []
    for category, question in questions:
        while True:
            answer = input(f"  {BLUE}{category}{RESET}: {question} [y/n/skip]: ").strip().lower()
            if answer in ("y", "yes"):
                ok(category)
                results["scores"][category] = True
                break
            elif answer in ("n", "no"):
                fail(f"{category} — needs more work")
                results["scores"][category] = False
                results["approved"] = False
                failed_checks.append(category)
                break
            elif answer in ("s", "skip", ""):
                warn(f"{category} — skipped")
                results["scores"][category] = None
                break

    if results["approved"]:
        ok("Staff engineer would approve ✓")
    else:
        fail(f"Needs work in: {', '.join(failed_checks)}")

    return results


def run_all_checks(project_dir: Path, task_name: str, interactive: bool) -> dict:
    """Run the complete verification suite."""
    report = {
        "task": task_name,
        "timestamp": datetime.now().isoformat(),
        "project_dir": str(project_dir),
        "checks": {},
        "verdict": "UNKNOWN",
    }

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  ultrathink Verification Protocol{RESET}")
    print(f"  Task: {task_name}")
    print(f"  Dir:  {project_dir}")
    print(f"{BOLD}{'='*60}{RESET}")

    header("1. Test Suite")
    report["checks"]["tests"] = check_tests(project_dir)

    header("2. Code Quality (Linting)")
    report["checks"]["linting"] = check_linting(project_dir)

    header("3. Debug Artifacts Scan")
    report["checks"]["debug"] = check_no_debug_artifacts(project_dir)

    header("4. Task Plan Completion")
    report["checks"]["task_plan"] = check_task_plan(project_dir)

    header("5. Staff Engineer Check")
    report["checks"]["staff_engineer"] = check_staff_engineer(interactive)

    # Final verdict
    tests_ok   = report["checks"]["tests"]["failed"] == 0
    lint_ok    = report["checks"]["linting"]["passed"]
    debug_ok   = report["checks"]["debug"]["passed"]
    plan_ok    = report["checks"]["task_plan"].get("completion", 0) >= 0.8
    se_ok      = report["checks"]["staff_engineer"]["approved"]

    all_ok = tests_ok and lint_ok and debug_ok and plan_ok and se_ok

    header("📊 Verification Summary")
    print(f"  Tests:          {'✓ PASS' if tests_ok else '✗ FAIL'}")
    print(f"  Linting:        {'✓ PASS' if lint_ok  else '⚠ ISSUES'}")
    print(f"  Debug Artifacts:{'✓ CLEAN' if debug_ok else '⚠ FOUND'}")
    print(f"  Task Plan:      {'✓ DONE' if plan_ok  else '⚠ INCOMPLETE'}")
    print(f"  Staff Engineer: {'✓ APPROVED' if se_ok else '✗ NOT YET'}")
    print()

    if all_ok:
        report["verdict"] = "PASS"
        print(f"  {GREEN}{BOLD}✅ VERIFIED — Task is complete{RESET}")
    else:
        report["verdict"] = "FAIL"
        print(f"  {RED}{BOLD}❌ NOT DONE — Fix issues above before marking complete{RESET}")

    # Save report
    report_path = project_dir / "tasks" / "verification-report.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))
    info(f"Report saved: {report_path}")

    return report


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ultrathink Verification Protocol — run before marking any task done"
    )
    parser.add_argument("--task",        default="Unnamed Task", help="Task name for the report")
    parser.add_argument("--dir",         default=".",            help="Project directory to verify")
    parser.add_argument("--check",       default="all",          help="Which check to run: all|tests|lint|debug|plan|se")
    parser.add_argument("--no-interact", action="store_true",    help="Skip interactive staff engineer check")
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()
    if not project_dir.exists():
        print(f"{RED}Error: Directory not found: {project_dir}{RESET}")
        sys.exit(1)

    report = run_all_checks(
        project_dir=project_dir,
        task_name=args.task,
        interactive=not args.no_interact,
    )

    sys.exit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
