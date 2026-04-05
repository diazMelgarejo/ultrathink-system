"""
tests/test_conformance.py
──────────────────────────
Conformance test suite for Content Insertion Decision Framework v1.2.

Same 6 test vectors as the TypeScript suite.
Both suites must produce identical results.

Run:
    pytest tests/test_conformance.py -v
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from core.content_insertion_framework import (
    Task, Env, Decision,
    decide, automation_justified, verify, execute_with_fallback,
    Verifier, ExecutionResult,
)
from linter.policy_linter import lint, LintViolation


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _task(**overrides) -> Task:
    defaults = dict(
        task_type="content_insertion",
        is_one_time=True,
        frequency_estimate=1,
        content_static=True,
        requires_transformation=False,
        requires_conditional_logic=False,
        requires_external_integration=False,
        content_length_chars=1_200,
        format_requirements="plain",
        signature="test_signature_abc",
    )
    defaults.update(overrides)
    return Task(**defaults)


def _env(**overrides) -> Env:
    defaults = dict(
        field_accessible=True,
        editor_visible=True,
        paste_supported=True,
        upload_available=False,
        max_safe_chars_form_input=10_000,
        max_safe_chars_typing=5_000,
    )
    defaults.update(overrides)
    return Env(**defaults)


class FakeVerifier:
    """Test double for Verifier protocol."""
    def __init__(self, content_store: str = ""):
        self.content_store = content_store
        self.refresh_called = False

    def refresh_once_if_needed(self) -> None:
        self.refresh_called = True

    def extract_text(self) -> str:
        return self.content_store


# ─── TV-01: Static text, short, field accessible ──────────────────────────────

class TestTV01:
    """TV-01: Static text 2k chars, field accessible → chooses direct_form_input."""

    def setup_method(self):
        self.task = _task(content_length_chars=2_000)
        self.env  = _env(field_accessible=True, editor_visible=True, paste_supported=True)
        self.decision = decide(self.task, self.env)

    def test_chosen_tool(self):
        assert self.decision.chosen_tool == "direct_form_input"

    def test_automation_not_justified(self):
        assert self.decision.automation_justified is False
        assert automation_justified(self.task) is False

    def test_has_fallback(self):
        assert len(self.decision.fallback_chain) > 0

    def test_verification_required(self):
        assert self.decision.verification_required is True

    def test_no_lint_errors(self):
        violations = lint(self.decision, self.task, self.env)
        errors = [v for v in violations if v.severity == "error"]
        assert errors == [], f"Unexpected lint errors: {errors}"


# ─── TV-02: Static text 12k chars, field over limit ───────────────────────────

class TestTV02:
    """TV-02: 12k chars → field skipped (over limit), paste available → clipboard_paste."""

    def setup_method(self):
        self.task = _task(content_length_chars=12_000)
        self.env  = _env(field_accessible=True, editor_visible=False,
                         paste_supported=True, upload_available=True)
        self.decision = decide(self.task, self.env)

    def test_chosen_tool(self):
        assert self.decision.chosen_tool == "clipboard_paste"

    def test_form_input_not_chosen(self):
        assert self.decision.chosen_tool != "direct_form_input"

    def test_scripting_not_chosen(self):
        assert self.decision.chosen_tool != "scripting"

    def test_no_lint_errors(self):
        violations = [v for v in lint(self.decision, self.task, self.env) if v.severity == "error"]
        assert violations == []


# ─── TV-03: Rich text, typing available but paste also available ───────────────

class TestTV03:
    """TV-03: Rich text, editor visible + paste supported → direct_typing (rank 2 over 3)."""

    def setup_method(self):
        self.task = _task(content_length_chars=3_000, format_requirements="rich_text")
        self.env  = _env(field_accessible=False, editor_visible=True,
                         paste_supported=True, upload_available=False)
        self.decision = decide(self.task, self.env)

    def test_chosen_tool(self):
        assert self.decision.chosen_tool == "direct_typing"

    def test_paste_in_fallback(self):
        assert "clipboard_paste" in self.decision.fallback_chain

    def test_no_lint_errors(self):
        violations = [v for v in lint(self.decision, self.task, self.env) if v.severity == "error"]
        assert violations == []


# ─── TV-04: No field/editor/paste, upload available ───────────────────────────

class TestTV04:
    """TV-04: All simple methods blocked except upload → file_upload chosen."""

    def setup_method(self):
        self.task = _task(content_length_chars=4_000)
        self.env  = _env(field_accessible=False, editor_visible=False,
                         paste_supported=False, upload_available=True)
        self.decision = decide(self.task, self.env)

    def test_chosen_tool(self):
        assert self.decision.chosen_tool == "file_upload"

    def test_scripting_not_chosen(self):
        assert self.decision.chosen_tool != "scripting"

    def test_no_lint_errors(self):
        violations = [v for v in lint(self.decision, self.task, self.env) if v.severity == "error"]
        assert violations == []


# ─── TV-05: Repeatable template, conditional logic, field accessible ───────────

class TestTV05:
    """
    TV-05: Repeatable template (20 uses) + conditional logic.
    automation_justified=True, BUT field_accessible=True → still rank 1.
    Scripting should be in fallback, not chosen.
    """

    def setup_method(self):
        self.task = _task(
            is_one_time=False,
            frequency_estimate=20,
            content_static=False,
            requires_conditional_logic=True,
            content_length_chars=500,
        )
        self.env = _env(field_accessible=True, editor_visible=True,
                        paste_supported=True, upload_available=True)
        self.decision = decide(self.task, self.env)

    def test_automation_justified(self):
        assert self.decision.automation_justified is True
        assert automation_justified(self.task) is True

    def test_chosen_tool_is_still_rank1(self):
        # Even when automation is justified, simplest eligible method wins
        assert self.decision.chosen_tool == "direct_form_input"

    def test_scripting_available_as_fallback(self):
        assert "scripting" in self.decision.fallback_chain

    def test_no_lint_errors(self):
        violations = [v for v in lint(self.decision, self.task, self.env) if v.severity == "error"]
        assert violations == []


# ─── TV-06: UI lag — verify without duplicate insert ─────────────────────────

class TestTV06:
    """TV-06: UI lag — must refresh and verify, not re-insert."""

    def setup_method(self):
        self.task = _task(content_length_chars=500, signature="hello_world_marker")
        self.env  = _env(field_accessible=True)
        self.decision = decide(self.task, self.env)

    def test_chosen_tool(self):
        assert self.decision.chosen_tool == "direct_form_input"

    def test_verify_finds_content_after_lag(self):
        # Verifier simulates page with content already present (lag scenario)
        verifier = FakeVerifier(content_store="some text hello_world_marker more text")
        assert verify(verifier, "hello_world_marker") is True
        assert verifier.refresh_called is True

    def test_verify_fails_cleanly_when_absent(self):
        verifier = FakeVerifier(content_store="unrelated content")
        assert verify(verifier, "hello_world_marker") is False

    def test_execute_does_not_duplicate_on_lag(self):
        """
        Simulate: method executes successfully but UI doesn't visually update.
        The execution loop should verify once, confirm success, and NOT retry.
        """
        insert_call_count = [0]

        def fake_insert(content: str) -> None:
            insert_call_count[0] += 1

        # Verifier always returns content as if it was inserted (even on first check)
        verifier = FakeVerifier(content_store="pre-existing hello_world_marker")

        result = execute_with_fallback(
            decision=self.decision,
            executors={"direct_form_input": fake_insert},
            verifier=verifier,
            content="test content",
            signature="hello_world_marker",
        )

        assert result.status == "success"
        assert result.tool == "direct_form_input"
        assert insert_call_count[0] == 1, "Content was inserted more than once (duplicate!)"


# ─── Linter conformance tests ─────────────────────────────────────────────────

class TestLinter:
    """Verify the linter catches all five defined anti-patterns."""

    def test_lint001_scripting_while_simpler_eligible(self):
        task = _task()
        env  = _env(field_accessible=True)
        bad_decision = Decision(
            chosen_tool="scripting",
            fallback_chain=[],
            reason_codes=["forced_bad"],
            automation_justified=True,
        )
        violations = lint(bad_decision, task, env)
        rule_ids = [v.rule_id for v in violations]
        assert "LINT-001" in rule_ids
        assert "LINT-003" in rule_ids  # complexity bias also fires

    def test_lint002_verification_disabled(self):
        task = _task()
        env  = _env()
        decision = decide(task, env)
        decision.verification_required = False  # manually disable
        violations = lint(decision, task, env)
        assert any(v.rule_id == "LINT-002" for v in violations)

    def test_lint004_scripting_for_one_time_static(self):
        task = _task(is_one_time=True, content_static=True, frequency_estimate=1)
        env  = _env(field_accessible=False, editor_visible=False,
                    paste_supported=False, upload_available=False)
        bad_decision = Decision(
            chosen_tool="scripting",
            fallback_chain=[],
            reason_codes=["forced"],
            automation_justified=False,
        )
        violations = lint(bad_decision, task, env)
        assert any(v.rule_id == "LINT-004" for v in violations)

    def test_lint005_no_fallback_warning(self):
        task = _task()
        env  = _env(field_accessible=True, editor_visible=False,
                    paste_supported=False, upload_available=False)
        decision = decide(task, env)
        # Force-clear fallback to trigger warning
        decision.fallback_chain = []
        violations = lint(decision, task, env)
        assert any(v.rule_id == "LINT-005" and v.severity == "warning" for v in violations)

    def test_clean_decision_passes_all_rules(self):
        task = _task()
        env  = _env()
        decision = decide(task, env)
        errors = [v for v in lint(decision, task, env) if v.severity == "error"]
        assert errors == [], f"Clean decision should have zero lint errors; got: {errors}"


# ─── Policy JSON test ─────────────────────────────────────────────────────────

class TestPolicyJSON:
    """Verify the JSON policy file is valid and contains required keys."""

    def test_policy_json_loads(self):
        path = os.path.join(os.path.dirname(__file__), "../core/content_insertion_policy.json")
        with open(path) as f:
            policy = json.load(f)
        assert policy["framework_version"] == "1.2"
        assert "tool_priority_order" in policy
        assert "verification" in policy
        assert "anti_patterns" in policy
        assert "test_vectors" in policy
        assert len(policy["test_vectors"]) == 6

    def test_policy_test_vectors_match_implementation(self):
        """Each test vector's expected_chosen_tool must match decide()."""
        path = os.path.join(os.path.dirname(__file__), "../core/content_insertion_policy.json")
        with open(path) as f:
            policy = json.load(f)

        for tv in policy["test_vectors"]:
            t_data = tv["task"]
            e_data = tv["env"]
            task = Task(
                task_type=t_data.get("task_type", "content_insertion"),
                is_one_time=t_data["is_one_time"],
                frequency_estimate=t_data["frequency_estimate"],
                content_static=t_data["content_static"],
                requires_transformation=t_data["requires_transformation"],
                requires_conditional_logic=t_data["requires_conditional_logic"],
                requires_external_integration=t_data["requires_external_integration"],
                content_length_chars=t_data["content_length_chars"],
                format_requirements=t_data.get("format_requirements", "plain"),
                signature="test",
            )
            env = Env(
                field_accessible=e_data["field_accessible"],
                editor_visible=e_data["editor_visible"],
                paste_supported=e_data["paste_supported"],
                upload_available=e_data["upload_available"],
                max_safe_chars_form_input=e_data.get("max_safe_chars_form_input", 10_000),
                max_safe_chars_typing=e_data.get("max_safe_chars_typing", 5_000),
            )
            result = decide(task, env)
            assert result.chosen_tool == tv["expected_chosen_tool"], (
                f"[{tv['id']}] {tv['description']}: "
                f"expected {tv['expected_chosen_tool']!r}, got {result.chosen_tool!r}"
            )
