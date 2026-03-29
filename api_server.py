"""api_server.py — UltraThink REST API (port 8001)

Exposes POST /ultrathink and GET /health so Perplexity-Tools can call the
ultrathink 5-stage reasoning pipeline via HTTP.

Design principles
-----------------
* Stateless — no agent registry, no Redis.  PT owns lifecycle/dedup via
  .state/agents.json before calling this server.
* Graceful degradation — if Ollama is unreachable the endpoint returns an
  error JSON with status="error"; PT then falls back to local Qwen3-30B.
* Dependency-minimal — only FastAPI + httpx + python-dotenv (already in
  requirements.txt or trivially addable).

Usage
-----
  pip install fastapi uvicorn httpx python-dotenv
  python -m uvicorn api_server:app --host 0.0.0.0 --port 8001
"""

import os
import time
import logging
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (all overridable via .env)
# ---------------------------------------------------------------------------
API_PORT = int(os.getenv("API_PORT", "8001"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# Ollama endpoints — prefer the Dell RTX 3080 for heavy models
OLLAMA_PRIMARY = os.getenv("OLLAMA_WINDOWS_ENDPOINT", "http://192.168.1.100:11434")
OLLAMA_FALLBACK = os.getenv("OLLAMA_MAC_ENDPOINT", "http://localhost:11434")

# Model selection per task type (override via env vars)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3:30b-a3b-instruct-q4_K_M")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen3:8b-instruct")
CODE_MODEL = os.getenv("CODE_MODEL", "qwen3-coder:14b")

# Request timeout (seconds) — deep reasoning can take 60-120 s
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# v0.9.7.0 Hardening: Version consistency with Perplexity-Tools
VERSION = "0.9.7.0"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ultrathink.api")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="UltraThink API",
    version=VERSION,
    description="Deep-reasoning bridge for Perplexity-Tools orchestrator",
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class UltraThinkRequest(BaseModel):
    task_description: str = Field(..., min_length=1, description="What to reason about")
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
    context: Optional[str] = Field(None, description="Extra background context")
    max_tokens: int = Field(4000, ge=256, le=16000)
    temperature: float = Field(0.7, ge=0.0, le=1.0)


class UltraThinkResponse(BaseModel):
    status: str
    result: str
    model_used: str
    execution_time_ms: int
    reasoning_depth: str
    metadata: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_primary: str
    ollama_fallback: str
    models: dict


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _select_model(task_type: str, reasoning_depth: str) -> str:
    """Pick the best local Ollama model for this task.

    Priority (mirrors PERPLEXITY_BRIDGE.md Model Selection Matrix):
      code         -> CODE_MODEL  (qwen3-coder:14b)
      ultra depth  -> DEFAULT_MODEL (qwen3:30b)
      standard / fast -> FAST_MODEL (qwen3:8b) unless depth >= deep
    """
    if task_type == "code":
        return CODE_MODEL
    if reasoning_depth == "ultra":
        return DEFAULT_MODEL
    if reasoning_depth == "deep":
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
async def health():
    """Health check — confirms the server is up and shows config."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        ollama_primary=OLLAMA_PRIMARY,
        ollama_fallback=OLLAMA_FALLBACK,
        models={
            "default": DEFAULT_MODEL,
            "fast": FAST_MODEL,
            "code": CODE_MODEL,
        },
    )


@app.post("/ultrathink", response_model=UltraThinkResponse)
async def ultrathink(req: UltraThinkRequest):
    """Deep-reasoning endpoint called by Perplexity-Tools orchestrator.

    Stateless: callers are responsible for deduplication before calling.
    """
    start = time.monotonic()
    model = _select_model(req.task_type, req.reasoning_depth)
    prompt = _build_prompt(req)
    log.info(
        "ultrathink | depth=%s task_type=%s model=%s tokens=%d",
        req.reasoning_depth,
        req.task_type,
        model,
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
    log.info("ultrathink done | %d ms via %s", elapsed_ms, endpoint_used)
    return UltraThinkResponse(
        status="success",
        result=result,
        model_used=model,
        execution_time_ms=elapsed_ms,
        reasoning_depth=req.reasoning_depth,
        metadata={
            "endpoint_used": endpoint_used,
            "prompt_chars": len(prompt),
        },
    )


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
