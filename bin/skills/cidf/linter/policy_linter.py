"""
linter/policy_linter.py
────────────────────────
Policy linter for Content Insertion Decision Framework v1.2.

Rejects any Decision that violates the framework's five lint rules.
Use this in CI pipelines, agent pre-execution hooks, or unit tests.

Usage:
    from linter.policy_linter import lint, LintError
    errors = lint(decision, task, env)
    if errors:
        raise LintError(errors)
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from typing import List

from core.content_insertion_framework import Decision, Task, Env, automation_justified


# ─── Lint result ──────────────────────────────────────────────────────────────

@dataclass
class LintViolation:
    rule_id: str
    message: str
    severity: str = "error"   # "error" | "warning"


class LintError(Exception):
    def __init__(self, violations: List[LintViolation]) -> None:
        self.violations = violations
        lines = [f"  [{v.rule_id}] {v.message}" for v in violations]
        super().__init__("Policy lint failed:\n" + "\n".join(lines))


# ─── Tool complexity map ──────────────────────────────────────────────────────

_TOOL_COMPLEXITY: dict[str, int] = {
    "direct_form_input": 1,
    "direct_typing":     2,
    "clipboard_paste":   2,
    "file_upload":       3,
    "scripting":         5,
}


def _min_eligible_complexity(task: Task, env: Env) -> int:
    """Return complexity of the lowest-rank method currently eligible."""
    if env.field_accessible and task.content_length_chars <= env.max_safe_chars_form_input:
        return 1
    if env.editor_visible and task.content_length_chars <= env.max_safe_chars_typing:
        return 2
    if env.paste_supported:
        return 2
    if env.upload_available:
        return 3
    return 5  # scripting only


def _any_simple_method_eligible(task: Task, env: Env) -> bool:
    return _min_eligible_complexity(task, env) < 5


# ─── Lint rules ───────────────────────────────────────────────────────────────

def lint(decision: Decision, task: Task, env: Env) -> List[LintViolation]:
    """
    Run all lint rules. Returns list of violations (empty = clean).
    """
    violations: List[LintViolation] = []

    # LINT-001: Scripting chosen while simpler methods are available
    if decision.chosen_tool == "scripting" and _any_simple_method_eligible(task, env):
        violations.append(LintViolation(
            rule_id="LINT-001",
            message=(
                f"Scripting chosen but simpler method eligible "
                f"(min eligible complexity: {_min_eligible_complexity(task, env)}). "
                "Iterate from rank 1 first."
            ),
        ))

    # LINT-002: verification_required must always be True
    if not decision.verification_required:
        violations.append(LintViolation(
            rule_id="LINT-002",
            message="verification_required is False or missing. Verification is mandatory and cannot be disabled.",
        ))

    # LINT-003: Complexity bias — chosen tool is more complex than necessary
    chosen_complexity = _TOOL_COMPLEXITY.get(decision.chosen_tool, 99)
    min_complexity    = _min_eligible_complexity(task, env)
    if chosen_complexity > min_complexity:
        violations.append(LintViolation(
            rule_id="LINT-003",
            message=(
                f"Complexity bias: chosen '{decision.chosen_tool}' (complexity={chosen_complexity}) "
                f"but a simpler method is eligible (min complexity={min_complexity})."
            ),
        ))

    # LINT-004: Scripting chosen for one-time static task
    if decision.chosen_tool == "scripting" and task.is_one_time and task.content_static:
        violations.append(LintViolation(
            rule_id="LINT-004",
            message=(
                "Scripting gate is CLOSED: task is one-time and content is static. "
                "Use the simplest eligible method instead."
            ),
        ))

    # LINT-005: No fallback defined when failure is plausible
    # At minimum, warn if chosen tool has no fallback and the env may fail
    if not decision.fallback_chain and decision.chosen_tool != "scripting":
        violations.append(LintViolation(
            rule_id="LINT-005",
            message=(
                f"No fallback_chain defined for chosen tool '{decision.chosen_tool}'. "
                "Add at least one fallback to handle verification failure."
            ),
            severity="warning",
        ))

    return violations


def lint_strict(decision: Decision, task: Task, env: Env) -> None:
    """
    Raises LintError if any violations are found (including warnings in strict mode).
    Use this as a pre-execution guard in production agents.
    """
    violations = lint(decision, task, env)
    if violations:
        raise LintError(violations)


def lint_errors_only(decision: Decision, task: Task, env: Env) -> None:
    """
    Raises LintError only for error-severity violations.
    Warnings are returned but do not block execution.
    """
    violations = [v for v in lint(decision, task, env) if v.severity == "error"]
    if violations:
        raise LintError(violations)
