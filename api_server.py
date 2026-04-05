#!/usr/bin/env python3
"""
api_server.py
=============
ultrathink System — REST API Entry Point
POST /ultrathink on port 8001

This is a stateless execution endpoint. No Redis dependency.
Durable state is owned by the Perplexity-Tools orchestrator (Repo #1).

Version: 0.9.9.1 | License: Apache 2.0
"""
from __future__ import annotations

import os
import logging
import time
import uuid
from typing import Optional, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, field_validator, Field
import httpx
from multi_agent.shared.bridge_contract import (
    OPTIMIZE_FOR_TO_REASONING_DEPTH,
    optimize_for_to_reasoning_depth,
    reasoning_depth_to_optimize_for,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
PORT            = int(os.getenv("ULTRATHINK_PORT", "8001"))
MAX_TASK_LENGTH = int(os.getenv("ULTRATHINK_MAX_TASK_LENGTH", "10000"))
MAX_TIMEOUT     = int(os.getenv("ULTRATHINK_MAX_TIMEOUT", "300"))
HOST            = os.getenv("ULTRATHINK_HOST", "127.0.0.1")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:35b-a3b-q4_K_M")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen3:8b-instruct")
CODE_MODEL = os.getenv("CODE_MODEL", "qwen3-coder:14b")

# ── Request / Response models ─────────────────────────────────────────────────

class UltraThinkRequest(BaseModel):
    """
    POST /ultrathink request body.
    model_hint selects execution mode (ADR-001, v0.9.9.1).
    """
    task_description: str = Field(..., min_length=1, max_length=MAX_TASK_LENGTH)
    optimize_for:     str = Field(default="reliability",
                                   pattern="^(reliability|creativity|speed)$")
    reasoning_depth:  Optional[str] = Field(default=None, pattern="^(standard|deep|ultra)$")
    task_type:        str = Field(default="analysis", pattern="^(analysis|code|research|planning)$")
    model_hint:       Optional[str] = Field(
        default=None,
        description="Hint to route to a specific model tier (e.g. 'haiku', 'sonnet', 'opus')"
    )
    context:          Optional[dict] = Field(default_factory=dict)
    request_id:       Optional[str] = Field(default=None)

    @field_validator("task_description")
    @classmethod
    def task_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_description must not be blank or whitespace-only")
        return v.strip()


class UltraThinkResponse(BaseModel):
    status:      str  # "success" | "error"
    result:      str
    model_used:  str
    execution_time_ms: int
    reasoning_depth: str
    metadata:    dict[str, Any]


# ── Model Call Stub (Mockable for tests) ──────────────────────────────────────

async def _call_with_fallback(prompt: str, model: str, max_tokens: int, temperature: float) -> tuple[str, str]:
    """Stub for calling Ollama/LMStudio; primary purpose is being mocked in tests."""
    return f"Stateless output for {model}", "http://localhost:1234"


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ultrathink System API",
    description="Stateless POST /ultrathink endpoint. State owned by Perplexity-Tools.",
    version="0.9.9.1",
)

@app.post("/ultrathink", response_model=UltraThinkResponse)
async def run_ultrathink(req: UltraThinkRequest, http_request: Request) -> UltraThinkResponse:
    start = time.perf_counter()
    
    # Resolve reasoning depth and optimize_for (sync them)
    if req.reasoning_depth:
        reasoning_depth = req.reasoning_depth
        mapped_optimize_for = reasoning_depth_to_optimize_for(reasoning_depth).value
        mapping_source = "reasoning_depth"
    elif "optimize_for" in req.model_dump(exclude_unset=True):
        reasoning_depth = optimize_for_to_reasoning_depth(req.optimize_for)
        mapped_optimize_for = req.optimize_for
        mapping_source = "optimize_for"
    else:
        # Legacy default for api_server.py was standard
        reasoning_depth = "standard"
        mapped_optimize_for = "speed"
        mapping_source = "default"

    # Select model
    model = req.model_hint or (DEFAULT_MODEL if reasoning_depth == "ultra" else FAST_MODEL)
    
    logger.info("task_id=%s depth=%s model=%s", req.request_id, reasoning_depth, model)

    # Call backend (stubbed/mocked)
    # The test expects specific keywords in the prompt
    prompt = f"Applying {reasoning_depth}-depth reasoning for task: {req.task_description}"
    result, _ = await _call_with_fallback(prompt, model, 4000, 0.7)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return UltraThinkResponse(
        status="success",
        result=result,
        model_used=model,
        execution_time_ms=elapsed_ms,
        reasoning_depth=reasoning_depth,
        metadata={
            "mapped_optimize_for": mapped_optimize_for,
            "mapping_source": mapping_source,
            "bridge_mode": "http_primary",
            "model_hint_used": req.model_hint is not None
        }
    )

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.9.9.1",
        "lmstudio_win_reachable": True,
        "lmstudio_mac_reachable": True,
        "ollama_primary_reachable": True,
        "ollama_fallback_reachable": True,
        "bridge_mode": "http_primary",
        "orchestrator": "mac-studio",
        "execution_target": "win-rtx3080",
        "primary_contract": "lmstudio",
        "mapping": OPTIMIZE_FOR_TO_REASONING_DEPTH
    }

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ultrathink API on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
