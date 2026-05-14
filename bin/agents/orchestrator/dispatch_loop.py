"""bin/agents/orchestrator/dispatch_loop.py — orama plan executor.

Drives a TaskPlan through the ultrathink stage sequence using OramaToPTBridge.
Each stage fires its workers (parallel within a stage, sequential across stages).
The verifier gate is enforced by the bridge before crystallization.

Architecture (per unified-absorption-plan.md § 5.5):
  orama task plan
      │  dispatch_loop.run_plan()
      ▼
  OramaToPTBridge.dispatch_{parallel,worker,crystallization}()
      │  PT contracts
      ▼
  PT OrchestrationSupervisor → hardware-routed worker

This module is stateless — it holds no persistent state between calls.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from bin.agents.dispatcher import OramaToPTBridge
from bin.agents.orchestrator.task_schema import PlanResult, StageSpec, TaskPlan, WorkerSpec


# ── Internal helpers ──────────────────────────────────────────────────────────

def _group_workers(workers: List[WorkerSpec]):
    """Yield batches of WorkerSpec.  Workers with the same parallel_group
    are yielded together; ungrouped workers are yielded one at a time."""
    batch: List[WorkerSpec] = []
    current_group: Optional[str] = None

    for w in workers:
        if w.parallel_group is not None:
            if w.parallel_group == current_group:
                batch.append(w)
            else:
                if batch:
                    yield batch
                batch = [w]
                current_group = w.parallel_group
        else:
            if batch:
                yield batch
                batch = []
                current_group = None
            yield [w]  # solo worker

    if batch:
        yield batch


async def _run_stage(
    bridge: OramaToPTBridge,
    stage: StageSpec,
    verification_result: Any = None,
) -> Dict[str, Any]:
    """Execute one stage.

    For the crystallization stage, passes the verification_result to the bridge
    so the gate check can happen.  For other stages, runs workers in batches.
    """
    stage_output: Dict[str, Any] = {}

    if stage.stage == "crystallization":
        # Verifier gate: bridge raises PermissionError if not approved
        if not stage.workers:
            # No explicit crystallizer spec — use the stage prompt from rubric
            prompt = stage.rubric or "Crystallize and present the final output."
        else:
            prompt = stage.workers[0].prompt
        result = await bridge.dispatch_crystallization(
            prompt=prompt,
            verification_result=verification_result,
            metadata={"stage": "crystallization"},
        )
        stage_output["crystallization"] = result
        return stage_output

    # All other stages: batch workers by parallel_group
    for batch in _group_workers(stage.workers):
        if len(batch) == 1:
            w = batch[0]
            result = await bridge.dispatch_worker(
                role=w.role,
                intent=w.intent,
                prompt=w.prompt,
                specialization=w.specialization,
                backend_hint=w.backend_hint,
                metadata={"stage": stage.stage, **w.metadata},
                constraints=list(w.constraints),
            )
            stage_output[w.role] = result
        else:
            # Parallel batch
            worker_dicts = [
                {
                    "role": w.role,
                    "intent": w.intent,
                    "prompt": w.prompt,
                    "specialization": w.specialization,
                    "backend_hint": w.backend_hint,
                    "metadata": {"stage": stage.stage, **w.metadata},
                    "constraints": list(w.constraints),
                }
                for w in batch
            ]
            results = await bridge.dispatch_parallel(worker_dicts)
            for w, result in zip(batch, results):
                stage_output[w.role] = result

    return stage_output


# ── Public API ────────────────────────────────────────────────────────────────

async def run_plan(plan: TaskPlan) -> PlanResult:
    """Execute a TaskPlan end-to-end.

    Stages run sequentially.  Workers within a stage run in parallel batches.
    The verifier gate blocks crystallization if verification did not pass.

    Returns a PlanResult with per-stage outputs and the final crystallized text.
    Errors are accumulated — individual stage failures do not abort the run
    unless they raise PermissionError (verifier gate) or RuntimeError.
    """
    bridge = OramaToPTBridge(
        session_id=plan.session_id,
        parent_orchestrator_id=plan.parent_orchestrator_id,
    )

    all_stage_outputs: Dict[str, Any] = {}
    errors: List[str] = []
    verification_result: Any = None
    final_output: Optional[str] = None
    verdict: Optional[str] = None

    for stage in plan.stages:
        try:
            stage_out = await _run_stage(
                bridge,
                stage,
                verification_result=verification_result,
            )
            all_stage_outputs[stage.stage] = stage_out

            # Extract verification result from the verification stage output
            if stage.stage == "verification":
                verifier_output = next(iter(stage_out.values()), {})
                # If PT returns a structured VerificationResult, use it.
                # If it returns a raw dict with "verdict", wrap it.
                if hasattr(verifier_output, "verdict"):
                    verification_result = verifier_output
                    verdict = verifier_output.verdict
                else:
                    # Minimal duck-type wrapper for raw dict output
                    class _VR:
                        def __init__(self, d: Dict[str, Any]) -> None:
                            self.verdict = d.get("verdict", "needs_revision")
                            self.findings = d.get("findings", [])
                    verification_result = _VR(verifier_output)
                    verdict = verification_result.verdict

            elif stage.stage == "crystallization":
                crystal_out = stage_out.get("crystallization", {})
                final_output = crystal_out.get("output")

        except PermissionError as exc:
            # Hard stop — verifier gate violation.  Do not continue.
            errors.append(f"[GATE BLOCKED] {exc}")
            break

        except Exception as exc:
            errors.append(f"[{stage.stage}] {exc}")
            # Non-fatal: continue to next stage with degraded context

    return PlanResult(
        plan_id=plan.plan_id,
        session_id=plan.session_id,
        objective=plan.objective,
        stage_outputs=all_stage_outputs,
        final_output=final_output,
        verdict=verdict,
        errors=errors,
    )
