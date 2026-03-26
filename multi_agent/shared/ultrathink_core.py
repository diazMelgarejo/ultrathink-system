#!/usr/bin/env python3
"""
ultrathink_core.py
==================
Shared types, constants, and base classes for the ultrathink multi_agent system.
Version: 0.9.4.3 | License: Apache 2.0

This is the single source of truth for data contracts between agents.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


# ── Enumerations ──────────────────────────────────────────────────────────────

class Stage(str, Enum):
    CONTEXT       = "context_immersion"
    ARCHITECTURE  = "architecture"
    REFINEMENT    = "refinement"
    EXECUTION     = "execution"
    VERIFICATION  = "verification"
    CRYSTALLIZATION = "crystallization"
    DONE          = "done"

class MessageType(str, Enum):
    DELEGATE_TASK      = "delegate_task"
    RESULT_RETURN      = "result_return"
    REFINEMENT_REQUEST = "refinement_request"
    STATUS_UPDATE      = "status_update"
    ABORT              = "abort"

class Verdict(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    WARNING = "WARNING"

class OptimizeFor(str, Enum):
    RELIABILITY = "reliability"
    CREATIVITY  = "creativity"
    SPEED       = "speed"


# ── Core data types ───────────────────────────────────────────────────────────

@dataclass
class AgentMessage:
    """Message passed between agents via the message bus."""
    from_agent:   str
    to_agent:     str
    message_type: MessageType
    payload:      dict[str, Any]
    trace_id:     str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id:   str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    priority:     str = "medium"  # high | medium | low
    metadata:     dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "message_id":   self.message_id,
            "timestamp":    self.timestamp,
            "from_agent":   self.from_agent,
            "to_agent":     self.to_agent,
            "message_type": self.message_type,
            "trace_id":     self.trace_id,
            "priority":     self.priority,
            "payload":      self.payload,
            "metadata":     self.metadata,
        }


@dataclass
class TaskState:
    """Shared task state persisted in state manager across all agents."""
    task_id:           str = field(default_factory=lambda: str(uuid.uuid4()))
    task_description:  str = ""
    optimize_for:      OptimizeFor = OptimizeFor.RELIABILITY
    current_stage:     Stage = Stage.CONTEXT
    iteration_count:   int = 0
    max_iterations:    int = 3
    elegance_score:    float = 0.0
    elegance_threshold: float = 0.8
    stage_outputs:     dict[str, Any] = field(default_factory=dict)
    agents_active:     list[dict] = field(default_factory=list)
    lessons_learned:   list[dict] = field(default_factory=list)
    created_at:        str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at:      Optional[str] = None

    def needs_refinement(self) -> bool:
        return (
            self.elegance_score < self.elegance_threshold
            and self.iteration_count < self.max_iterations
        )

    def is_done(self) -> bool:
        return self.current_stage == Stage.DONE

    def to_dict(self) -> dict:
        return {
            "task_id":           self.task_id,
            "task_description":  self.task_description,
            "optimize_for":      self.optimize_for,
            "current_stage":     self.current_stage,
            "iteration_count":   self.iteration_count,
            "max_iterations":    self.max_iterations,
            "elegance_score":    self.elegance_score,
            "elegance_threshold": self.elegance_threshold,
            "stage_outputs":     self.stage_outputs,
            "agents_active":     self.agents_active,
            "lessons_learned":   self.lessons_learned,
            "created_at":        self.created_at,
            "completed_at":      self.completed_at,
        }


@dataclass
class ValidationResult:
    """Structured result from verifier agent."""
    valid:      bool
    verdict:    Verdict = Verdict.PASS
    confidence: float = 1.0
    issues:     list[str] = field(default_factory=list)
    warnings:   list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid":      self.valid,
            "verdict":    self.verdict,
            "confidence": self.confidence,
            "issues":     self.issues,
            "warnings":   self.warnings,
        }


@dataclass
class ContextOutput:
    """Output from the context immersion agent."""
    context_summary:    str
    constraints:        list[str]
    existing_patterns:  list[str]
    historical_lessons: list[dict]
    confidence:         float

    def to_dict(self) -> dict:
        return {
            "context_summary":    self.context_summary,
            "constraints":        self.constraints,
            "existing_patterns":  self.existing_patterns,
            "historical_lessons": self.historical_lessons,
            "confidence":         self.confidence,
        }


@dataclass
class ArchitectureOutput:
    """Output from the architect agent."""
    blueprint:      dict[str, Any]
    elegance_score: float
    interfaces:     dict[str, Any]
    edge_cases:     list[str]

    def needs_refinement(self, threshold: float = 0.8) -> bool:
        return self.elegance_score < threshold

    def to_dict(self) -> dict:
        return {
            "blueprint":      self.blueprint,
            "elegance_score": self.elegance_score,
            "interfaces":     self.interfaces,
            "edge_cases":     self.edge_cases,
        }


# ── Constants ─────────────────────────────────────────────────────────────────

ELEGANCE_THRESHOLD   = 0.8
MAX_REFINEMENT_LOOPS = 3
MAX_EXECUTOR_AGENTS  = 5
MAX_NESTING_DEPTH    = 3
CONTEXT_CONFIDENCE_MIN = 0.7

QUALITY_RUBRIC_WEIGHTS = {
    "simplicity":       5,
    "readability":      5,
    "maintainability":  4,
    "robustness":       4,
    "test_coverage":    4,
    "performance":      3,
}

def calculate_elegance_score(rubric_scores: dict[str, float]) -> float:
    """Weighted average of rubric scores → elegance score 0.0–1.0."""
    weights = QUALITY_RUBRIC_WEIGHTS
    weighted_sum = sum(rubric_scores.get(k, 0.5) * w for k, w in weights.items())
    total_weight = sum(weights.values())
    return round(weighted_sum / total_weight, 3)
