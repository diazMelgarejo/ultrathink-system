#!/usr/bin/env python3
"""api_server.py - UltraThink REST API (port 8001)

Exposes POST /ultrathink and GET /health so Perplexity-Tools can call the
ultrathink 5-stage reasoning pipeline via HTTP.

Design principles
-----------------
* MCP remains the primary bridge contract.
* This server is the in-repo HTTP backup bridge.
* Stateless - no agent registry, no Redis. PT owns lifecycle/dedup via
  .state/agents.json before calling this server.
* Graceful degradation - if Ollama is unreachable the endpoint returns an
  error JSON with status="error"; PT then falls back to local models.
* Hardware-agnostic by default - ultrathink does NOT detect hardware itself.
  PT's hardware/SKILL.md owns model assignment per machine profile.
  PT MAY pass model_hint in the request to override the default selection.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from multi_agent.shared.bridge_contract import (
    OPTIMIZE_FOR_TO_REASONING_DEPTH,
    optimize_for_to_reasoning_depth,
    reasoning_depth_to_optimize_for,
)

load_dotenv()


API_PORT = int(os.getenv("API_PORT", "8001"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

OLLAMA_PRIMARY = os.getenv("OLLAMA_WINDOWS_ENDPOINT", "http://192.168.1.100:11434")
OLLAMA_FALLBACK = os.getenv("OLLAMA_MAC_ENDPOINT", "http://localhost:11434")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:35b-a3b-q4_K_M")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen3:8b-instruct")
CODE_MODEL = os.getenv("CODE_MODEL", "qwen3-coder:14b")

_raw_timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_TIMEOUT = max(1, min(_raw_timeout, 600))

VERSION = "0.9.9.0"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ultrathink.api")


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app = FastAPI(
    title="UltraThink API",
    version=VERSION,
    description=(
        "Backup compatibility HTTP bridge for Perplexity-Tools. "
        "MCP remains the primary contract."
    ),
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "*")
if _allowed_hosts != "*":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts.split(","))


class UltraThinkRequest(BaseModel):
    task_description: str = Field(..., min_length=1, max_length=8000, description="What to reason about")
    reasoning_depth: str = Field(
        "standard",
        description="standard | deep | ultra",
        pattern="^(standard|deep|ultra)$",
    )
    optimize_for: Optional[str] = Field(
        None,
        description="Optional MCP-style optimization target",
        pattern="^(reliability|creativity|speed)$",
    )
    task_type: str = Field(
        "analysis",
        description="analysis | code | research | planning",
        pattern="^(analysis|code|research|planning)$",
    )
    context: Optional[str] = Field(None, description="Extra background context", max_length=4000)
    max_tokens: int = Field(4000, ge=256, le=16000)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    model_hint: Optional[str] = Field(
        None,
        description="Optional model override from PT hardware layer",
        max_length=128,
    )

    @field_validator("task_description", "context", "model_hint", mode="before")
    @classmethod
    def no_null_bytes(cls, value: Optional[str]) -> Optional[str]:
        if value and "\x00" in value:
            raise ValueError("Null bytes not allowed")
        return value


class UltraThinkResponse(BaseModel):
    status: str
    result: str
    model_used: str
    execution_time_ms: int
    reasoning_depth: str
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_primary_reachable: bool
    ollama_fallback_reachable: bool
    models: Dict[str, str]
    bridge_mode: str
    primary_contract: str
    http_endpoint: str
    mapping: Dict[str, str]


def _resolve_contract_fields(req: UltraThinkRequest) -> tuple[str, str, str]:
    """Normalize HTTP reasoning_depth and MCP optimize_for into one contract."""
    explicit_fields = req.model_fields_set

    if "reasoning_depth" in explicit_fields:
        reasoning_depth = req.reasoning_depth
        mapping_source = "reasoning_depth"
    elif req.optimize_for is not None:
        reasoning_depth = optimize_for_to_reasoning_depth(req.optimize_for)
        mapping_source = "optimize_for"
    else:
        reasoning_depth = req.reasoning_depth
        mapping_source = "default"

    optimize_for = reasoning_depth_to_optimize_for(reasoning_depth).value
    return reasoning_depth, optimize_for, mapping_source


def _select_model(task_type: str, reasoning_depth: str, model_hint: Optional[str] = None) -> str:
    """Pick the best local Ollama model for this task."""
    if model_hint:
        log.info("_select_model: using PT model_hint=%s", model_hint)
        return model_hint
    if task_type == "code":
        return CODE_MODEL
    if reasoning_depth in ("ultra", "deep"):
        return DEFAULT_MODEL
    return FAST_MODEL


def _build_prompt(req: UltraThinkRequest, reasoning_depth: str) -> str:
    """Compose an ultrathink-style prompt from the request."""
    depth_instructions = {
        "standard": "Provide a clear, well-structured response.",
        "deep": (
            "Apply the ultrathink 5-stage methodology: "
            "(1) Context Immersion, (2) Visionary Architecture, "
            "(3) Ruthless Refinement, (4) Masterful Execution, "
            "(5) Crystallize Vision."
        ),
        "ultra": (
            "Apply full ultrathink ultra-depth reasoning. "
            "Break the problem into sub-components, reason from first principles, "
            "challenge every assumption, then synthesize the most elegant solution. "
            "Show your reasoning steps explicitly."
        ),
    }
    parts = []
    if req.context:
        parts.append(f"CONTEXT:\n{req.context}\n")
    parts.append(f"TASK ({req.task_type.upper()}):\n{req.task_description}\n")
    parts.append(f"INSTRUCTION:\n{depth_instructions[reasoning_depth]}")
    return "\n".join(parts)


async def _call_ollama(prompt: str, model: str, endpoint: str, max_tokens: int, temperature: float) -> str:
    """POST to Ollama /api/generate; raise on error."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        resp = await client.post(f"{endpoint}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")


