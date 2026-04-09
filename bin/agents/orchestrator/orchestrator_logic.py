#!/usr/bin/env python3
"""
Baseline orchestration helpers for the ultrathink multi-agent network.

This module intentionally stays lightweight: it encodes the stage machine and
task-state transitions that the higher-level PT orchestrator can delegate into,
without re-owning any gateway or runtime discovery logic.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from datetime import datetime

_SHARED_DIR = Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from ultrathink_core import OptimizeFor, Stage, TaskState, ValidationResult, Verdict


STAGE_SEQUENCE = [
    Stage.CONTEXT,
    Stage.ARCHITECTURE,
    Stage.REFINEMENT,
    Stage.EXECUTION,
    Stage.VERIFICATION,
    Stage.CRYSTALLIZATION,
    Stage.DONE,
]


def create_task_state(
    task_description: str,
    optimize_for: OptimizeFor = OptimizeFor.RELIABILITY,
) -> TaskState:
    """Create the canonical initial task state for a new ultrathink run."""
    return TaskState(
        task_description=task_description.strip(),
        optimize_for=optimize_for,
        current_stage=Stage.CONTEXT,
    )


def record_stage_output(
    state: TaskState,
    *,
    stage: Stage,
    output: dict[str, Any],
) -> TaskState:
    """Persist one stage output into the shared task state."""
    state.stage_outputs[stage.value] = output
    return state


def advance_stage(
    state: TaskState,
    *,
    stage_output: dict[str, Any] | None = None,
    elegance_score: float | None = None,
    validation: ValidationResult | None = None,
) -> TaskState:
    """Advance the task state through the standard ultrathink stage machine."""
    current_stage = state.current_stage

    if stage_output is not None:
        record_stage_output(state, stage=current_stage, output=stage_output)

    if elegance_score is not None:
        state.elegance_score = elegance_score

    if current_stage == Stage.CONTEXT:
        state.current_stage = Stage.ARCHITECTURE
        return state

    if current_stage in (Stage.ARCHITECTURE, Stage.REFINEMENT):
        if state.needs_refinement():
            state.iteration_count += 1
            state.current_stage = Stage.REFINEMENT
            return state
        state.current_stage = Stage.EXECUTION
        return state

    if current_stage == Stage.EXECUTION:
        state.current_stage = Stage.VERIFICATION
        return state

    if current_stage == Stage.VERIFICATION:
        if validation is not None:
            record_stage_output(
                state,
                stage=Stage.VERIFICATION,
                output=validation.to_dict(),
            )
            if validation.verdict == Verdict.FAIL:
                state.current_stage = Stage.EXECUTION
                return state
        state.current_stage = Stage.CRYSTALLIZATION
        return state

    if current_stage == Stage.CRYSTALLIZATION:
        state.current_stage = Stage.DONE
        state.completed_at = state.completed_at or datetime.utcnow().isoformat()
        return state

    return state
