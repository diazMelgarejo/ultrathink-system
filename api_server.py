#!/usr/bin/env python3
"""api_server.py - UltraThink REST API (port 8001)

Exposes POST /ultrathink and GET /health so Perplexity-Tools can call the
ultrathink 5-stage reasoning pipeline via HTTP.

Design principles
-----------------
* HTTP bridge is the v1.0 RC transport; MCP-optional transport is planned for v1.1+.
* This server is the active HTTP bridge for v1.0 RC (not a backup — it is the transport).
* Stateless - no agent registry, no Redis. PT owns lifecycle/dedup via
  .state/agents.json before calling this server.
* Graceful degradation - if all backends are unreachable the endpoint returns an
  error JSON with status="error"; PT then falls back to local models.
* Mac is the default orchestrator originator: PT + US api_server both run on Mac.
  All heavy reasoning roles (coder, checker, refiner, executor, verifier) are
  dispatched to Windows (LM Studio Win or OLLAMA_PRIMARY) by default.
  Mac (LM Studio Mac or OLLAMA_FALLBACK) is used only when Windows is busy or unreachable,
  or when the task is explicitly routed to mac-studio via model_hint or PT reconcile.
* PT MAY pass model_hint to override the default Windows-first selection.
* Backend priority: LM Studio Win → LM Studio Mac → Ollama Win → Ollama Mac.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

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
    model_to_hardware_profile,
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

# PT reconcile endpoint — US calls this before spawning to check GPU contention.
# If PT is unreachable the call is skipped (graceful degradation).
PT_ENDPOINT = os.getenv("PERPLEXITY_ENDPOINT", "http://localhost:8000")
PT_RECONCILE_TIMEOUT = float(os.getenv("PT_RECONCILE_TIMEOUT", "3"))

# ── LM Studio (v1.0 RC primary backend) ──────────────────────────────────────
LMS_WIN_ENDPOINTS: List[str] = [
    ep.strip()
    for ep in os.getenv("LM_STUDIO_WIN_ENDPOINTS", "http://192.168.1.100:1234").split(",")
    if ep.strip()
]
LMS_MAC_ENDPOINT: str = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_API_TOKEN: str = os.getenv("LM_STUDIO_API_TOKEN", "")
LMS_WIN_MODEL: str = os.getenv("LMS_WIN_MODEL", "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2")
LMS_MAC_MODEL: str = os.getenv("LMS_MAC_MODEL", "Qwen3.5-9B-MLX-4bit")
LMS_MAC_CONTEXT: int = int(os.getenv("LMS_MAC_CONTEXT", "4096"))
_raw_lms_timeout = int(os.getenv("LM_STUDIO_TIMEOUT", "120"))
LMS_TIMEOUT: float = max(1, min(_raw_lms_timeout, 600))

VERSION = "1.0.0-rc"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ultrathink.api")


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app = FastAPI(
    title="UltraThink API",
    version=VERSION,
    description=(
        "HTTP bridge for Perplexity-Tools. "
        "HTTP bridge is the v1.0 RC transport. MCP-optional planned for v1.1+."
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
    lmstudio_win_reachable: bool
    lmstudio_win_count: int
    lmstudio_mac_reachable: bool
    ollama_primary_reachable: bool
    ollama_fallback_reachable: bool
    models: Dict[str, str]
    bridge_mode: str
    orchestrator: str
    execution_target: str
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
    """Pick the best local model for this task."""
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


async def _call_lmstudio(prompt: str, model: str, endpoint: str, max_tokens: int) -> str:
    """POST to LM Studio /api/v1/chat; extract first message-type content."""
    headers = {"Content-Type": "application/json"}
    if LMS_API_TOKEN:
        headers["Authorization"] = f"Bearer {LMS_API_TOKEN}"
    payload: Dict[str, Any] = {"model": model, "input": prompt, "context_length": max_tokens}
    async with httpx.AsyncClient(timeout=LMS_TIMEOUT) as client:
        resp = await client.post(f"{endpoint}/api/v1/chat", json=payload, headers=headers)
        resp.raise_for_status()
        output = resp.json().get("output", [])
    for item in output:
        if item.get("type") == "message":
            return item.get("content", "")
    return " ".join(item.get("content", "") for item in output if item.get("content"))


async def _reconcile_with_pt(session_id: str, model_id: str) -> tuple[bool, Optional[str]]:
    """
    Call PT /reconcile before spawning a GPU session.
    Returns (approved, suggested_model_or_None).
    Gracefully skips (approved=True) if PT is unreachable — US stays stateless.
    """
    hardware_profile = model_to_hardware_profile(model_id)
    payload = {
        "session_id": session_id,
        "model_id": model_id,
        "hardware_profile": hardware_profile,
    }
    try:
        async with httpx.AsyncClient(timeout=PT_RECONCILE_TIMEOUT) as client:
            resp = await client.post(
                f"{PT_ENDPOINT.rstrip('/')}/reconcile", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            approved: bool = data.get("approved", True)
            suggested: Optional[str] = data.get("suggested_model")
            if not approved:
                log.warning(
                    "PT reconcile denied session=%s model=%s profile=%s reason=%s suggested=%s",
                    session_id, model_id, hardware_profile,
                    data.get("reason", ""), suggested,
                )
            else:
                log.info(
                    "PT reconcile approved session=%s model=%s profile=%s",
                    session_id, model_id, hardware_profile,
                )
            return approved, suggested
    except Exception as exc:
        log.debug("PT reconcile unreachable (%s); proceeding without contention check", exc)
        return True, None


async def _call_with_fallback(prompt: str, model: str, max_tokens: int, temperature: float) -> tuple[str, str]:
    """Try LM Studio Win → LM Studio Mac → Ollama primary → Ollama fallback."""
    for ep in LMS_WIN_ENDPOINTS:
        try:
            text = await _call_lmstudio(prompt, LMS_WIN_MODEL, ep, max_tokens)
            return text, ep
        except Exception as exc:
            log.warning("LM Studio Win %s failed: %s", ep, exc)
    try:
        text = await _call_lmstudio(prompt, LMS_MAC_MODEL, LMS_MAC_ENDPOINT, min(max_tokens, LMS_MAC_CONTEXT))
        return text, LMS_MAC_ENDPOINT
    except Exception as exc:
        log.warning("LM Studio Mac failed: %s", exc)
    for endpoint in [OLLAMA_PRIMARY, OLLAMA_FALLBACK]:
        try:
            text = await _call_ollama(prompt, model, endpoint, max_tokens, temperature)
            return text, endpoint
        except Exception as exc:
            log.warning("Ollama endpoint %s failed: %s", endpoint, exc)
    raise RuntimeError("All backends unreachable")


@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
async def health(request: Request):
    """Health check — probes LM Studio (primary) and Ollama (fallback)."""

    async def _lms_ok(endpoint: str) -> bool:
        try:
            headers = {"Authorization": f"Bearer {LMS_API_TOKEN}"} if LMS_API_TOKEN else {}
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{endpoint}/v1/models", headers=headers)
                return r.status_code == 200
        except Exception:
            return False

    async def _ollama_ok(endpoint: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{endpoint}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    win_checks, mac_ok, primary_ok, fallback_ok = await asyncio.gather(
        asyncio.gather(*[_lms_ok(ep) for ep in LMS_WIN_ENDPOINTS]),
        _lms_ok(LMS_MAC_ENDPOINT),
        _ollama_ok(OLLAMA_PRIMARY),
        _ollama_ok(OLLAMA_FALLBACK),
    )
    win_ok = any(win_checks)

    return HealthResponse(
        status="ok",
        version=VERSION,
        lmstudio_win_reachable=win_ok,
        lmstudio_win_count=sum(1 for v in win_checks if v),
        lmstudio_mac_reachable=mac_ok,
        ollama_primary_reachable=primary_ok,
        ollama_fallback_reachable=fallback_ok,
        models={
            "lms_win": LMS_WIN_MODEL,
            "lms_mac": LMS_MAC_MODEL,
            "default": DEFAULT_MODEL,
            "fast": FAST_MODEL,
            "code": CODE_MODEL,
        },
        bridge_mode="http_primary",
        orchestrator="mac-studio",
        execution_target="win-rtx3080",
        primary_contract="lmstudio",
        http_endpoint="/ultrathink",
        mapping=OPTIMIZE_FOR_TO_REASONING_DEPTH,
    )


@app.post("/ultrathink", response_model=UltraThinkResponse)
@limiter.limit("20/minute")
async def ultrathink(req: UltraThinkRequest, request: Request):
    """Deep-reasoning endpoint called by Perplexity-Tools orchestrator."""
    import uuid
    started_at = time.monotonic()
    reasoning_depth, optimize_for, mapping_source = _resolve_contract_fields(req)
    model = _select_model(req.task_type, reasoning_depth, req.model_hint)

    # Close the loop: ask PT to check GPU contention before we spawn.
    # PT may redirect to a lighter model (e.g. mac-studio) if win-rtx3080 is busy.
    session_id = str(uuid.uuid4())
    approved, suggested_model = await _reconcile_with_pt(session_id, model)
    if not approved and suggested_model:
        log.info("PT redirected model %s → %s", model, suggested_model)
        model = suggested_model
    elif not approved:
        raise HTTPException(status_code=503, detail="GPU contention — PT reconcile denied, no fallback model provided")

    prompt = _build_prompt(req, reasoning_depth)

    log.info(
        "ultrathink | depth=%s task_type=%s model=%s hint=%s tokens=%d mapping=%s session=%s",
        reasoning_depth,
        req.task_type,
        model,
        req.model_hint or "none",
        req.max_tokens,
        mapping_source,
        session_id,
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
            "reconcile_session_id": session_id,
            "reconcile_approved": approved,
            "reconcile_redirected": suggested_model is not None and not approved is False,
            "bridge_mode": "http_primary",
            "primary_contract": "lmstudio",
            "mapped_optimize_for": optimize_for,
            "mapping_source": mapping_source,
            "endpoint_used": "redacted",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
