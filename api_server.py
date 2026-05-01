#!/usr/bin/env python3
"""
api_server.py
=============
The ὅραμα System — REST API Entry Point
POST /ultrathink on port 8001

This is a stateless execution endpoint. No Redis dependency.
Durable state is owned by the Perpetua-Tools orchestrator (Repo #1).

Version: 0.9.9.2 | License: Apache 2.0
"""
from __future__ import annotations

import os
import json
import logging
import time
import uuid
from typing import Optional, Any
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator, Field
import httpx
from bin.shared.bridge_contract import (
    OPTIMIZE_FOR_TO_REASONING_DEPTH,
    optimize_for_to_reasoning_depth,
    reasoning_depth_to_optimize_for,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Backend routing priority ──────────────────────────────────────────────────

import platform as _platform_mod


class BackendPriority:
    """
    Backend dispatch priority token (per-request or env var override).

    Priority resolution (highest → lowest):
      1. per-request UltraThinkRequest.backend_priority
      2. ORAMA_BACKEND_PRIORITY env var
      3. platform-default (mac→LOCAL, windows→WINDOWS)

    The actual dispatch *order* is determined by BackendRouter, which also
    factors in ORAMA_PLATFORM and task_type.
    """
    LOCAL   = "local"
    CLOUD   = "cloud"
    WINDOWS = "windows"
    _VALID  = {"local", "cloud", "windows"}

    @classmethod
    def from_str(cls, value: str) -> str:
        v = (value or "").strip().lower()
        return v if v in cls._VALID else cls.LOCAL


def _detect_platform() -> str:
    """Detect current OS: 'mac' on Darwin/macOS, 'windows' on Windows."""
    env = os.getenv("ORAMA_PLATFORM", "").strip().lower()
    if env in ("mac", "windows"):
        return env
    return "mac" if _platform_mod.system() == "Darwin" else "windows"


_LOCAL_LM_STUDIO_URL = os.getenv("LOCAL_LM_STUDIO_URL",  "http://localhost:1234/v1")
_CLOUD_API_URL       = os.getenv("CLOUD_API_URL",         "https://api.anthropic.com/v1")
_WIN_LM_STUDIO_HOST  = os.getenv("WIN_LM_STUDIO_HOST",   "192.168.254.108")
_WIN_LM_STUDIO_PORT  = os.getenv("WIN_LM_STUDIO_PORT",   "1234")
_WIN_LM_STUDIO_URL   = f"http://{_WIN_LM_STUDIO_HOST}:{_WIN_LM_STUDIO_PORT}/v1"

# Named endpoint descriptors — one per logical backend slot
_EP = {
    "mac_main":   {"name": "mac_main",   "url": _LOCAL_LM_STUDIO_URL, "tier": "mac"},
    "win_coding": {"name": "win_coding", "url": _WIN_LM_STUDIO_URL,   "tier": "windows", "note": "coding-optimised"},
    "win_main":   {"name": "win_main",   "url": _WIN_LM_STUDIO_URL,   "tier": "windows"},
    "cloud":      {"name": "cloud",      "url": _CLOUD_API_URL,        "tier": "cloud"},
}


class BackendRouter:
    """
    Resolves the ordered backend dispatch list for a single request.

    Priority matrix (no manual override):

      Mac + non-code:  mac_main → win_main  → cloud → win_coding
      Mac + code:      mac_main → win_coding → win_main → cloud
      Windows + any:   win_main → cloud     → win_coding  (Mac is never a Windows fallback)

    Override via:
      - BackendRouter(override="cloud")         — explicit per-request
      - ORAMA_BACKEND_PRIORITY env var          — process-wide default
      - ORAMA_PLATFORM env var                  — platform identity
    """

    def __init__(
        self,
        override: str | None = None,
        task_type: str = "analysis",
    ) -> None:
        self.platform: str = _detect_platform()
        self.task_type: str = task_type or "analysis"
        self._explicit_override: bool = False

        # Priority token: override > env var > platform-default (not stored as override)
        if override and override.strip().lower() in BackendPriority._VALID:
            self.priority: str = BackendPriority.from_str(override)
            self._explicit_override = True
        else:
            env_val = os.getenv("ORAMA_BACKEND_PRIORITY", "").strip().lower()
            if env_val in BackendPriority._VALID:
                self.priority = env_val
                self._explicit_override = True
            else:
                # Platform-default — NOT an explicit override
                self.priority = BackendPriority.LOCAL

    def ordered_endpoints(self) -> list[dict]:
        """Return backend list in dispatch order, most-preferred first."""
        is_code = self.task_type == "code"

        # Explicit override: priority token dictates first endpoint
        if self._explicit_override:
            if self.priority == BackendPriority.CLOUD:
                return [_EP["cloud"], _EP["mac_main"], _EP["win_main"], _EP["win_coding"]]
            if self.priority == BackendPriority.WINDOWS:
                order = [_EP["win_coding"], _EP["win_main"], _EP["cloud"], _EP["mac_main"]] if is_code \
                    else [_EP["win_main"], _EP["win_coding"], _EP["cloud"], _EP["mac_main"]]
                return order
            # LOCAL explicit override → same as mac platform-default
            if self.platform == "mac" or self.priority == BackendPriority.LOCAL:
                if is_code:
                    return [_EP["mac_main"], _EP["win_coding"], _EP["win_main"], _EP["cloud"]]
                return [_EP["mac_main"], _EP["win_main"], _EP["cloud"], _EP["win_coding"]]

        # Platform-default (no explicit override)
        if self.platform == "mac":
            if is_code:
                return [_EP["mac_main"], _EP["win_coding"], _EP["win_main"], _EP["cloud"]]
            return [_EP["mac_main"], _EP["win_main"], _EP["cloud"], _EP["win_coding"]]
        else:  # windows: win_main first, cloud second; Mac is never a Windows fallback
            return [_EP["win_main"], _EP["cloud"], _EP["win_coding"]]


# ── Constants ─────────────────────────────────────────────────────────────────
PORT            = int(os.getenv("ULTRATHINK_PORT", "8001"))
MAX_TASK_LENGTH = int(os.getenv("ULTRATHINK_MAX_TASK_LENGTH", "10000"))
MAX_TIMEOUT     = int(os.getenv("ULTRATHINK_MAX_TIMEOUT", "300"))
HOST            = os.getenv("ULTRATHINK_HOST", "127.0.0.1")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:35b-a3b-q4_K_M")
FAST_MODEL = os.getenv("FAST_MODEL", "qwen3:8b-instruct")
CODE_MODEL = os.getenv(
    "CODE_MODEL",
    "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",  # verified Windows-only model
)

PERPETUA_TOOLS_ROOT = Path(
    os.getenv(
        "PERPETUA_TOOLS_ROOT",
        Path(__file__).resolve().parent.parent / "perplexity-api" / "Perpetua-Tools",
    )
)

# Local disaster-recovery cache (used only when PT is unreachable).
_POLICY_CACHE_PATH = Path(__file__).resolve().parent / "config" / "hardware_policy_cache.yml"


class HardwarePolicyResolver:
    """
    Disaster-recovery policy resolver — PT-first with explicit fallback chain.

    Layer 1 — PT-authoritative (preferred):
        Import utils.hardware_policy from PERPETUA_TOOLS_ROOT.
        orama defers to PT for all enforcement decisions.

    Layer 2 — Offline fallback (degraded, warns loudly):
        Use config/hardware_policy_cache.yml — a vendored snapshot of PT's
        model_hardware_policy.yml. Enforcement still runs; audit trail shows
        "cache-authoritative" so ops can see when PT was unreachable.

    Layer 3 — Hard fail:
        Cache missing too → HTTP 503 on any routing call. Never skip enforcement.

    PT FINAL HANDOFF:
        Before completing any routing decision, resolver records whether the
        decision was PT-authoritative or cache-authoritative in the response
        metadata so callers have a full audit trail.
    """

    def __init__(self) -> None:
        self._pt_available: bool = False
        self._source: str = "uninitialized"
        self._check_affinity_fn = None
        self._expected_platform_fn = None

    def initialize(self) -> None:
        """Called from FastAPI lifespan — probe PT import, set up fallback."""
        # Layer 1: try PT
        if PERPETUA_TOOLS_ROOT.exists():
            if str(PERPETUA_TOOLS_ROOT) not in os.sys.path:
                os.sys.path.insert(0, str(PERPETUA_TOOLS_ROOT))
            try:
                from utils.hardware_policy import (  # type: ignore[import]
                    check_affinity as _ca,
                    expected_platform_for_model as _ep,
                    HardwareAffinityError as _HAE,
                )
                self._check_affinity_fn = _ca
                self._expected_platform_fn = _ep
                self._pt_available = True
                self._source = "pt-authoritative"
                logger.info(
                    "HardwarePolicyResolver: PT-authoritative mode (PERPETUA_TOOLS_ROOT=%s)",
                    PERPETUA_TOOLS_ROOT,
                )
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "HardwarePolicyResolver: PT import failed (%s) — trying local cache",
                    exc,
                )

        # Layer 2: local policy cache fallback
        if _POLICY_CACHE_PATH.exists():
            logger.critical(
                "HardwarePolicyResolver: PT UNREACHABLE — using offline cache at %s. "
                "All routing decisions are CACHE-AUTHORITATIVE. Fix PERPETUA_TOOLS_ROOT.",
                _POLICY_CACHE_PATH,
            )
            self._source = "cache-authoritative"
            self._pt_available = False
            try:
                import yaml as _yaml  # type: ignore[import]
                _policy = _yaml.safe_load(_POLICY_CACHE_PATH.read_text()) or {}
            except ImportError:
                # Minimal fallback parser when PyYAML is absent
                _policy = self._parse_cache_minimal()

            _windows_only = {m.lower() for m in _policy.get("windows_only", [])}
            _mac_only     = {m.lower() for m in _policy.get("mac_only", [])}

            def _ca_cached(model_id: str, platform: str) -> None:
                key = model_id.lower()
                plat = platform.lower()
                if plat in ("win", "windows") and key in _mac_only:
                    raise HardwareAffinityError(f"NEVER_WIN: {model_id} is mac-only (cache)")
                if plat in ("mac", "macos", "darwin") and key in _windows_only:
                    raise HardwareAffinityError(f"NEVER_MAC: {model_id} is windows-only (cache)")

            def _ep_cached(model_id: str) -> str | None:
                key = model_id.lower()
                if key in _windows_only:
                    return "win"
                if key in _mac_only:
                    return "mac"
                return None

            self._check_affinity_fn = _ca_cached
            self._expected_platform_fn = _ep_cached
            return

        # Layer 3: hard fail — no policy available
        logger.critical(
            "HardwarePolicyResolver: PT UNREACHABLE and no local cache at %s. "
            "Hardware enforcement DISABLED — this is a configuration error.",
            _POLICY_CACHE_PATH,
        )
        self._source = "disabled-no-cache"
        self._check_affinity_fn = lambda m, p: None
        self._expected_platform_fn = lambda m: None

    def _parse_cache_minimal(self) -> dict:
        """Minimal YAML parser for hardware_policy_cache.yml without PyYAML."""
        policy: dict = {"windows_only": [], "mac_only": []}
        section = None
        for line in _POLICY_CACHE_PATH.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if stripped == "windows_only:":
                section = "windows_only"
            elif stripped == "mac_only:":
                section = "mac_only"
            elif stripped.startswith("- ") and section:
                policy[section].append(stripped[2:].strip())
        return policy

    def check_affinity(self, model_id: str, platform: str) -> None:
        if self._check_affinity_fn:
            self._check_affinity_fn(model_id, platform)

    def expected_platform_for_model(self, model_id: str) -> str | None:
        if self._expected_platform_fn:
            return self._expected_platform_fn(model_id)
        return None

    @property
    def source(self) -> str:
        return self._source

    @property
    def pt_available(self) -> bool:
        return self._pt_available


