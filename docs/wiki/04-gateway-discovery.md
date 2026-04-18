# 04. Gateway Discovery — Commandeer-First Bootstrap

**TL;DR:** Probe all known candidate ports before running any install. If a compatible gateway is already listening, commandeer it — never start a duplicate.

---

## Root Cause (2026-04-07)

The old bootstrap only checked `127.0.0.1:18789` (OpenClaw default). If AlphaClaw or any other compatible fork was running on a different port, a second daemon was started — potentially conflicting with already-loaded agents and evicting models from GPU memory.

---

## Fix

```python
OPENCLAW_CANDIDATE_PORTS = [18789, 11435, 8080, 3000]

async def _find_running_gateway() -> str | None:
    extra = os.environ.get("OPENCLAW_EXTRA_PORTS", "")
    ports = OPENCLAW_CANDIDATE_PORTS + [int(p) for p in extra.split(",") if p.strip()]
    for port in ports:
        url = f"http://127.0.0.1:{port}"
        try:
            r = httpx.get(f"{url}/health", timeout=2)
            if r.status_code < 500:
                return url
        except Exception:
            continue
    return None

async def bootstrap():
    existing = await _find_running_gateway()
    if existing:
        os.environ["OPENCLAW_GATEWAY_URL"] = existing
        await _update_openclaw_config(existing)  # refresh config, do NOT restart daemon
        return
    # Nothing found — proceed with full install
    await _install_and_start_gateway()
```

### What "commandeer" means
- Write/refresh `openclaw.json` and agent workspace configs
- Set `OPENCLAW_GATEWAY_URL` env var
- **Do NOT** call `openclaw onboard --install-daemon` — this restarts the daemon and evicts loaded models

---

## Rules

1. **All bootstrap scripts must probe before install**
2. **Commandeer-first, install-last** — compatible service exists anywhere on localhost? Use it.
3. **Never stop/restart a running daemon during bootstrap**
4. **Always set a discoverable env var** (`OPENCLAW_GATEWAY_URL`) pointing to the live gateway URL
5. **Probe by interface** (`/health`, `/v1/models`), not by process name — works across forks and versions
6. **`OPENCLAW_CANDIDATE_PORTS`** defines probe order; `OPENCLAW_EXTRA_PORTS` extends it at runtime

---

## Related

- [Session log 2026-04-07](../LESSONS.md#2026-04-07--claude--idempotent-gateway-discovery-commandeer-first-bootstrap)
- Commit: `6bc40d0` (UTS) — feat(bootstrap): probe all candidate ports and commandeer any running gateway
- See also: [AlphaClaw docs/wiki/03-gateway-config.md](https://github.com/diazMelgarejo/AlphaClaw/blob/feature/MacOS-post-install/docs/wiki/03-gateway-config.md)