async def _call_with_fallback(prompt: str, model: str, max_tokens: int, temperature: float) -> tuple[str, str]:
    """Try primary Ollama endpoint; fall back to secondary."""
    for endpoint in [OLLAMA_PRIMARY, OLLAMA_FALLBACK]:
        try:
            text = await _call_ollama(prompt, model, endpoint, max_tokens, temperature)
            return text, endpoint
        except Exception as exc:
            log.warning("Ollama endpoint %s failed: %s", endpoint, exc)
    raise RuntimeError("All Ollama endpoints unreachable")


@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
async def health(request: Request):
    """Health check for the backup HTTP bridge."""
    primary_ok = False
    fallback_ok = False
    async with httpx.AsyncClient(timeout=3) as client:
        try:
            response = await client.get(f"{OLLAMA_PRIMARY}/api/tags")
            primary_ok = response.status_code == 200
        except Exception:
            pass
        try:
            response = await client.get(f"{OLLAMA_FALLBACK}/api/tags")
            fallback_ok = response.status_code == 200
        except Exception:
            pass
    return HealthResponse(
        status="ok",
        version=VERSION,
        ollama_primary_reachable=primary_ok,
        ollama_fallback_reachable=fallback_ok,
        models={
            "default": DEFAULT_MODEL,
            "fast": FAST_MODEL,
            "code": CODE_MODEL,
        },
        bridge_mode="http_backup",
        primary_contract="mcp",
        http_endpoint="/ultrathink",
        mapping=OPTIMIZE_FOR_TO_REASONING_DEPTH,
    )


@app.post("/ultrathink", response_model=UltraThinkResponse)
@limiter.limit("20/minute")
async def ultrathink(req: UltraThinkRequest, request: Request):
    """Deep-reasoning endpoint called by Perplexity-Tools orchestrator."""
    started_at = time.monotonic()
    reasoning_depth, optimize_for, mapping_source = _resolve_contract_fields(req)
    model = _select_model(req.task_type, reasoning_depth, req.model_hint)
    prompt = _build_prompt(req, reasoning_depth)

    log.info(
        "ultrathink | depth=%s task_type=%s model=%s hint=%s tokens=%d mapping=%s",
        reasoning_depth,
        req.task_type,
        model,
        req.model_hint or "none",
        req.max_tokens,
        mapping_source,
    )
    try:
        result, _ = await _call_with_fallback(
            prompt, model, req.max_tokens, req.temperature
        )
    except RuntimeError as exc:
        log.error("ultrathink failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))

    elapsed_ms = int((time.monotonic() - started_at) * 1000)
    log.info("ultrathink done | %d ms", elapsed_ms)
    return UltraThinkResponse(
        status="success",
        result=result,
        model_used=model,
        execution_time_ms=elapsed_ms,
        reasoning_depth=reasoning_depth,
        metadata={
            "prompt_chars": len(prompt),
            "model_hint_used": req.model_hint is not None,
            "bridge_mode": "http_backup",
            "primary_contract": "mcp",
            "mapped_optimize_for": optimize_for,
            "mapping_source": mapping_source,
            "endpoint_used": "redacted",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
