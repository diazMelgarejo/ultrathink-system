#!/usr/bin/env python3
"""
spawn_agents.py — Parallel-agent dispatch for the three-repo AI stack.

Recruits available agents (Codex, Gemini CLI, LM Studio Mac/Win) for
division-of-labor coding tasks.  Respects the Windows GPU sequential-load
rule: at most one Win model request runs at a time.

Usage (CLI):
    python scripts/spawn_agents.py --task "review api_server.py for issues" --agent codex
    python scripts/spawn_agents.py --task "..."  --agent gemini
    python scripts/spawn_agents.py --task "..."  --agent lmstudio-mac
    python scripts/spawn_agents.py --task "..."  --agent lmstudio-win
    python scripts/spawn_agents.py --task "..."  --agent all      # parallel where safe
    python scripts/spawn_agents.py --status                        # show which agents are available

HTTP API (called from portal /api/spawn-agent):
    POST /api/spawn-agent  { "agent": "codex", "task": "..." }

Exit codes:
    0  — all dispatched agents completed without error
    1  — one or more agents failed or are unavailable
    2  — config / dependency error
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]

# Resolve Win IP via shared resolver (openclaw.json → discovery state → PT tilting → env → subnet.103)
# This avoids stale hardcoded IPs and works correctly whether called from start.sh or standalone.
try:
    import sys as _sys
    _sys.path.insert(0, str(REPO_ROOT))
    from utils.ip_resolver import get_win_lms_url as _get_win_lms_url
    _WIN_LMS_DEFAULT = _get_win_lms_url()
except Exception:
    _WIN_LMS_DEFAULT = "http://192.168.254.105:1234"  # true last-resort

LMS_MAC_ENDPOINT = os.getenv("LM_STUDIO_MAC_ENDPOINT", "http://localhost:1234")
LMS_WIN_ENDPOINT = os.getenv("LM_STUDIO_WIN_ENDPOINTS", _WIN_LMS_DEFAULT).split(",")[0].strip()
LMS_API_KEY = os.getenv("LM_STUDIO_API_TOKEN", "lm-studio")

OLLAMA_MAC_ENDPOINT = os.getenv("OLLAMA_MAC_ENDPOINT", "http://127.0.0.1:11434")
MANAGER_MODEL = os.getenv("MANAGER_MODEL", "qwen3.5:9b-nvfp4")

# Windows GPU lock — one model at a time (CLAUDE.md §4 invariant)
_WIN_GPU_LOCK = asyncio.Lock()


def _is_event_loop_running() -> bool:
    """Check if an asyncio event loop is already running (e.g. inside FastAPI)."""
    try:
        loop = asyncio.get_running_loop()
        return loop.is_running()
    except RuntimeError:
        return False

# ── Agent definitions ─────────────────────────────────────────────────────────

@dataclass
class AgentInfo:
    name: str
    kind: str          # "cli" | "http"
    available: bool = False
    version: str = ""
    detail: str = ""


def _probe_cli(cmd: List[str]) -> tuple[bool, str]:
    """Check if a CLI tool is reachable; return (available, version_string)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        ver = (r.stdout + r.stderr).strip().split("\n")[0]
        return r.returncode == 0, ver
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


