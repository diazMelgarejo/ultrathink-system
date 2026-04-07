#!/usr/bin/env python3
"""
openclaw_bootstrap.py — ultrathink-system OpenClaw bootstrap
--------------------------------------------------------------
Idempotent. Safe to call on every start.sh run.

Division of responsibilities:
  Perplexity-Tools  → probes real hardware, writes .state/routing.json
  ultrathink-system → reads probe results, writes ~/.openclaw/openclaw.json,
                      creates agent workspaces, starts the OpenClaw daemon

Set PT_AGENTS_STATE to the path of Perplexity-Tools' .state/routing.json so
this script can use real probe results instead of env-var defaults.

Usage:
    python openclaw_bootstrap.py --bootstrap            # full idempotent bootstrap
    python openclaw_bootstrap.py --bootstrap --force    # force-rewrite openclaw.json
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OPENCLAW_GATEWAY_PORT = 18789

# ── env-var defaults (all exported by start.sh) ───────────────────────────────

MAC_IP     = os.getenv("MAC_IP",  "192.168.254.105")
WIN_IP     = os.getenv("WIN_IP",  "192.168.254.101")
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

    manager_primary = (f"lmstudio-mac/{manager_model}" if mac_lms_ok
                       else f"ollama-mac/{manager_model}")

    agents_root = str(Path.home() / ".openclaw" / "agents")

    config = {
        "gateway": {"mode": "local", "port": OPENCLAW_GATEWAY_PORT, "bind": "loopback"},
        "agents": {
            "defaults": {
                "model": {"primary": manager_primary},
                "workspace": f"{agents_root}/default",
            },
            "list": [
                {"id": "mac-researcher",
                 "model": {"primary": manager_primary},
                 "workspace": f"{agents_root}/mac-researcher"},
                {"id": "win-researcher",
                 "model": {"primary": coder_primary},
                 "workspace": f"{agents_root}/win-researcher"},
                {"id": "orchestrator",
                 "model": {"primary": manager_primary},
                 "workspace": f"{agents_root}/orchestrator"},
                {"id": "coder",
                 "model": {"primary": coder_primary},
                 "workspace": f"{agents_root}/coder"},
                {"id": "autoresearcher",
                 "model": {"primary": coder_primary},
                 "workspace": str(Path.home() / "autoresearch")},
            ],
        },
        "models": {
            "providers": {
                "lmstudio-mac": {
                    "baseUrl": _lms_base_url(mac_lms_url),
                    "apiKey":  LMS_TOKEN,
                    "api":     "openai-completions",
                    "models":  [{"id": MAC_MODEL,
                                 "name": f"Mac LMS — {MAC_MODEL}",
                                 "contextWindow": 32768, "maxTokens": 8192,
                                 "cost": {"input": 0, "output": 0}}],
                },
                "lmstudio-win": {
                    "baseUrl": _lms_base_url(win_lms_url),
                    "apiKey":  LMS_TOKEN,
                    "api":     "openai-completions",
                    "models":  [{"id": WIN_MODEL,
                                 "name": f"Win LMS — {WIN_MODEL}",
                                 "contextWindow": 32768, "maxTokens": 8192,
                                 "cost": {"input": 0, "output": 0}}],
                },
                "ollama-mac": {
                    "apiKey":  "ollama-local",
                    "baseUrl": OLLAMA_MAC,
                    "api":     "ollama",
                },
                "ollama-win": {
                    "apiKey":  "ollama-remote",
                    "baseUrl": OLLAMA_WIN,
                    "api":     "ollama",
                },
            },
        },
    }

    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[openclaw] ✓ openclaw.json written → {config_file}  (coder-backend={coder_backend})")


def _ensure_agent_workspaces(config_dir: Path) -> None:
    """
    Copy SOUL.md files from openclaw/agents/<role>/ (git-tracked source)
    to ~/.openclaw/agents/<role>/SOUL.md. Idempotent — skips existing files.
    """
    soul_src   = SCRIPT_DIR / "bin" / "agents"
    agents_dir = config_dir / "agents"
    roles = ["mac-researcher", "win-researcher", "orchestrator", "coder", "autoresearcher"]

    for role in roles:
        role_dir  = agents_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        soul_file = role_dir / "SOUL.md"
        if soul_file.exists():
            continue
        src = soul_src / role / "SOUL.md"
        if src.exists():
            shutil.copy(src, soul_file)
            print(f"[openclaw] ✓ agent workspace: {role}")
        else:
            print(f"[openclaw] ⚠ missing source: openclaw/agents/{role}/SOUL.md")


def _ensure_autoresearch() -> None:
    """Idempotent clone + uv sync of ~/autoresearch (karpathy/autoresearch)."""
    repo = Path.home() / "autoresearch"
    if repo.exists():
        print("[openclaw] ✓ ~/autoresearch already exists")
        return
    print("[openclaw] → Cloning karpathy/autoresearch…")
    try:
        subprocess.run(
            ["git", "clone", "https://github.com/karpathy/autoresearch", str(repo)],
            check=True, capture_output=True,
        )
        subprocess.run(["pip", "install", "uv"], check=True, capture_output=True)
        subprocess.run(["uv", "sync"], cwd=repo, check=True, capture_output=True)
        print("[openclaw] ✓ autoresearch ready (run 'uv run prepare.py' for dataset)")
    except subprocess.CalledProcessError as e:
        print(f"[openclaw] ✗ autoresearch setup failed (non-fatal): {e}")


# ── main bootstrap ────────────────────────────────────────────────────────────

async def bootstrap_openclaw(force: bool = False) -> bool:
    """
    Idempotent OpenClaw gateway bootstrap. Safe to call on every start.sh run.

    Steps:
      1. Verify npm is available
      2. Install openclaw@latest if missing
      3. Write ~/.openclaw/openclaw.json (skipped if exists and not forced)
      4. Create agent workspaces from openclaw/agents/*/SOUL.md
      5. Start OpenClaw daemon (openclaw onboard --install-daemon) — reuses if running
      6. Ensure ~/autoresearch is cloned and synced
    """
    try:
        import httpx
    except ImportError:
        print("[openclaw] ✗ httpx not installed — run: pip install httpx")
        return False

    config_dir  = Path.home() / ".openclaw"
    config_file = config_dir  / "openclaw.json"

    # 1. npm check
    if not shutil.which("npm"):
        print("[openclaw] ✗ npm not found — install Node 24 from https://nodejs.org/")
        return False

    # 2. Install openclaw if missing
    if not shutil.which("openclaw"):
        print("[openclaw] → Installing openclaw@latest…")
        try:
            subprocess.run(["npm", "install", "-g", "openclaw@latest"],
                           check=True, capture_output=True)
            print("[openclaw] ✓ openclaw installed")
        except subprocess.CalledProcessError as e:
            print(f"[openclaw] ✗ install failed: {e.stderr.decode()[:200]}")
            return False

    # 3. Write config (first run or forced)
    if not config_file.exists() or force:
        _write_openclaw_config(config_dir, config_file)

    # 4. Agent workspaces
    _ensure_agent_workspaces(config_dir)

    # 5. Gateway — idempotent health check first
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"http://127.0.0.1:{OPENCLAW_GATEWAY_PORT}/health")
            if r.status_code == 200:
                print(f"[openclaw] ✓ gateway already running :{OPENCLAW_GATEWAY_PORT}")
                _ensure_autoresearch()
                return True
    except Exception:
        pass  # not running — fall through to start it

    print("[openclaw] → Starting OpenClaw gateway…")
    try:
        # onboard --install-daemon: configures defaults, registers daemon, starts gateway
        subprocess.run(["openclaw", "onboard", "--install-daemon"],
                       check=True, capture_output=True)
        print(f"[openclaw] ✓ gateway started :{OPENCLAW_GATEWAY_PORT}")
    except subprocess.CalledProcessError as e:
        print(f"[openclaw] ✗ gateway start failed: {e}")
        return False

    # 6. AutoResearcher
    _ensure_autoresearch()
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ultrathink-system OpenClaw bootstrap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python openclaw_bootstrap.py --bootstrap          # idempotent full bootstrap\n"
            "  python openclaw_bootstrap.py --bootstrap --force  # force-rewrite openclaw.json\n"
            "\n"
            "Environment variables (all exported by start.sh):\n"
            "  PT_AGENTS_STATE   path to Perplexity-Tools .state/routing.json (probe results)\n"
            "  MAC_IP / WIN_IP   detected LAN IPs\n"
            "  LM_STUDIO_*       LM Studio endpoints and token\n"
        ),
    )
    parser.add_argument("--bootstrap", action="store_true",
                        help="Idempotent OpenClaw install + configure + start gateway")
    parser.add_argument("--force", action="store_true",
                        help="Force-rewrite openclaw.json even if it already exists")
    _args = parser.parse_args()

    if _args.bootstrap:
        ok = asyncio.run(bootstrap_openclaw(force=_args.force))
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)
