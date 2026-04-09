#!/usr/bin/env python3
"""
openclaw_bootstrap.py - ultrathink-system delegate-only OpenClaw config applier
-----------------------------------------------------------------------------
Perplexity-Tools is the sole runtime authority. This script only:
  1. Reads the PT-resolved runtime payload
  2. Writes ~/.openclaw/openclaw.json using that exact payload
  3. Ensures local agent workspaces and SOUL.md files exist

Usage:
    python openclaw_bootstrap.py --apply
    python openclaw_bootstrap.py --apply --payload /path/to/runtime_payload.json
    python openclaw_bootstrap.py --apply --force
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PAYLOAD = Path(".state/pt_runtime_payload.json")
OPENCLAW_GATEWAY_PORT = int(os.getenv("OPENCLAW_GATEWAY_PORT", "18789"))

# Candidate ports to probe for any running OpenClaw-compatible gateway.
# Includes OpenClaw default (18789) and AlphaClaw (chrysb/alphaclaw) which
# may run on 11435 or other ports. Add more via OPENCLAW_EXTRA_PORTS env var.
_extra = [int(p) for p in os.getenv("OPENCLAW_EXTRA_PORTS", "").split(",") if p.strip()]
OPENCLAW_CANDIDATE_PORTS: list[int] = list(dict.fromkeys(
    [OPENCLAW_GATEWAY_PORT, 11435, 8080, 3000, 4000, 9000] + _extra
))

# ── env-var defaults (all exported by start.sh) ───────────────────────────────

MAC_IP     = os.getenv("MAC_IP",  "192.168.254.103")
WIN_IP     = os.getenv("WIN_IP",  "192.168.254.100")
OLLAMA_MAC = os.getenv("OLLAMA_MAC_ENDPOINT",     f"http://{MAC_IP}:11434")
OLLAMA_WIN = os.getenv("OLLAMA_WINDOWS_ENDPOINT",  f"http://{WIN_IP}:11434")
LMS_MAC    = os.getenv("LM_STUDIO_MAC_ENDPOINT",   f"http://{MAC_IP}:1234")
LMS_WIN    = os.getenv("LM_STUDIO_WIN_ENDPOINTS",   f"http://{WIN_IP}:1234")
LMS_TOKEN  = os.getenv("LM_STUDIO_API_TOKEN", "lm-studio")

MAC_MODEL  = os.getenv("MAC_LMS_MODEL", "qwen3:8b-instruct")
WIN_MODEL  = os.getenv("WINDOWS_LMS_MODEL",
                        "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2")


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_pt_state() -> dict | None:
    """Load PT's real probe results from .state/routing.json (PT_AGENTS_STATE env var)."""
    state_path = os.getenv("PT_AGENTS_STATE")
    if state_path and Path(state_path).exists():
        with open(state_path) as f:
            return json.load(f)
    return None


def _lms_base_url(raw: str) -> str:
    """Ensure LM Studio baseUrl ends with /v1 (OpenAI-compat requirement)."""
    raw = raw.rstrip("/")
    return raw if raw.endswith("/v1") else f"{raw}/v1"


# ── gateway discovery ─────────────────────────────────────────────────────────

async def _probe_url(url: str, client) -> bool:
    """Return True if url responds with HTTP < 400 on /health or /v1/models."""
    for path in ("/health", "/v1/models"):
        try:
            r = await client.get(f"{url.rstrip('/')}{path}")
            if r.status_code < 400:
                return True
        except Exception:
            pass
    return False


async def _find_any_gateway() -> str | None:
    """
    Probe all candidate ports for a running OpenClaw-compatible gateway.

    Compatible gateways (OpenClaw, AlphaClaw, or any proxy exposing /health
    or /v1/models) are detected without discriminating on implementation.
    Returns the base URL of the first responsive gateway, or None.
    """
    try:
        import httpx
    except ImportError:
        return None

    async with httpx.AsyncClient(timeout=1.5) as client:
        for port in OPENCLAW_CANDIDATE_PORTS:
            url = f"http://127.0.0.1:{port}"
            if await _probe_url(url, client):
                return url
    return None