async def _probe_http_async(url: str) -> bool:
    """Async probe for an HTTP endpoint (non-blocking)."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{url}/v1/models")
            return r.status_code < 500
    except Exception:
        return False


def discover_agents() -> Dict[str, AgentInfo]:
    """Probe all known agents and return their availability."""
    agents: Dict[str, AgentInfo] = {}

    # ── Codex ──────────────────────────────────────────────────────────────────
    codex_bin = shutil.which("codex") or "/opt/homebrew/bin/codex"
    ok, ver = _probe_cli([codex_bin, "--version"])
    agents["codex"] = AgentInfo(
        name="Codex",
        kind="cli",
        available=ok,
        version=ver,
        detail=codex_bin if ok else "not found — run scripts/setup_codex.sh",
    )

    # ── Gemini CLI ─────────────────────────────────────────────────────────────
    gemini_bin = shutil.which("gemini") or shutil.which("gemini-cli")
    if gemini_bin:
        ok, ver = _probe_cli([gemini_bin, "--version"])
    else:
        ok, ver = False, ""
    agents["gemini"] = AgentInfo(
        name="Gemini CLI",
        kind="cli",
        available=ok,
        version=ver,
        detail=gemini_bin if ok else "not found — install @google/gemini-cli",
    )
    agents["gemini-review"] = AgentInfo(
        name="Gemini Review",
        kind="cli",
        available=ok,
        version=ver,
        detail=f"Code review mode — {gemini_bin if ok else 'not found'}",
    )

    # ── Ollama Mac ─────────────────────────────────────────────────────────────
    ol_mac_ok = False
    ol_mac_ver = ""
    try:
        import httpx as _httpx_probe
        r = _httpx_probe.get(f"{OLLAMA_MAC_ENDPOINT}/api/tags", timeout=3.0)
        ol_mac_ok = r.status_code < 400
        if ol_mac_ok:
            models = r.json().get("models", [])
            ol_mac_ver = f"{len(models)} models" if models else "reachable"
    except Exception:
        pass
    agents["ollama-mac"] = AgentInfo(
        name="Ollama Mac",
        kind="http",
        available=ol_mac_ok,
        version=ol_mac_ver,
        detail=f"{OLLAMA_MAC_ENDPOINT} — {'reachable' if ol_mac_ok else 'not reachable'}",
    )

    # ── LM Studio Mac ──────────────────────────────────────────────────────────
    mac_ok = asyncio.run(_probe_http_async(LMS_MAC_ENDPOINT)) if not _is_event_loop_running() else False
    agents["lmstudio-mac"] = AgentInfo(
        name="LM Studio Mac",
        kind="http",
        available=mac_ok,
        detail=LMS_MAC_ENDPOINT,
    )

    # ── LM Studio Win ──────────────────────────────────────────────────────────
    win_ok = asyncio.run(_probe_http_async(LMS_WIN_ENDPOINT)) if not _is_event_loop_running() else False
    agents["lmstudio-win"] = AgentInfo(
        name="LM Studio Win (RTX 3080)",
        kind="http",
        available=win_ok,
        detail=LMS_WIN_ENDPOINT,
    )

    return agents


# ── Dispatch functions ────────────────────────────────────────────────────────

async def _dispatch_codex(task: str, context_file: Optional[Path] = None) -> Dict[str, Any]:
    """Run Codex on a task using a PTY to satisfy its terminal requirement.

    Codex requires stdin to be a TTY (interactive terminal). When spawned from
    Python subprocesses (Claude Code, portal, CI) there is no TTY.

    Fix: use Python's `pty.openpty()` to allocate a pseudo-terminal pair.
    The master fd receives all output; the slave fd is passed as stdin/stdout/stderr
    to the Codex process, satisfying its TTY check.

    This makes Codex fully automatable — no human terminal required.
    """
    import pty, select, fcntl, termios

    codex_bin = shutil.which("codex") or "/opt/homebrew/bin/codex"
    if not os.path.exists(codex_bin):
        return {"ok": False, "output": "Codex not found. Run scripts/setup_codex.sh", "elapsed": 0}

    task_with_ctx = task
    if context_file and context_file.exists():
        context = context_file.read_text()[:8000]  # limit context size
        task_with_ctx = f"Context:\n{context}\n\nTask:\n{task}"

    cmd = [codex_bin, "--full-auto", task_with_ctx]
    t0 = time.time()

    def _run_with_pty() -> tuple[int, str]:
        """Run codex in a PTY, collect all output, return (returncode, output)."""
        master_fd, slave_fd = pty.openpty()
        # Make master non-blocking for reads
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        import subprocess as _sp
        proc = _sp.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            cwd=str(REPO_ROOT),
        )
        os.close(slave_fd)  # parent doesn't need the slave end

        output_chunks = []
        deadline = time.time() + 300  # 5 min timeout
        while True:
            if time.time() > deadline:
                proc.kill()
                output_chunks.append("\n[spawn_agents] TIMEOUT (5min)\n")
                break
            # Check if process finished
            ret = proc.poll()
            # Read any available output
            try:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    chunk = os.read(master_fd, 4096)
                    output_chunks.append(chunk.decode("utf-8", errors="replace"))
            except OSError:
                break  # master closed (child exited)
            if ret is not None:
                # Drain remaining output
                try:
                    while True:
                        chunk = os.read(master_fd, 4096)
                        output_chunks.append(chunk.decode("utf-8", errors="replace"))
                except OSError:
                    pass
                break

        os.close(master_fd)
        rc = proc.wait() if proc.poll() is None else proc.returncode
        return rc, "".join(output_chunks)

    try:
        loop = asyncio.get_event_loop()
        rc, output = await loop.run_in_executor(None, _run_with_pty)
        elapsed = time.time() - t0
        return {"ok": rc == 0, "output": output, "elapsed": elapsed}
    except Exception as exc:
        return {"ok": False, "output": str(exc), "elapsed": time.time() - t0}


async def _dispatch_gemini(task: str) -> Dict[str, Any]:
    """Run Gemini CLI on a task. Returns {ok, output, elapsed}."""
    gemini_bin = shutil.which("gemini") or shutil.which("gemini-cli")
    if not gemini_bin:
        return {"ok": False, "output": "Gemini CLI not found. Install: npm i -g @google/gemini-cli", "elapsed": 0}

    t0 = time.time()
    try:
        # --yolo (alias: -y) auto-approves Gemini tool calls — required for
        # non-interactive script dispatch. Without it Gemini stalls on the
        # first sandbox/tool prompt and the subprocess hangs until timeout.
        proc = await asyncio.create_subprocess_exec(
            gemini_bin, "--yolo", "-p", task,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(REPO_ROOT),
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=180)
        elapsed = time.time() - t0
        output = stdout.decode("utf-8", errors="replace")
        return {"ok": proc.returncode == 0, "output": output, "elapsed": elapsed}
    except asyncio.TimeoutError:
        return {"ok": False, "output": "Gemini timed out (3min)", "elapsed": time.time() - t0}
    except Exception as exc:
        return {"ok": False, "output": str(exc), "elapsed": time.time() - t0}


async def _dispatch_gemini_review(task: str) -> Dict[str, Any]:
    """Run Gemini in code-review mode: prefixes task with structured review prompt."""
    review_prompt = (
        "You are a code reviewer. Review the following code or describe the review task, "
        "identify bugs, security issues, style violations, and improvement opportunities. "
        "Be specific and cite line numbers where possible.\n\n"
        f"REVIEW TASK: {task}"
    )
    return await _dispatch_gemini(review_prompt)


async def _dispatch_ollama_mac(task: str) -> Dict[str, Any]:
    """Dispatch a task to the local Mac Ollama backend."""
    import httpx as _httpx
    import time as _time
    t0 = _time.monotonic()
    try:
        async with _httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": MANAGER_MODEL or "qwen3.5:9b-nvfp4",
                "prompt": task,
                "stream": False,
            }
            r = await client.post(f"{OLLAMA_MAC_ENDPOINT}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            return {
                "ok": True,
                "output": data.get("response", ""),
                "elapsed": round(_time.monotonic() - t0, 2),
            }
    except Exception as e:
        return {"ok": False, "output": str(e), "elapsed": round(_time.monotonic() - t0, 2)}


async def _dispatch_lmstudio(endpoint: str, model: str, task: str, *, win_gpu: bool = False) -> Dict[str, Any]:
    """Send a task to an LM Studio OpenAI-compat endpoint. Win GPU is serialized."""
    try:
        import httpx
    except ImportError:
        return {"ok": False, "output": "httpx not installed (pip install httpx)", "elapsed": 0}

    async def _call() -> Dict[str, Any]:
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": task}],
                    "max_tokens": 4096,
                    "temperature": 0.2,
                }
                headers = {"Authorization": f"Bearer {LMS_API_KEY}"}
                r = await client.post(f"{endpoint}/v1/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                return {"ok": True, "output": content, "elapsed": time.time() - t0}
        except Exception as exc:
            return {"ok": False, "output": str(exc), "elapsed": time.time() - t0}

    if win_gpu:
        # Windows GPU: serialize all requests — one model at a time
        async with _WIN_GPU_LOCK:
            return await _call()
    else:
        return await _call()


async def _get_lmstudio_model(endpoint: str) -> str:
    """Get first loaded model from LM Studio endpoint."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Authorization": f"Bearer {LMS_API_KEY}"}
            r = await client.get(f"{endpoint}/v1/models", headers=headers)
            r.raise_for_status()
            models = r.json().get("data", [])
            if models:
                return models[0]["id"]
    except Exception:
        pass
    return "default"


