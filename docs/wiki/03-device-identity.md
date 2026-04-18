# 03. Device Identity & GPU Crash Recovery

**TL;DR:** One inference backend per physical device. 30-second cooldown after any GPU crash. Probe local IPs before trusting any "remote" endpoint URL.

---

## Root Cause (2026-04-07)

- `WINDOWS_IP` misconfigured to the Mac's own LAN IP → probe succeeded → system treated one Mac as a two-node cluster → two models loaded simultaneously on same GPU
- Immediate retry after a 503/404 triggered repeated load/unload cycles, burning GPU memory bandwidth
- Silent `asyncio.sleep(N)` made crash recovery indistinguishable from a freeze

---

## Fix

### Local IP detection
```python
import socket

def _get_local_ips() -> set[str]:
    ips = set()
    # UDP routing trick: no packets sent, but reveals outbound LAN IP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
        except OSError:
            pass
    ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    return ips

def _is_local_endpoint(url: str, local_ips: set[str]) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    return host in local_ips or host in ("127.0.0.1", "localhost", "::1")
```

### One-role-per-device guard
```python
# After probing, zero out any "Windows" endpoint that resolves to a local IP
if _is_local_endpoint(REMOTE_WINDOWS_URL, local_ips):
    windows_ok = False  # same machine — do not assign Windows role
```

### Crash recovery with progress bar
```python
CRASH_RECOVERY_SECS = 30

async def _wait_with_progress(seconds: int, role: str, reason: str):
    for i in range(seconds, 0, -1):
        print(f"\r  [{role}] {reason} — retrying in {i}s   ", end="", flush=True)
        await asyncio.sleep(1)
    print()
```

### Error classification
```python
# In exception handler:
status = getattr(getattr(exc, "response", None), "status_code", None)
if status == 503:
    reason = "model loading"
elif status == 404:
    reason = "model unloaded"
else:
    reason = "backend offline"
await _wait_with_progress(CRASH_RECOVERY_SECS, role, reason)
```

---

## Rules

1. **Always call `_get_local_ips()` before trusting any "remote" endpoint**
2. **One role per physical device** — zero out probes whose host IP is in local_ips
3. **On same device: Ollama > LM Studio** deterministically
4. **Crash recovery ≥ 30 seconds** — GPU model cycles need this buffer
5. **Classify errors before sleeping** — 503 ≠ 404 ≠ ConnectError; each needs a distinct message
6. **Show a progress bar during recovery** — `asyncio.sleep(N)` is invisible

---

## Related

- [Session log 2026-04-07](../LESSONS.md#2026-04-07--claude--device-identity--gpu-crash-recovery)
- Commit: `8af62f5` (PT) — feat(routing): one-role-per-device guard + GPU crash recovery cooldown
