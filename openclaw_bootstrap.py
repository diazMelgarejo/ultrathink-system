#!/usr/bin/env python3
"""
openclaw_bootstrap.py — ultrathink-system delegation shim
----------------------------------------------------------
Bootstrap logic has moved to Perplexity-Tools/alphaclaw_bootstrap.py.

This shim delegates to the canonical PT script via PT_HOME env var,
falling back to the inline logic below only when PT is not found.

Set PT_HOME to the root of your Perplexity-Tools checkout:
    export PT_HOME=/path/to/Perplexity-Tools

Usage (unchanged):
    python openclaw_bootstrap.py --bootstrap
    python openclaw_bootstrap.py --bootstrap --force
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

# ── delegation ────────────────────────────────────────────────────────────────

_PT_HOME    = Path(os.getenv("PT_HOME", str(Path.home() / "Perplexity-Tools")))
_PT_SCRIPT  = _PT_HOME / "alphaclaw_bootstrap.py"


async def bootstrap_openclaw(force: bool = False) -> bool:
    """Delegate to PT's alphaclaw_bootstrap.py, fallback to inline logic."""
    if _PT_SCRIPT.exists():
        print(f"[openclaw] → Delegating to PT bootstrap: {_PT_SCRIPT}")
        extra = ["--force"] if force else []
        result = subprocess.run(
            [sys.executable, str(_PT_SCRIPT), "--bootstrap"] + extra,
            env={**os.environ, "UTS_HOME": str(SCRIPT_DIR)},
        )
        return result.returncode == 0

    print("[openclaw] ⚠  PT_HOME not found "
          f"({_PT_HOME}) — running inline fallback")
    return await _bootstrap_inline(force=force)


# ── inline fallback (kept for UTS standalone use without PT) ──────────────────

OPENCLAW_GATEWAY_PORT: int = int(os.getenv("OPENCLAW_GATEWAY_PORT", "18789"))
_extra_ports = [int(p) for p in os.getenv("OPENCLAW_EXTRA_PORTS", "").split(",")
                if p.strip()]
OPENCLAW_CANDIDATE_PORTS: list[int] = list(dict.fromkeys(
    [OPENCLAW_GATEWAY_PORT, 11435, 8080, 3000, 4000, 9000] + _extra_ports
))

MAC_IP    = os.getenv("MAC_IP", "192.168.254.105")
WIN_IP    = os.getenv("WIN_IP", "192.168.254.101")
OLLAMA_MAC = os.getenv("OLLAMA_MAC_ENDPOINT",    f"http://{MAC_IP}:11434")
OLLAMA_WIN = os.getenv("OLLAMA_WINDOWS_ENDPOINT", f"http://{WIN_IP}:11434")
LMS_MAC   = os.getenv("LM_STUDIO_MAC_ENDPOINT",   f"http://{MAC_IP}:1234")
LMS_WIN   = os.getenv("LM_STUDIO_WIN_ENDPOINTS",   f"http://{WIN_IP}:1234")
LMS_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "lm-studio")
MAC_MODEL = os.getenv("MAC_LMS_MODEL", "qwen3:8b-instruct")
WIN_MODEL = os.getenv("WINDOWS_LMS_MODEL",
                      "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2")

# Autoresearch — env-var configurable (mirrors PT's alphaclaw_bootstrap.py)
AUTORESEARCH_REMOTE = os.getenv(
    "AUTORESEARCH_REMOTE", "https://github.com/uditgoenka/autoresearch"
)


async def _probe_url(url: str, client) -> bool:
    for path in ("/health", "/v1/models"):
        try:
            r = await client.get(f"{url.rstrip('/')}{path}")
            if r.status_code < 400:
                return True
        except Exception:
            pass
    return False


async def _find_any_gateway() -> str | None:
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


