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
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, field_validator, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
PORT            = int(os.getenv("ULTRATHINK_PORT", "8001"))
MAX_TASK_LENGTH = int(os.getenv("ULTRATHINK_MAX_TASK_LENGTH", "10000"))
MAX_TIMEOUT     = int(os.getenv("ULTRATHINK_MAX_TIMEOUT", "300"))
HOST            = os.getenv("ULTRATHINK_HOST", "127.0.0.1")  # never 0.0.0.0 in prod


# ── Request / Response models ─────────────────────────────────────────────────

class UltraThinkRequest(BaseModel):
    """
    POST /ultrathink request body.
    model_hint selects execution mode (ADR-001, v0.9.9.1).
    """
    task_description: str = Field(..., min_length=1, max_length=MAX_TASK_LENGTH)
    optimize_for:     str = Field(default="reliability",
                                   pattern="^(reliability|creativity|speed)$")
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

    @field_validator("model_hint")
    @classmethod
    def model_hint_allowed_values(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"haiku", "sonnet", "opus", "fast", "balanced", "powerful"}
        if v.lower() not in allowed:
            raise ValueError(f"model_hint must be one of {sorted(allowed)}")
        return v.lower()


class UltraThinkResponse(BaseModel):
    request_id:  str
    status:      str  # "accepted" | "error"
    task_id:     str
    message:     str
    mode:        str  # "mode1" | "mode2" | "mode3"
    elapsed_ms:  float


# ── Mode router ───────────────────────────────────────────────────────────────

def route_to_mode(request: UltraThinkRequest) -> str:
    """
    Select execution mode based on task complexity signals.
    Mirrors the SKILL.md Mode Router logic.
    """
    desc = request.task_description.lower()
    word_count = len(desc.split())

    # Simple heuristics — the SKILL.md router has full rules
    if word_count <= 10 and request.model_hint in (None, "haiku", "fast"):
        return "mode1"
    elif word_count <= 50 or request.optimize_for == "speed":
        return "mode2"
    else:
        return "mode3"


# ── App ───────────────────────────────────────────────────────────────────────

def create_app() -> "FastAPI":
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

    app = FastAPI(
        title="ultrathink System API",
        description="Stateless POST /ultrathink endpoint. State owned by Perplexity-Tools.",
        version="0.9.9.1",
        docs_url="/docs",
        redoc_url=None,
    )

    @app.post("/ultrathink", response_model=UltraThinkResponse)
    async def run_ultrathink(request: UltraThinkRequest, http_request: Request) -> UltraThinkResponse:
        start = time.perf_counter()
        req_id = request.request_id or str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        mode = route_to_mode(request)

        logger.info(
            "task=%s mode=%s optimize=%s len=%d",
            task_id, mode, request.optimize_for, len(request.task_description)
        )

        # Stateless: no persistence here.
        # Perplexity-Tools (Repo #1) owns durable state via its own store.
        elapsed = (time.perf_counter() - start) * 1000

        return UltraThinkResponse(
            request_id=req_id,
            status="accepted",
            task_id=task_id,
            message=f"Task accepted for {mode} execution. optimize_for={request.optimize_for}",
            mode=mode,
            elapsed_ms=round(elapsed, 2),
        )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "version": "0.9.9.1", "stateless": True}

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("Install deps: pip install fastapi uvicorn pydantic")
        exit(1)
    app = create_app()
    logger.info("Starting ultrathink API on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
