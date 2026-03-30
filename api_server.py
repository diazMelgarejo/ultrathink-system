"""api_server.py - UltraThink REST API (port 8001)

Exposes POST /ultrathink and GET /health so Perplexity-Tools can call the
ultrathink 5-stage reasoning pipeline via HTTP.

Design principles
-----------------
* Stateless - no agent registry, no Redis.  PT owns lifecycle/dedup via
  .state/agents.json before calling this server.
* Graceful degradation - if Ollama is unreachable the endpoint returns an
  error JSON with status="error"; PT then falls back to local Qwen3.5-35B.
* Dependency-minimal - FastAPI + httpx + python-dotenv + slowapi (see
  requirements.txt). No Redis, no agent registry.
* Hardware-agnostic by default - ultrathink does NOT detect hardware itself.
  PT's hardware/SKILL.md owns model assignment per machine profile.
  PT MAY pass model_hint in the request to override the default selection;
  ultrathink honors the hint when provided (ADR-001, v0.9.9.0).

Usage
-----
  pip install fastapi uvicorn httpx python-dotenv slowapi
  python -m uvicorn api_server:app --host 0.0.0.0 --port 8001
"""
import os
import time
import logging
from typing import Any, Dict, Optional
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (all overridable via .env)
# ---------------------------------------------------------------------------
API_PORT = int(os.getenv("API_PORT", "8001"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# Ollama endpoints - prefer the Dell RTX 3080 for heavy models
OLLAMA_PRIMARY = os.getenv("OLLAMA_WINDOWS_ENDPOINT", "http://192.168.1.100:11434")
OLLAMA_FALLBACK = os.getenv("OLLAMA_MAC_ENDPOINT", "http://localhost:11434")

# Model selection per task type (override via env vars)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:35b-a3b-q4_K_M")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen3:8b-instruct")
CODE_MODEL = os.getenv("CODE_MODEL", "qwen3-coder:14b")

# Request timeout (seconds) - deep reasoning can take 60-120 s
# sec: clamp to sane bounds (1-600 s) to prevent misconfiguration
_raw_timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_TIMEOUT = max(1, min(_raw_timeout, 600))

# v0.9.9.0: model_hint support - PT can pass hardware-appropriate model
# v0.9.8.0: rate limiting + input validation + Pydantic V2 field_validator
VERSION = "0.9.9.0"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ultrathink.api")

# ---------------------------------------------------------------------------
# FastAPI app + rate limiter (OWASP API4 - Unrestricted Resource Consumption)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app = FastAPI(
    title="UltraThink API",
    version=VERSION,
    description="Deep-reasoning bridge for Perplexity-Tools orchestrator",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# sec: restrict to known hosts in production (set ALLOWED_HOSTS env var)
_allowed_hosts = os.getenv("ALLOWED_HOSTS", "*")
if _allowed_hosts != "*":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts.split(","))

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class UltraThinkRequest(BaseModel):
    # sec: bounded task_description (OWASP API3 injection + API4 DoS)
    task_description: str = Field(..., min_length=1, max_length=8000, description="What to reason about")
    reasoning_depth: str = Field(
        "standard",
        description="standard | deep | ultra",
        pattern="^(standard|deep|ultra)$",
    )
    task_type: str = Field(
        "analysis",
        description="analysis | code | research | planning",
        pattern="^(analysis|code|research|planning)$",
    )
    context: Optional[str] = Field(None, description="Extra background context", max_length=4000)
    max_tokens: int = Field(4000, ge=256, le=16000)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    # ADR-001 (v0.9.9.0): optional hardware-appropriate model hint from PT.
    # ultrathink is hardware-agnostic by default; PT's hardware/SKILL.md owns
    # model assignment. When model_hint is set, it takes precedence over the
    # internal _select_model() heuristic so PT can route mac-studio requests
    # to MLX-optimised models and win-rtx3080 requests to Ollama GGUF models.
    model_hint: Optional[str] = Field(
        None,
        description="Optional model override from PT hardware layer (e.g. 'qwen3:8b-instruct' for mac-studio)",
        max_length=128,
    )

    @field_validator("task_description", "context", "model_hint", mode="before")
    @classmethod
    def no_null_bytes(cls, v: Optional[str]) -> Optional[str]:
        if v and "\x00" in v:
            raise ValueError("Null bytes not allowed")
        return v


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
    # sec: do NOT expose internal IPs (OWASP API8 Security Misconfiguration)
    ollama_primary_reachable: bool
    ollama_fallback_reachable: bool
    models: Dict[str, str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _select_model(task_type: str, reasoning_depth: str, model_hint: Optional[str] = None) -> str:
    """Pick the best local Ollama model for this task.

    ADR-001 (v0.9.9.0): ultrathink is hardware-agnostic. If PT supplies a
    model_hint (derived from hardware/SKILL.md profile), use it directly.
    This keeps ultrathink's core logic hardware-unaware while still allowing
    PT to exercise optimal hardware-aware model selection.

    Fallback priority (mirrors PERPLEXITY_BRIDGE.md Model Selection Matrix):
      code        -> CODE_MODEL  (qwen3-coder:14b)
      ultra depth -> DEFAULT_MODEL (qwen3.5:35b)
      standard    -> FAST_MODEL  (qwen3:8b) unless depth >= deep
    """
    if model_hint:
        log.info("_select_model: using PT model_hint=%s", model_hint)
        return model_hint
    if task_type == "code":
        return CODE_MODEL
    if reasoning_depth in ("ultra", "deep"):
        return DEFAULT_MODEL
    return FAST_MODEL


def _build_prompt(req: UltraThinkRequest) -> str:
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
    parts.append(f"INSTRUCTION:\n{depth_instructions[req.reasoning_depth]}")
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
    """Try primary Ollama endpoint; fall back to secondary.

    Returns (response_text, endpoint_used).
    """
    for endpoint in [OLLAMA_PRIMARY, OLLAMA_FALLBACK]:
        try:
            text = await _call_ollama(prompt, model, endpoint, max_tokens, temperature)
            return text, endpoint
        except Exception as exc:
            log.warning("Ollama endpoint %s failed: %s", endpoint, exc)
    raise RuntimeError("All Ollama endpoints unreachable")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
async def health(request: Request):
    """Health check - confirms the server is up.

    sec: internal IPs are not exposed; only reachability booleans returned.
    """
    primary_ok = False
    fallback_ok = False
    async with httpx.AsyncClient(timeout=3) as client:
        try:
            r = await client.get(f"{OLLAMA_PRIMARY}/api/tags")
            primary_ok = r.status_code == 200
        except Exception:
            pass
        try:
            r = await client.get(f"{OLLAMA_FALLBACK}/api/tags")
            fallback_ok = r.status_code == 200
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
    )


@app.post("/ultrathink", response_model=UltraThinkResponse)
@limiter.limit("20/minute")
async def ultrathink(req: UltraThinkRequest, request: Request):
    """Deep-reasoning endpoint called by Perplexity-Tools orchestrator.

    Stateless: callers are responsible for deduplication before calling.
    Hardware-agnostic: model selection defers to PT via optional model_hint.
    """
    start = time.monotonic()
    model = _select_model(req.task_type, req.reasoning_depth, req.model_hint)
    prompt = _build_prompt(req)
    log.info(
        "ultrathink | depth=%s task_type=%s model=%s hint=%s tokens=%d",
        req.reasoning_depth,
        req.task_type,
        model,
        req.model_hint or "none",
        req.max_tokens,
    )
    try:
        result, endpoint_used = await _call_with_fallback(
            prompt, model, req.max_tokens, req.temperature
        )
    except RuntimeError as exc:
        log.error("ultrathink failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("ultrathink done | %d ms", elapsed_ms)
    return UltraThinkResponse(
        status="success",
        result=result,
        model_used=model,
        execution_time_ms=elapsed_ms,
        reasoning_depth=req.reasoning_depth,
        # sec: do not expose endpoint_used (contains internal IP)
        metadata={
            "prompt_chars": len(prompt),
            "model_hint_used": req.model_hint is not None,
        },
    )


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