def _load_pt_state() -> dict | None:
    state_path = os.getenv("PT_AGENTS_STATE")
    if state_path and Path(state_path).exists():
        with open(state_path) as f:
            return json.load(f)
    return None


def _lms_base_url(raw: str) -> str:
    raw = raw.rstrip("/")
    return raw if raw.endswith("/v1") else f"{raw}/v1"


def _write_openclaw_config(config_dir: Path, config_file: Path) -> None:
    pt = _load_pt_state()
    if pt:
        mac_lms_url   = pt.get("mac_lmstudio_endpoint") or LMS_MAC
        win_lms_url   = pt.get("lmstudio_endpoint")     or LMS_WIN
        coder_model   = pt.get("coder_model",   WIN_MODEL)
        manager_model = pt.get("manager_model", MAC_MODEL)
        coder_backend = pt.get("coder_backend", "mac-degraded")
        mac_lms_ok    = bool(pt.get("mac_lmstudio_ok"))
    else:
        mac_lms_url = LMS_MAC; win_lms_url = LMS_WIN
        coder_model = WIN_MODEL; manager_model = MAC_MODEL
        coder_backend = "unknown"; mac_lms_ok = False

    if coder_backend == "windows-lmstudio":
        coder_primary = f"lmstudio-win/{coder_model}"
    elif coder_backend == "windows-ollama":
        coder_primary = f"ollama-win/{coder_model}"
    else:
        coder_primary = f"lmstudio-mac/{manager_model}"
    manager_primary = (f"lmstudio-mac/{manager_model}" if mac_lms_ok
                       else f"ollama-mac/{manager_model}")

    agents_root = str(Path.home() / ".openclaw" / "agents")
    config = {
        "gateway": {"mode": "local", "port": OPENCLAW_GATEWAY_PORT,
                    "bind": "loopback", "commandeered": False},
        "agents": {
            "defaults": {"model": {"primary": manager_primary},
                         "workspace": f"{agents_root}/default"},
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
                    "baseUrl": _lms_base_url(mac_lms_url), "apiKey": LMS_TOKEN,
                    "api": "openai-completions",
                    "models": [{"id": MAC_MODEL, "name": f"Mac LMS — {MAC_MODEL}",
                                "contextWindow": 32768, "maxTokens": 8192,
                                "cost": {"input": 0, "output": 0}}],
                },
                "lmstudio-win": {
                    "baseUrl": _lms_base_url(win_lms_url), "apiKey": LMS_TOKEN,
                    "api": "openai-completions",
                    "models": [{"id": WIN_MODEL, "name": f"Win LMS — {WIN_MODEL}",
                                "contextWindow": 32768, "maxTokens": 8192,
                                "cost": {"input": 0, "output": 0}}],
                },
                "ollama-mac": {"apiKey": "ollama-local",
                               "baseUrl": OLLAMA_MAC, "api": "ollama"},
                "ollama-win": {"apiKey": "ollama-remote",
                               "baseUrl": OLLAMA_WIN, "api": "ollama"},
            },
        },
    }
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[openclaw] ✓ openclaw.json written → {config_file}")


def _ensure_agent_workspaces(config_dir: Path) -> None:
    soul_src   = SCRIPT_DIR / "bin" / "agents"
    agents_dir = config_dir / "agents"
    roles = ["mac-researcher", "win-researcher", "orchestrator",
             "coder", "autoresearcher"]
    for role in roles:
        role_dir = agents_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        soul_file = role_dir / "SOUL.md"
        if soul_file.exists():
            continue
        src = soul_src / role / "SOUL.md"
        if src.exists():
            shutil.copy(src, soul_file)
            print(f"[openclaw] ✓ agent workspace: {role}")
        else:
            print(f"[openclaw] ⚠ missing SOUL.md for {role}")