# ── Orchestration ─────────────────────────────────────────────────────────────

async def dispatch(agent_name: str, task: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Dispatch a task to a named agent. Returns result dict."""
    agent_name = agent_name.lower().strip()

    if agent_name == "codex":
        return await _dispatch_codex(task)

    elif agent_name == "gemini":
        return await _dispatch_gemini(task)

    elif agent_name == "gemini-review":
        return await _dispatch_gemini_review(task)

    elif agent_name == "ollama-mac":
        return await _dispatch_ollama_mac(task)

    elif agent_name == "lmstudio-mac":
        m = model or await _get_lmstudio_model(LMS_MAC_ENDPOINT)
        return await _dispatch_lmstudio(LMS_MAC_ENDPOINT, m, task, win_gpu=False)

    elif agent_name == "lmstudio-win":
        m = model or await _get_lmstudio_model(LMS_WIN_ENDPOINT)
        return await _dispatch_lmstudio(LMS_WIN_ENDPOINT, m, task, win_gpu=True)

    elif agent_name == "all":
        # Parallel: Codex + Gemini + Ollama Mac + LM Studio Mac (non-GPU-bound)
        # Sequential: LM Studio Win (GPU-bound, serialized by lock)
        results = await asyncio.gather(
            _dispatch_codex(task),
            _dispatch_gemini(task),
            _dispatch_ollama_mac(task),
            _dispatch_lmstudio(LMS_MAC_ENDPOINT, model or await _get_lmstudio_model(LMS_MAC_ENDPOINT), task),
            _dispatch_lmstudio(LMS_WIN_ENDPOINT, model or await _get_lmstudio_model(LMS_WIN_ENDPOINT), task, win_gpu=True),
            return_exceptions=True,
        )
        agents_out = {}
        for name, res in zip(["codex", "gemini", "ollama-mac", "lmstudio-mac", "lmstudio-win"], results):
            if isinstance(res, Exception):
                agents_out[name] = {"ok": False, "output": str(res), "elapsed": 0}
            else:
                agents_out[name] = res
        all_ok = all(v.get("ok") for v in agents_out.values())
        return {"ok": all_ok, "results": agents_out}

    else:
        return {"ok": False, "output": f"Unknown agent: '{agent_name}'. Use: codex, gemini, lmstudio-mac, lmstudio-win, all"}


# ── Status report ─────────────────────────────────────────────────────────────

def print_status():
    agents = discover_agents()
    print("\n  Agent Availability\n  " + "─" * 46)
    for key, ag in agents.items():
        status = "✓  AVAILABLE" if ag.available else "✗  UNAVAILABLE"
        color = "\033[92m" if ag.available else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset}  {ag.name:<22}  {ag.detail}")
        if ag.version:
            print(f"             {'':22}  {ag.version}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dispatch tasks to AI coding agents (Codex, Gemini, LM Studio).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--task", "-t", help="Task description to send to the agent")
    parser.add_argument(
        "--agent", "-a",
        default="codex",
        choices=["codex", "gemini", "ollama-mac", "lmstudio-mac", "lmstudio-win", "all"],
        help="Agent to dispatch (default: codex)",
    )
    parser.add_argument("--model", "-m", help="Optional model override for LM Studio agents")
    parser.add_argument("--status", "-s", action="store_true", help="Show agent availability and exit")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if not args.task:
        parser.error("--task is required (or use --status to probe agents)")

    async def _run():
        result = await dispatch(args.agent, args.task, model=args.model)
        if args.json_output:
            print(json.dumps(result, indent=2))
        else:
            if "results" in result:
                # "all" mode
                for name, res in result["results"].items():
                    ok_str = "✓" if res.get("ok") else "✗"
                    elapsed = f"{res.get('elapsed', 0):.1f}s"
                    print(f"\n── {name} ({ok_str}, {elapsed}) " + "─" * 30)
                    print(res.get("output", ""))
            else:
                ok_str = "✓" if result.get("ok") else "✗"
                elapsed = f"{result.get('elapsed', 0):.1f}s"
                print(f"\n── {args.agent} ({ok_str}, {elapsed}) " + "─" * 30)
                print(result.get("output", ""))
        return 0 if result.get("ok") else 1

    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