def _write_openclaw_config(config_dir: Path, config_file: Path) -> None:
    """Write ~/.openclaw/openclaw.json from PT probe results + env-var defaults."""
    pt = _load_pt_state()

    if pt:
        # Use real probe results from Perplexity-Tools
        mac_lms_url   = pt.get("mac_lmstudio_endpoint") or LMS_MAC
        win_lms_url   = pt.get("lmstudio_endpoint")     or LMS_WIN
        coder_model   = pt.get("coder_model",   WIN_MODEL)
        manager_model = pt.get("manager_model", MAC_MODEL)
        coder_backend = pt.get("coder_backend", "mac-degraded")
        mac_lms_ok    = bool(pt.get("mac_lmstudio_ok"))
    else:
        mac_lms_url   = LMS_MAC
        win_lms_url   = LMS_WIN
        coder_model   = WIN_MODEL
        manager_model = MAC_MODEL
        coder_backend = "unknown"
        mac_lms_ok    = False

    # Resolve primary model refs based on what's actually live
    if coder_backend == "windows-lmstudio":
        coder_primary   = f"lmstudio-win/{coder_model}"
    elif coder_backend == "windows-ollama":
        coder_primary   = f"ollama-win/{coder_model}"
    else:
        coder_primary   = f"lmstudio-mac/{manager_model}"


def _payload_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env_path = Path(sys.argv[0]).parent / ".state" / "pt_runtime_payload.json"
    return Path(
        os.environ.get("PT_RUNTIME_STATE")
        or os.environ.get("PT_RUNTIME_PAYLOAD")
        or env_path
    )


def load_runtime_payload(payload: str | None = None) -> dict[str, Any]:
    path = _payload_path(payload)
    if not path.exists():
        raise FileNotFoundError(
            f"PT runtime payload not found: {path}. "
            "Run Perplexity-Tools orchestrator.py bootstrap first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_agent_workspaces(config_dir: Path) -> None:
    agents_dir = config_dir / "agents"
    roles = ["mac-researcher", "win-researcher", "orchestrator", "coder", "autoresearcher"]
    for role in roles:
        role_dir = agents_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        soul_file = role_dir / "SOUL.md"
        if soul_file.exists():
            continue
        source = SCRIPT_DIR / "bin" / "agents" / role / "SOUL.md"
        if source.exists():
            shutil.copy(source, soul_file)
            print(f"[openclaw] wrote workspace for {role}")


def apply_runtime_payload(payload: dict[str, Any], force: bool = False) -> dict[str, Any]:
    openclaw_config = payload.get("gateway", {}).get("openclaw_config")
    if not openclaw_config:
        raise ValueError("PT runtime payload does not contain gateway.openclaw_config")

    config_dir = Path.home() / ".openclaw"
    config_file = config_dir / "openclaw.json"
    config_dir.mkdir(parents=True, exist_ok=True)

    if force or not config_file.exists() or json.loads(config_file.read_text(encoding="utf-8")) != openclaw_config:
        config_file.write_text(json.dumps(openclaw_config, indent=2), encoding="utf-8")
        print(f"[openclaw] applied PT-resolved config -> {config_file}")
    else:
        print(f"[openclaw] config already matches PT payload -> {config_file}")

    _ensure_agent_workspaces(config_dir)
    return {
        "applied": True,
        "config_path": str(config_file),
        "gateway_ready": bool(payload.get("gateway", {}).get("gateway_ready")),
        "gateway_url": payload.get("gateway", {}).get("gateway_url"),
        "topology": payload.get("role_routing", {}).get("topology"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delegate-only OpenClaw config applier for ultrathink-system",
    )
    parser.add_argument("--apply", action="store_true", help="Apply PT-resolved OpenClaw config")
    parser.add_argument("--payload", default=None, help="Path to PT runtime payload JSON")
    parser.add_argument("--force", action="store_true", help="Force-write openclaw.json")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args()

    if not args.apply:
        parser.print_help()
        raise SystemExit(1)

    result = apply_runtime_payload(load_runtime_payload(args.payload), force=args.force)
    if args.json:
        print(json.dumps(result, indent=2))
    raise SystemExit(0)