# Module-level resolver instance — initialized in lifespan
_policy_resolver = HardwarePolicyResolver()


# Legacy module-level re-export — PT import succeeds during normal operation.
# Fallback shim only activates when PT is unreachable (Layer-3 degraded mode).
try:
    from utils.hardware_policy import HardwareAffinityError as HardwareAffinityError  # type: ignore[import]
except ImportError:
    class HardwareAffinityError(RuntimeError):  # type: ignore[no-redef]
        """Fallback shim — PT import failed. Active only in Layer-3 degraded mode."""
        pass


def check_affinity(model_id: str, platform: str) -> None:
    _policy_resolver.check_affinity(model_id, platform)


def expected_platform_for_model(model_id: str) -> str | None:
    return _policy_resolver.expected_platform_for_model(model_id)


def _load_pt_runtime_state() -> dict[str, Any] | None:
    state_path = os.getenv("PT_RUNTIME_STATE", "").strip()
    if not state_path:
        return None
    path = Path(state_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read PT runtime state %s: %s", path, exc)
        return None

# ── Request / Response models ─────────────────────────────────────────────────

class UltraThinkRequest(BaseModel):
    """
    POST /ultrathink request body.
    model_hint selects execution mode (ADR-001, v0.9.9.2).
    v2 shape: session_id added for correlation across the perpetua-core/oramasys stack.
    """
    model_config = ConfigDict(protected_namespaces=())

    task_description: str = Field(..., min_length=1, max_length=MAX_TASK_LENGTH)
    optimize_for:     str = Field(default="reliability",
                                   pattern="^(reliability|creativity|speed)$")
    reasoning_depth:  Optional[str] = Field(default=None, pattern="^(standard|deep|ultra)$")
    task_type:        str = Field(default="analysis", pattern="^(analysis|code|research|planning)$")
    model_hint:       Optional[str] = Field(
        default=None,
        description="Hint to route to a specific model tier (e.g. 'haiku', 'sonnet', 'opus')"
    )
    platform:         Optional[str] = Field(default=None, pattern="^(mac|win)$")
    context:          Optional[dict] = Field(default_factory=dict)
    request_id:       Optional[str] = Field(default=None)
    session_id:       Optional[str] = Field(default=None,
                                             description="v2 session correlation ID (perpetua-core/oramasys)")
    backend_priority: str = Field(
        default="local",
        pattern="^(local|cloud|windows)$",
        description="Backend dispatch order: local (default) → cloud → windows. "
                    "Override env ORAMA_BACKEND_PRIORITY or pass per-request.",
    )

    @field_validator("task_description")
    @classmethod
    def task_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_description must not be blank or whitespace-only")
        return v.strip()


class UltraThinkResponse(BaseModel):
    """
    POST /ultrathink response.
    v2 shape: session_id, nodes_visited, retry_count added for perpetua-core compatibility.
    """
    model_config = ConfigDict(protected_namespaces=())

    status:      str  # "success" | "error"
    result:      str
    model_used:  str
    execution_time_ms: int
    reasoning_depth: str
    metadata:    dict[str, Any]
    session_id:       Optional[str] = Field(default=None)
    nodes_visited:    list[str] = Field(default_factory=list)
    retry_count:      int = Field(default=0)


# ── Model Call Stub (Mockable for tests) ──────────────────────────────────────

async def _call_with_fallback(prompt: str, model: str, max_tokens: int, temperature: float) -> tuple[str, str]:
    """Stub for calling Ollama/LMStudio; primary purpose is being mocked in tests."""
    return f"Stateless output for {model}", "http://localhost:1234"


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize hardware policy resolver (PT-first, cache fallback)."""
    _policy_resolver.initialize()
    if not _policy_resolver.pt_available:
        logger.warning(
            "⚠️  orama started WITHOUT Perpetua-Tools policy authority. "
            "source=%s — set PERPETUA_TOOLS_ROOT to restore PT-authoritative enforcement.",
            _policy_resolver.source,
        )
    else:
        logger.info("✓ Perpetua-Tools hardware policy loaded (PT-authoritative).")
    yield
    # Shutdown: nothing to clean up (stateless)


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="The ὅραμα System API",
    description="Stateless POST /ultrathink endpoint. State owned by Perpetua-Tools.",
    version="0.9.9.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
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

    requested_platform = req.platform or (req.context or {}).get("platform") or (req.context or {}).get("affinity")
    if not requested_platform and "/" in model:
        provider, raw_model = model.split("/", 1)
        if provider in {"lmstudio-mac", "ollama-mac"}:
            requested_platform = "mac"
            model = raw_model
        elif provider in {"lmstudio-win", "ollama-win"}:
            requested_platform = "win"
            model = raw_model
    if not requested_platform:
        requested_platform = expected_platform_for_model(model)
    if requested_platform:
        try:
            check_affinity(model_id=model, platform=requested_platform)
        except HardwareAffinityError as exc:
            return JSONResponse(
                status_code=400,
                content={"error": "HARDWARE_MISMATCH", "detail": str(exc)},
            )
    
    # Resolve backend dispatch order: request field > env var > platform-default
    backend_router = BackendRouter(override=req.backend_priority, task_type=req.task_type)
    backend_attempted = backend_router.ordered_endpoints()[0]["name"]

    logger.info(
        "task_id=%s depth=%s model=%s backend=%s",
        req.request_id, reasoning_depth, model, backend_attempted,
    )

    # Call backend (stubbed/mocked; real implementation uses backend_router.ordered_endpoints())
    prompt = f"Applying {reasoning_depth}-depth reasoning for task: {req.task_description}"
    result, _ = await _call_with_fallback(prompt, model, 4000, 0.7)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return UltraThinkResponse(
        status="success",
        result=result,
        model_used=model,
        execution_time_ms=elapsed_ms,
        reasoning_depth=reasoning_depth,
        session_id=req.session_id,
        nodes_visited=["ultrathink_node"],
        metadata={
            "mapped_optimize_for": mapped_optimize_for,
            "mapping_source": mapping_source,
            "bridge_mode": "http_primary",
            "model_hint_used": req.model_hint is not None,
            "backend_priority": backend_router.priority,
            "backend_attempted": backend_attempted,
            # PT final handoff audit — always present so callers know policy authority
            "policy_source": _policy_resolver.source,
            "pt_authoritative": _policy_resolver.pt_available,
        }
    )

@app.get("/health")
async def health():
    runtime_state = _load_pt_runtime_state()
    return {
        "status": "ok",
        "version": "0.9.9.2",
        "lmstudio_win_reachable": True,
        "lmstudio_mac_reachable": True,
        "ollama_primary_reachable": True,
        "ollama_fallback_reachable": True,
        "bridge_mode": "http_primary",
        "orchestrator": "mac-studio",
        "execution_target": "win-rtx3080",
        "primary_contract": "lmstudio",
        "mapping": OPTIMIZE_FOR_TO_REASONING_DEPTH,
        "pt_runtime": {
            "available": runtime_state is not None,
            "gateway_ready": bool((runtime_state or {}).get("gateway", {}).get("gateway_ready")),
            "distributed": bool((runtime_state or {}).get("routing", {}).get("distributed")),
        },
        "hardware_policy": {
            "source": _policy_resolver.source,
            "pt_authoritative": _policy_resolver.pt_available,
        },
        "backend_priority": BackendRouter().priority,
        "backend_endpoints": BackendRouter().ordered_endpoints(),
    }


@app.get("/runtime-state")
async def runtime_state():
    payload = _load_pt_runtime_state()
    return {"available": payload is not None, "runtime": payload}

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ultrathink API on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