def _ensure_autoresearch() -> None:
    """Idempotent clone + uv sync --dev of ~/autoresearch (uditgoenka/autoresearch)."""
    repo = Path.home() / "autoresearch"
    if repo.exists():
        print("[openclaw] ✓ ~/autoresearch already exists")
        return
    print(f"[openclaw] → Cloning {AUTORESEARCH_REMOTE}…")
    try:
        subprocess.run(["git", "clone", AUTORESEARCH_REMOTE, str(repo)],
                       check=True)
        import datetime
        branch = f"autoresearch/{datetime.date.today().isoformat()}"
        subprocess.run(["git", "checkout", "-b", branch], cwd=repo, check=True)
        subprocess.run(["pip", "install", "uv"], check=True, capture_output=True)
        subprocess.run(["uv", "sync", "--dev"], cwd=repo, check=True)
        print("[openclaw] ✓ autoresearch ready")
    except subprocess.CalledProcessError as e:
        print(f"[openclaw] ✗ autoresearch setup failed (non-fatal): {e}")


async def _bootstrap_inline(force: bool = False) -> bool:
    """Inline fallback when PT is unavailable."""
    try:
        import httpx  # noqa: F401
    except ImportError:
        print("[openclaw] ✗ httpx not installed — run: pip install httpx")
        return False

    config_dir  = Path.home() / ".openclaw"
    config_file = config_dir / "openclaw.json"

    print(f"[openclaw] → Probing {len(OPENCLAW_CANDIDATE_PORTS)} candidate ports…")
    existing_url = await _find_any_gateway()
    if existing_url:
        print(f"[openclaw] ✓ Found gateway at {existing_url} — commandeering")
        os.environ["OPENCLAW_GATEWAY_URL"] = existing_url
        if not config_file.exists() or force:
            _write_openclaw_config(config_dir, config_file)
        _ensure_agent_workspaces(config_dir)
        _ensure_autoresearch()
        return True

    if not shutil.which("npm"):
        print("[openclaw] ✗ npm not found — install Node.js from https://nodejs.org/")
        return False

    _aclaw_installed = shutil.which("alphaclaw") is not None
    if not _aclaw_installed:
        install_dir = Path.home() / ".alphaclaw"
        install_dir.mkdir(parents=True, exist_ok=True)
        print("[openclaw] → Installing @chrysb/alphaclaw…")
        try:
            subprocess.run(["npm", "install", "@chrysb/alphaclaw"],
                           check=True, cwd=str(install_dir))
        except subprocess.CalledProcessError as e:
            print(f"[openclaw] ✗ install failed: {e}")
            return False

    if not config_file.exists() or force:
        _write_openclaw_config(config_dir, config_file)
    _ensure_agent_workspaces(config_dir)

    print("[openclaw] → Starting AlphaClaw gateway…")
    try:
        install_dir = Path.home() / ".alphaclaw"
        subprocess.Popen(["npx", "alphaclaw", "start"], cwd=str(install_dir))
        gateway_url = f"http://127.0.0.1:{OPENCLAW_GATEWAY_PORT}"
        os.environ["OPENCLAW_GATEWAY_URL"] = gateway_url
    except Exception as e:
        print(f"[openclaw] ✗ gateway start failed: {e}")
        return False

    _ensure_autoresearch()
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ultrathink-system OpenClaw/AlphaClaw bootstrap shim",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Delegates to Perplexity-Tools/alphaclaw_bootstrap.py when PT_HOME is set.\n"
            "Falls back to inline logic if PT is unavailable.\n\n"
            "Set PT_HOME to your Perplexity-Tools checkout root:\n"
            "  export PT_HOME=/path/to/Perplexity-Tools\n"
        ),
    )
    parser.add_argument("--bootstrap", action="store_true",
                        help="Idempotent AlphaClaw install + configure + start")
    parser.add_argument("--force", action="store_true",
                        help="Force-rewrite openclaw.json")
    _args = parser.parse_args()

    if _args.bootstrap:
        ok = asyncio.run(bootstrap_openclaw(force=_args.force))
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)
