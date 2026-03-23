#!/usr/bin/env python3
"""
test_orchestrator.py
====================
Unit tests for the ultrathink orchestrator logic and core types.
Run: pytest tests/test_orchestrator.py -v
"""
import sys
import pytest
from pathlib import Path

# Add shared to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "multi_agent" / "shared"))

try:
    from ultrathink_core import (
        TaskState, AgentMessage, ValidationResult, ArchitectureOutput,
        Stage, MessageType, Verdict, OptimizeFor,
        calculate_elegance_score, ELEGANCE_THRESHOLD, QUALITY_RUBRIC_WEIGHTS
    )
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


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
        d = TaskState().to_dict()
        for key in ["task_id", "current_stage", "elegance_score", "stage_outputs"]:
            assert key in d


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestEleganceScoring:
    def test_perfect_scores_give_high_elegance(self):
        scores = {k: 1.0 for k in QUALITY_RUBRIC_WEIGHTS}
        assert calculate_elegance_score(scores) == 1.0

    def test_zero_scores_give_zero_elegance(self):
        scores = {k: 0.0 for k in QUALITY_RUBRIC_WEIGHTS}
        assert calculate_elegance_score(scores) == 0.0

    def test_threshold_default_is_0_8(self):
        assert ELEGANCE_THRESHOLD == 0.8

    def test_simplicity_has_highest_weight(self):
        weights = QUALITY_RUBRIC_WEIGHTS
        assert weights["simplicity"] == max(weights.values())


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestAgentMessage:
    def test_message_has_auto_ids(self):
        msg = AgentMessage(
            from_agent="orchestrator",
            to_agent="context-agent",
            message_type=MessageType.DELEGATE_TASK,
            payload={"task": "test"}
        )
        assert msg.trace_id
        assert msg.message_id
        assert msg.timestamp

    def test_to_dict_has_all_fields(self):
        msg = AgentMessage(
            from_agent="a", to_agent="b",
            message_type=MessageType.RESULT_RETURN,
            payload={}
        )
        d = msg.to_dict()
        for key in ["from_agent", "to_agent", "message_type", "trace_id", "payload"]:
            assert key in d


@pytest.mark.skipif(not IMPORTS_OK, reason="shared module import failed")
class TestValidationResult:
    def test_valid_pass_default(self):
        r = ValidationResult(valid=True)
        assert r.verdict == Verdict.PASS
        assert r.issues == []

    def test_invalid_fail(self):
        r = ValidationResult(valid=False, verdict=Verdict.FAIL, issues=["test broke"])
        assert not r.valid
        d = r.to_dict()
        assert d["verdict"] == Verdict.FAIL


class TestExamplesExist:
    def test_financial_validator_example(self):
        example = Path(__file__).parent.parent / "examples" / "financial-validator"
        assert (example / "README.md").exists()
        assert (example / "task.md").exists()
        assert (example / "output" / "validate_financial_data.py").exists()

    def test_financial_validator_has_function(self):
        code = (Path(__file__).parent.parent / "examples" / "financial-validator" /
                "output" / "validate_financial_data.py").read_text()
        assert "def validate_equity_data" in code
        assert "ValidationReport" in code
        assert "PASS" in code and "FAIL" in code
