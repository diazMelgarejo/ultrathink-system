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
