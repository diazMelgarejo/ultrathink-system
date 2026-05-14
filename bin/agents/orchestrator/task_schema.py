"""bin/agents/orchestrator/task_schema.py — orama-side task schema definitions.

These are orama's internal planning types — NOT the shared PT contracts.
They describe the PLAN that orama builds for a task before dispatching to PT.

Ownership (per unified-absorption-plan.md § 5):
  - PT owns: JobSpec, TaskEnvelope, WorkerResult, VerificationResult (runtime types)
  - orama owns: TaskPlan, StageSpec, WorkerSpec (planning types — this file)

orama imports the PT shared types for dispatch; it never re-defines them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Worker spec (one role assignment in a plan) ───────────────────────────────

class WorkerSpec(BaseModel):
    """One worker role assignment within a stage plan.

    Built by orama's stage planner before dispatch.  When dispatched, orama
    passes these fields to OramaToPTBridge.dispatch_worker().
    """
    model_config = ConfigDict(frozen=True)

    role: str
    intent: str
    prompt: str
    specialization: Optional[str] = None
    backend_hint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    parallel_group: Optional[str] = None   # workers with the same group run together


# ── Stage spec (one ultrathink stage) ────────────────────────────────────────

class StageSpec(BaseModel):
    """One stage in the ultrathink pipeline.

    Stages are sequential within a task plan.  Workers within a stage may be
    parallel (same parallel_group) or sequential (no group).
    """
    model_config = ConfigDict(frozen=True)

    stage: Literal[
        "context",
        "architecture",
        "refinement",
        "execution",
        "verification",
        "crystallization",
    ]
    workers: List[WorkerSpec] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    rubric: Optional[str] = None   # passed to verifier worker as the evaluation rubric


# ── Task plan (the full orama plan for one user request) ─────────────────────

class TaskPlan(BaseModel):
    """orama's complete plan for one user request.

    Produced by the planner.  Consumed by dispatch_loop.run_plan().
    Not persisted — orama is stateless.  PT persists job results.
    """
    model_config = ConfigDict(frozen=True)

    plan_id: str
    session_id: str
    parent_orchestrator_id: str
    objective: str
    optimize_for: Literal["speed", "quality", "reasoning"] = "quality"
    stages: List[StageSpec] = Field(default_factory=list)
    global_constraints: List[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @field_validator("stages", mode="before")
    @classmethod
    def stages_must_be_ordered(cls, v: List[StageSpec]) -> List[StageSpec]:
        """Ensure stages appear in a valid ultrathink order."""
        _order = [
            "context", "architecture", "refinement",
            "execution", "verification", "crystallization",
        ]
        names = [s.stage if isinstance(s, StageSpec) else s.get("stage", "") for s in v]
        prev_idx = -1
        for name in names:
            if name not in _order:
                continue
            cur_idx = _order.index(name)
            if cur_idx < prev_idx:
                raise ValueError(
                    f"Stage '{name}' appears out of order. "
                    f"Ultrathink stages must follow: {_order}"
                )
            prev_idx = cur_idx
        return v


# ── Plan result (what dispatch_loop returns after running a plan) ─────────────

class PlanResult(BaseModel):
    """Summary of a completed task plan execution.

    Returned by dispatch_loop.run_plan().  Contains per-stage outputs and
    the final crystallized output (if crystallization stage was included).
    """
    model_config = ConfigDict(frozen=True)

    plan_id: str
    session_id: str
    objective: str
    stage_outputs: Dict[str, Any] = Field(default_factory=dict)
    final_output: Optional[str] = None      # content of the crystallization output
    verdict: Optional[str] = None           # "approved" | "needs_revision" | "failed"
    errors: List[str] = Field(default_factory=list)
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
