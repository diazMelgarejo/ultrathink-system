#!/usr/bin/env python3
"""
validate_registry.py — model registry validator with live-agent detection.

On each run:
1. Probes all known endpoints (LM Studio Win/Mac, Ollama Win/Mac, Portal)
2. Compares what is actually running against the expected registry
3. For FIRST RUN (no prior state): offers to spin up sensible defaults
4. For RUNNING AGENTS: asks before commandeering (never silently takes over)
5. Reports mismatches and exits 1 if any required backend is unreachable

Usage:
    python scripts/validate_registry.py             # probe + report
    python scripts/validate_registry.py --spin      # probe + offer to start defaults
    python scripts/validate_registry.py --yes       # non-interactive (auto-confirm defaults)
    python scripts/validate_registry.py --quiet     # minimal output (CI mode)

Exit codes:
    0 — all required backends reachable
    1 — one or more required backends unreachable
    2 — config/read error
"""

import asyncio
import json
import os
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

REPO_ROOT = Path(__file__).parent.parent
STATE_FILE = REPO_ROOT / ".state" / "registry_state.json"

# ---------------------------------------------------------------------------
# Known agent endpoints (override via env vars)
# ---------------------------------------------------------------------------

KNOWN_AGENTS = [
    {
        "name": "LM Studio Win (primary agent)",
        "env_key": "LMS_WIN_ENDPOINTS",
        "default": "http://192.168.254.101:1234",
        "probe_path": "/v1/models",
        "required": True,
        "role": "coder/checker/refiner/executor/verifier",
        "model_env": "LMS_WIN_MODEL",
        "model_default": "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
    },
    {
        "name": "LM Studio Mac (orchestrator)",
        "env_key": "LMS_MAC_ENDPOINT",
        "default": "http://localhost:1234",
        "probe_path": "/v1/models",
        "required": True,
        "role": "orchestrator/final-validator/presenter",
        "model_env": "LMS_MAC_MODEL",
        "model_default": "Qwen3.5-9B-MLX-4bit",
    },
    {
        "name": "Ollama Win (fallback)",
        "env_key": "OLLAMA_WIN_ENDPOINT",
        "default": "http://192.168.254.101:11434",
        "probe_path": "/api/tags",
        "required": False,
        "role": "fallback",
        "model_env": None,
        "model_default": None,
    },
    {
        "name": "Ollama Mac (fallback)",
        "env_key": "OLLAMA_MAC_ENDPOINT",
        "default": "http://localhost:11434",
        "probe_path": "/api/tags",
        "required": False,
        "role": "fallback",
        "model_env": None,
        "model_default": None,
    },
    {
        "name": "Portal (LAN dashboard)",
        "env_key": "PORTAL_ENDPOINT",
        "default": "http://localhost:8002",
        "probe_path": "/health",
        "required": False,
        "role": "dashboard",
        "model_env": None,
        "model_default": None,
    },
    {
        "name": "UltraThink API (this service)",
        "env_key": "ULTRATHINK_ENDPOINT",
        "default": "http://localhost:8001",
        "probe_path": "/health",
        "required": False,
        "role": "api",
        "model_env": None,
        "model_default": None,
    },
]


@dataclass
class ProbeResult:
    name: str
    endpoint: str
    reachable: bool
    models: list[str] = field(default_factory=list)
    expected_model: Optional[str] = None
    model_loaded: Optional[bool] = None
    required: bool = False
    role: str = ""
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Async probing
# ---------------------------------------------------------------------------

async def probe_lms_endpoint(
    session: "httpx.AsyncClient",
    name: str,
    endpoint: str,
    path: str,
    expected_model: Optional[str],
    required: bool,
    role: str,
    timeout: float = 3.0,
) -> ProbeResult:
    url = endpoint.rstrip("/") + path
    try:
        resp = await session.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # LM Studio /v1/models returns {"data": [{"id": "..."}]}
        # Ollama /api/tags returns {"models": [{"name": "..."}]}
        models: list[str] = []
        if "data" in data:
            models = [m.get("id", m.get("name", "")) for m in data["data"]]
        elif "models" in data:
            models = [m.get("name", m.get("id", "")) for m in data["models"]]

        model_loaded = None
        if expected_model and models:
            model_loaded = any(expected_model.lower() in m.lower() for m in models)

        return ProbeResult(
            name=name, endpoint=endpoint, reachable=True,
            models=models, expected_model=expected_model,
            model_loaded=model_loaded, required=required, role=role,
        )
    except Exception as e:
        return ProbeResult(
            name=name, endpoint=endpoint, reachable=False,
            required=required, role=role, error=str(e),
        )


async def probe_all(agents: list[dict]) -> list[ProbeResult]:
    if not HAS_HTTPX:
        print("WARNING: httpx not installed — using socket-only probe", file=sys.stderr)
        return _probe_all_socket(agents)

    async with httpx.AsyncClient() as client:
        tasks = [
            probe_lms_endpoint(
                client,
                a["name"],
                os.environ.get(a["env_key"], a["default"]),
                a["probe_path"],
                os.environ.get(a["model_env"], a["model_default"])
                if a["model_env"] else a["model_default"],
                a["required"],
                a["role"],
            )
            for a in agents
        ]
        return await asyncio.gather(*tasks)


