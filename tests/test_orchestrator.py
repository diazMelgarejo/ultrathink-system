#!/usr/bin/env python3
"""
Unit tests for the ultrathink orchestrator logic and core types.
Run: pytest tests/test_orchestrator.py -v
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "bin" / "shared"))
sys.path.insert(0, str(ROOT / "bin" / "agents" / "orchestrator"))

try:
    from ultrathink_core import (
        ArchitectureOutput,
        AgentMessage,
        ELEGANCE_THRESHOLD,
        MessageType,
        OptimizeFor,
        QUALITY_RUBRIC_WEIGHTS,
        Stage,
        TaskState,
        ValidationResult,
        Verdict,
        calculate_elegance_score,
    )
    from orchestrator_logic import advance_stage, create_task_state
    IMPORTS_OK = True
except ImportError as exc:  # pragma: no cover - skip gate below handles this
    IMPORTS_OK = False
    IMPORT_ERROR = str(exc)


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestTaskState:
    def test_default_stage_is_context(self):
        state = TaskState()
        assert state.current_stage == Stage.CONTEXT

    def test_needs_refinement_low_score(self):
        state = TaskState(elegance_score=0.5, iteration_count=0)
        assert state.needs_refinement() is True

    def test_no_refinement_when_score_high(self):
        state = TaskState(elegance_score=0.9, iteration_count=0)
        assert state.needs_refinement() is False

    def test_no_refinement_when_max_iterations(self):
        state = TaskState(elegance_score=0.5, iteration_count=3, max_iterations=3)
        assert state.needs_refinement() is False

    def test_is_done(self):
        state = TaskState(current_stage=Stage.DONE)
        assert state.is_done() is True

    def test_to_dict_has_required_keys(self):
        payload = TaskState().to_dict()
        for key in ["task_id", "current_stage", "elegance_score", "stage_outputs"]:
            assert key in payload

    def test_created_at_is_timezone_aware_utc(self):
        parsed = datetime.fromisoformat(TaskState().created_at)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestEleganceScoring:
    def test_perfect_scores_give_high_elegance(self):
        scores = {key: 1.0 for key in QUALITY_RUBRIC_WEIGHTS}
        assert calculate_elegance_score(scores) == 1.0

    def test_zero_scores_give_zero_elegance(self):
        scores = {key: 0.0 for key in QUALITY_RUBRIC_WEIGHTS}
        assert calculate_elegance_score(scores) == 0.0

    def test_threshold_default_is_0_8(self):
        assert ELEGANCE_THRESHOLD == 0.8

    def test_simplicity_has_highest_weight(self):
        assert QUALITY_RUBRIC_WEIGHTS["simplicity"] == max(QUALITY_RUBRIC_WEIGHTS.values())


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestAgentMessage:
    def test_message_has_auto_ids(self):
        msg = AgentMessage(
            from_agent="orchestrator",
            to_agent="context-agent",
            message_type=MessageType.DELEGATE_TASK,
            payload={"task": "test"},
        )
        assert msg.trace_id
        assert msg.message_id
        assert msg.timestamp

    def test_timestamp_is_timezone_aware_utc(self):
        msg = AgentMessage(
            from_agent="orchestrator",
            to_agent="context-agent",
            message_type=MessageType.DELEGATE_TASK,
            payload={"task": "test"},
        )
        parsed = datetime.fromisoformat(msg.timestamp)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)

    def test_to_dict_has_all_fields(self):
        msg = AgentMessage(
            from_agent="a",
            to_agent="b",
            message_type=MessageType.RESULT_RETURN,
            payload={},
        )
        payload = msg.to_dict()
        for key in ["from_agent", "to_agent", "message_type", "trace_id", "payload"]:
            assert key in payload


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestValidationResult:
    def test_valid_pass_default(self):
        result = ValidationResult(valid=True)
        assert result.verdict == Verdict.PASS
        assert result.issues == []

    def test_invalid_fail(self):
        result = ValidationResult(valid=False, verdict=Verdict.FAIL, issues=["test broke"])
        assert not result.valid
        assert result.to_dict()["verdict"] == Verdict.FAIL


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestOrchestratorLogic:
    def test_create_task_state_uses_context_stage(self):
        state = create_task_state("Design a PT-first migration", OptimizeFor.RELIABILITY)
        assert state.task_description == "Design a PT-first migration"
        assert state.current_stage == Stage.CONTEXT

    def test_advance_stage_requires_refinement_before_execution(self):
        state = create_task_state("Refine a gateway design")
        state.current_stage = Stage.ARCHITECTURE

        updated = advance_stage(
            state,
            stage_output={"blueprint": "v1"},
            elegance_score=0.4,
        )

        assert updated.current_stage == Stage.REFINEMENT
        assert updated.iteration_count == 1
        assert updated.stage_outputs[Stage.ARCHITECTURE.value]["blueprint"] == "v1"

    def test_advance_stage_moves_to_done_after_pass(self):
        state = create_task_state("Ship the orchestrator")
        state.current_stage = Stage.VERIFICATION

        validated = advance_stage(
            state,
            validation=ValidationResult(valid=True, verdict=Verdict.PASS),
        )
        assert validated.current_stage == Stage.CRYSTALLIZATION

        done = advance_stage(validated, stage_output={"summary": "done"})
        assert done.current_stage == Stage.DONE
        assert done.completed_at


class TestExamplesExist:
    def test_financial_validator_example(self):
        example = ROOT / "examples" / "financial-validator"
        assert (example / "README.md").exists()
        assert (example / "task.md").exists()
        assert (example / "output" / "validate_financial_data.py").exists()

    def test_financial_validator_has_function(self):
        code = (
            ROOT
            / "examples"
            / "financial-validator"
            / "output"
            / "validate_financial_data.py"
        ).read_text(encoding="utf-8")
        assert "def validate_equity_data" in code
        assert "ValidationReport" in code
        assert "PASS" in code and "FAIL" in code
