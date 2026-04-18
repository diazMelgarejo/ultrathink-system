# 07. Startup & IP Detection — stdin Deadlock, load_dotenv, Concurrent Probing

**TL;DR:** `input()` in a daemon thread causes Abort trap: 6 at Python shutdown. Always `load_dotenv()` explicitly — shell-exported vars alone are unreliable. Fire all backend probes concurrently with `asyncio.create_task()` and await in two phases.

---

## Root Cause (2026-04-13)

Three separate failures on first `./start.sh` run:

1. **Abort trap: 6** — `_gather_alphaclaw_credentials()` spawned a daemon thread calling `input()`. After `t.join(30)` timeout, thread was still alive holding the stdin `BufferedReader` lock. Python interpreter shutdown tried to flush/close it → SIGABRT.

2. **Silent IP misconfiguration** — `agent_launcher.py` read `MAC_LMS_HOST`/`WINDOWS_IP` from env but neither was exported by `start.sh` or present in `.env`. Fallback hard-coded defaults (`.103`, `.100`) were always used; actual LAN addresses are `.110` (Mac LM Studio) and `.108` (Windows).

3. **Sequential backend probes** — probing local Ollama, local LM Studio, remote Mac LMS, and remote Windows sequentially added 2–5 seconds of wall-clock time to every startup.

---

## Fix

### stdin deadlock — three-layer fix

```python
# Layer 1: skip input() in non-interactive mode
if sys.stdin.isatty():
    t = threading.Thread(target=_gather_alphaclaw_credentials, daemon=True)
    t.start()
    t.join(30)
```

```bash
# Layer 2: start.sh — redirect stdin so input() gets instant EOFError
python "$SCRIPT_DIR/orchestrator.py" </dev/null
```

```python
# Layer 3: gateway Popen — prevent node process from inheriting broken fd
proc = subprocess.Popen(
    ["node", alphaclaw_bin],
    stdin=subprocess.DEVNULL,
    ...
)
```

### load_dotenv placement

```python
# agent_launcher.py — MUST be at module level before any env reads
from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)
```

### Concurrent backend probing

```python
async def probe_all_backends():
    # Fire all tasks at t=0
    t_local_ollama   = asyncio.create_task(_probe_ollama(LOCAL_URL))
    t_local_lms      = asyncio.create_task(_probe_lmstudio(LOCAL_LMS_URL))
    t_win_ollama     = asyncio.create_task(_probe_ollama(WIN_URL))
    t_win_lms        = asyncio.create_task(_probe_lmstudio(WIN_LMS_URL))

    # Await local first (faster, determines role assignments)
    local_ok, local_lms_ok = await asyncio.gather(t_local_ollama, t_local_lms)
    # Await LAN second (may still be in-flight but often done by now)
    win_ok, win_lms_ok = await asyncio.gather(t_win_ollama, t_win_lms)
    return local_ok, local_lms_ok, win_ok, win_lms_ok
```

### Self-correcting IP persistence

```python
def _persist_detected_ips(confirmed_endpoints: dict[str, str]):
    """Write confirmed live endpoints back to .env so next run is self-correcting."""
    env_path = Path(".env")
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    for key, val in confirmed_endpoints.items():
        lines = [l for l in lines if not l.startswith(f"{key}=")]
        lines.append(f"{key}={val}")
    env_path.write_text("\n".join(lines) + "\n")
```

---

## Rules

1. **Never call `input()` in a daemon thread** — use `sys.stdin.isatty()` guard + non-interactive mode
2. **Redirect stdin in start.sh** — `python script.py </dev/null` for all orchestrator processes
3. **`stdin=subprocess.DEVNULL`** on any `Popen` for long-running child processes
4. **Always call `load_dotenv()` explicitly** — shell-exported vars alone are unreliable
5. **Fire all backend probes concurrently** with `asyncio.create_task()`; await in phases
6. **`_persist_detected_ips()`** after every successful probe run — makes configuration self-correcting

---

## Related

- [Session log 2026-04-13](../LESSONS.md#2026-04-13--claude--startup-fix-ip-detection-stdin-deadlock-concurrent-backend-probing)
- Perplexity-Tools companion entry: [same topic, PT side](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/wiki/06-startup-ip-detection.md)
