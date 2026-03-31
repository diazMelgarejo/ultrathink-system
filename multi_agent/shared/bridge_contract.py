#!/usr/bin/env python3
"""
bridge_contract.py
==================
Shared compatibility helpers for keeping the MCP-first contract aligned with
the backup HTTP bridge.
"""
from __future__ import annotations

from multi_agent.shared.ultrathink_core import OptimizeFor


DEFAULT_OPTIMIZE_FOR = OptimizeFor.RELIABILITY
DEFAULT_REASONING_DEPTH = "ultra"

REASONING_DEPTH_TO_OPTIMIZE_FOR = {
    "standard": OptimizeFor.SPEED,
    "deep": OptimizeFor.CREATIVITY,
    "ultra": OptimizeFor.RELIABILITY,
}

OPTIMIZE_FOR_TO_REASONING_DEPTH = {
    optimize_for.value: reasoning_depth
    for reasoning_depth, optimize_for in REASONING_DEPTH_TO_OPTIMIZE_FOR.items()
}

REASONING_DEPTH_STEP_ESTIMATE = {
    "standard": 64,
    "deep": 192,
    "ultra": 384,
}

# Hardware profiles — must match the values PT's /reconcile endpoint expects.
HARDWARE_PROFILE_WIN = "win-rtx3080"
HARDWARE_PROFILE_MAC = "mac-studio"

# Model-id prefix → hardware profile (used by US to tell PT which GPU it's targeting)
_MODEL_PROFILE_PREFIXES: list[tuple[str, str]] = [
    ("qwen3.5:35b", HARDWARE_PROFILE_WIN),
    ("qwen3-coder", HARDWARE_PROFILE_WIN),
    ("qwen3-30b",   HARDWARE_PROFILE_WIN),
    ("qwen3.5-27b", HARDWARE_PROFILE_WIN),
    ("qwen3.5-9b",  HARDWARE_PROFILE_MAC),
    ("qwen3:8b",    HARDWARE_PROFILE_MAC),
]


def model_to_hardware_profile(model_id: str) -> str:
    """
    Return the hardware profile string for a given model ID.
    Falls back to HARDWARE_PROFILE_WIN (the primary GPU node) if unknown.
    """
    lower = model_id.lower()
    for prefix, profile in _MODEL_PROFILE_PREFIXES:
        if lower.startswith(prefix):
            return profile
    return HARDWARE_PROFILE_WIN


def optimize_for_to_reasoning_depth(optimize_for: OptimizeFor | str) -> str:
    key = optimize_for.value if isinstance(optimize_for, OptimizeFor) else str(optimize_for)
    if key not in OPTIMIZE_FOR_TO_REASONING_DEPTH:
        raise ValueError(f"Unknown optimize_for value: {optimize_for}")
    return OPTIMIZE_FOR_TO_REASONING_DEPTH[key]


def reasoning_depth_to_optimize_for(reasoning_depth: str) -> OptimizeFor:
    key = str(reasoning_depth).lower()
    if key not in REASONING_DEPTH_TO_OPTIMIZE_FOR:
        raise ValueError(f"Unknown reasoning_depth value: {reasoning_depth}")
    return REASONING_DEPTH_TO_OPTIMIZE_FOR[key]