def _probe_all_socket(agents: list[dict]) -> list[ProbeResult]:
    """Fallback socket probe when httpx is absent."""
    import socket
    import urllib.request

    results = []
    for a in agents:
        endpoint = os.environ.get(a["env_key"], a["default"])
        expected = (
            os.environ.get(a["model_env"], a["model_default"])
            if a["model_env"] else a["model_default"]
        )
        url = endpoint.rstrip("/") + a["probe_path"]
        try:
            req = urllib.request.urlopen(url, timeout=3)
            data = json.loads(req.read())
            models: list[str] = []
            if "data" in data:
                models = [m.get("id", "") for m in data["data"]]
            elif "models" in data:
                models = [m.get("name", "") for m in data["models"]]
            model_loaded = (
                any(expected.lower() in m.lower() for m in models)
                if expected and models else None
            )
            results.append(ProbeResult(
                name=a["name"], endpoint=endpoint, reachable=True,
                models=models, expected_model=expected,
                model_loaded=model_loaded, required=a["required"], role=a["role"],
            ))
        except Exception as e:
            results.append(ProbeResult(
                name=a["name"], endpoint=endpoint, reachable=False,
                required=a["required"], role=a["role"], error=str(e),
            ))
    return results


# ---------------------------------------------------------------------------
# State persistence (first-run detection)
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Reporting + commandeer logic
# ---------------------------------------------------------------------------

def print_results(results: list[ProbeResult], quiet: bool) -> None:
    ok = [r for r in results if r.reachable]
    fail = [r for r in results if not r.reachable]

    if not quiet:
        print("\n=== Model Registry Status ===")
        for r in results:
            status = "OK  " if r.reachable else "FAIL"
            model_note = ""
            if r.reachable and r.expected_model:
                if r.model_loaded is True:
                    model_note = f" [{r.expected_model}: loaded]"
                elif r.model_loaded is False:
                    model_note = f" [{r.expected_model}: NOT LOADED]"
            req_note = " (required)" if r.required else ""
            print(f"  [{status}] {r.name}{req_note} — {r.endpoint}{model_note}")
        print(f"\nReachable: {len(ok)}/{len(results)}", end="")
        if fail:
            missing_req = [r for r in fail if r.required]
            print(f"  |  Missing required: {len(missing_req)}")
        else:
            print()


def offer_defaults(results: list[ProbeResult], auto_yes: bool, quiet: bool) -> None:
    """For unreachable agents, suggest start commands — ask before doing anything."""
    unreachable = [r for r in results if not r.reachable]
    if not unreachable:
        return

    SPIN_COMMANDS = {
        "LM Studio Win (primary agent)": (
            "# Start LM Studio on Windows and load the model manually in the UI.\n"
            "# Then set: LMS_WIN_ENDPOINTS=http://<win-ip>:1234"
        ),
        "LM Studio Mac (orchestrator)": (
            "# Start LM Studio on Mac and load Qwen3.5-9B-MLX-4bit in the UI.\n"
            "# Ensure Server is enabled on port 1234."
        ),
        "Ollama Win (fallback)": "ollama serve  # on Windows",
        "Ollama Mac (fallback)": "ollama serve  # on Mac",
        "Portal (LAN dashboard)": "python portal_server.py",
        "UltraThink API (this service)": "python api_server.py",
    }

    if not quiet:
        print("\n=== Suggested Start Commands for Unreachable Services ===")
        for r in unreachable:
            cmd = SPIN_COMMANDS.get(r.name, f"# Start {r.name} manually")
            print(f"\n  {r.name}:")
            for line in cmd.splitlines():
                print(f"    {line}")

        if any(r.required for r in unreachable):
            print(
                "\n  WARN: one or more REQUIRED backends are unreachable. "
                "Start them before running tasks."
            )


def check_commandeer(results: list[ProbeResult], auto_yes: bool, quiet: bool) -> None:
    """
    Running agents detected — ask user before claiming ownership.
    Never silently commandeer.
    """
    running = [r for r in results if r.reachable and r.models]
    if not running:
        return

    state = load_state()
    already_registered = state.get("registered_agents", [])

    new_agents = [r for r in running if r.endpoint not in already_registered]
    if not new_agents:
        return  # already known, no prompt needed

    if not quiet:
        print("\n=== New Running Agents Detected ===")
        for r in new_agents:
            models_preview = ", ".join(r.models[:3])
            if len(r.models) > 3:
                models_preview += f"... (+{len(r.models) - 3} more)"
            print(f"  {r.name} @ {r.endpoint} — models: [{models_preview}]")

    if auto_yes:
        answer = "y"
    else:
        try:
            answer = input(
                "\nRegister these agents in local state? [y/N] "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

    if answer == "y":
        state.setdefault("registered_agents", [])
        for r in new_agents:
            if r.endpoint not in state["registered_agents"]:
                state["registered_agents"].append(r.endpoint)
        save_state(state)
        if not quiet:
            print(f"  Registered {len(new_agents)} agent(s) in {STATE_FILE}")
    else:
        if not quiet:
            print("  Skipped — agents not registered.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spin", action="store_true",
        help="Show suggested start commands for unreachable services",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Non-interactive: auto-confirm agent registration",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Minimal output (CI mode) — only errors printed",
    )
    args = parser.parse_args()

    results = asyncio.run(probe_all(KNOWN_AGENTS))

    print_results(results, quiet=args.quiet)

    if args.spin:
        offer_defaults(results, auto_yes=args.yes, quiet=args.quiet)

    check_commandeer(results, auto_yes=args.yes, quiet=args.quiet)

    # Exit 1 if any required backend is unreachable
    required_failures = [r for r in results if r.required and not r.reachable]
    if required_failures:
        if not args.quiet:
            names = ", ".join(r.name for r in required_failures)
            print(f"\nFAIL: required backends unreachable: {names}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
