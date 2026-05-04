#!/usr/bin/env python3
"""
scripts/discover.py
LM Studio Auto-Discovery Hub — Layer A.
Always probes by default (no TTL skip). Pass --cached to reuse warm gossip.
Idempotent: writes nothing if state hash is unchanged.
"""

from __future__ import annotations
import argparse, asyncio, fcntl, hashlib, json, logging, os, re, shutil, socket, sys, time
import urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────
OPENCLAW_DIR        = Path.home() / ".openclaw"
STATE_DIR           = OPENCLAW_DIR / "state"
BACKUPS_DIR         = STATE_DIR / "backups"
ARCHIVE_DIR         = STATE_DIR / "archive"
PROFILES_DIR        = OPENCLAW_DIR / "profiles"
DISCOVERY_JSON      = STATE_DIR / "discovery.json"
LAST_DISCOVERY_JSON = STATE_DIR / "last_discovery.json"
RECOVERY_SOURCE_TXT = STATE_DIR / "recovery_source.txt"
LOCK_FILE           = STATE_DIR / ".discover.lock"
DEFAULT_LOCK_FILE   = LOCK_FILE
OPENCLAW_JSON       = OPENCLAW_DIR / "openclaw.json"

LM_STUDIO_PORT     = 1234
SUBNET             = "192.168.254"
PROBE_TIMEOUT      = 0.2
MODEL_API_TIMEOUT  = 4
MAX_BACKUPS        = 30
ARCHIVE_DAYS       = 30
GOSSIP_TTL_SECONDS = 300

# ── Repo discovery ────────────────────────────────────────────────────────────

def _resolve_perpetua_root_env() -> Path | None:
    """Resolve canonical Perpetua root env var with legacy fallback.

    Precedence:
      1) PERPETUA_TOOLS_ROOT (canonical)
      2) PERPETUA_TOOLS_PATH (legacy compatibility)
    """
    root = (
        os.environ.get("PERPETUATOOLSROOT", "").strip()
        or os.environ.get("PERPETUA_TOOLS_ROOT", "").strip()
    )
    legacy = os.environ.get("PERPETUA_TOOLS_PATH", "").strip()
    selected = root or legacy
    return Path(selected).expanduser() if selected else None


def get_repo_paths() -> dict:
    base = Path.home() / "Documents" / "Terminal xCode" / "claude" / "OpenClaw"
    candidates = {
        "alphaclaw": [Path(os.environ.get("ALPHACLAW_INSTALL_DIR", "~/.alphaclaw")).expanduser()],
        "perpetua_tools": [
            base / "perplexity-api" / "Perpetua-Tools",
            Path.home() / "Perpetua-Tools",
        ],
        "orama_system": [
            base / "orama-system",
            Path.home() / "orama-system",
        ],
    }
    result = {}
    for name, paths in candidates.items():
        env_key = name.upper() + "_PATH"
        if name == "perpetua_tools":
            result[name] = _resolve_perpetua_root_env() or next((p for p in paths if p.exists()), None)
        elif env_val := os.environ.get(env_key):
            result[name] = Path(env_val).expanduser()
        else:
            result[name] = next((p for p in paths if p.exists()), None)
    return result

# ── Hardware affinity policy ──────────────────────────────────────────────────

def _simple_policy_parse(text: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {"windows_only": [], "mac_only": [], "shared": []}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1]
            current = key if key in parsed else None
            continue
        if current and stripped.startswith("-"):
            value = stripped[1:].strip().strip('"').strip("'")
            if value:
                parsed[current].append(value)
    return parsed

def load_policy(policy_path: Path | None = None) -> dict[str, Any]:
    """Load Perpetua-Tools' canonical hardware policy."""
    if policy_path is None:
        pt_root = _resolve_perpetua_root_env() or get_repo_paths().get("perpetua_tools")
        if not pt_root:
            return {"windows_only": [], "mac_only": [], "shared": []}
        policy_path = Path(pt_root) / "config" / "model_hardware_policy.yml"
    if not policy_path.exists():
        return {"windows_only": [], "mac_only": [], "shared": []}
    text = policy_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
    except Exception:
        loaded = _simple_policy_parse(text)
    return {
        "windows_only": list(loaded.get("windows_only", []) or []),
        "mac_only": list(loaded.get("mac_only", []) or []),
        "shared": list(loaded.get("shared", []) or []),
    }

def _import_pt_hardware_policy():
    pt_root = _resolve_perpetua_root_env()
    if not pt_root:
        raise ImportError("PERPETUATOOLSROOT/PERPETUA_TOOLS_ROOT not set")
    if str(pt_root) not in sys.path:
        sys.path.insert(0, str(pt_root))
    import importlib
    return importlib.import_module("utils.hardware_policy")


def _filter_models_for_platform_local(models: list, platform: str, policy: dict) -> list:
    normalized = platform.lower().strip()
    if normalized == "mac":
        forbidden = {m.lower() for m in policy.get("windows_only", [])}
    elif normalized == "win":
        forbidden = {m.lower() for m in policy.get("mac_only", [])}
    else:
        forbidden = set()
    return [m for m in models if str(m).lower() not in forbidden]


try:
    _hw_policy = _import_pt_hardware_policy()
    filter_models_for_platform = _hw_policy.filter_models_for_platform
except ImportError as exc:
    logging.critical(
        "Cannot import PT hardware_policy: %s. Falling back to local filter implementation.", exc
    )
    filter_models_for_platform = _filter_models_for_platform_local

def filter_endpoints_for_policy(endpoints: dict, policy: dict | None = None) -> dict:
    """Return a copy of endpoint discovery data with platform-forbidden models removed."""
    policy = policy if policy is not None else load_policy()
    filtered: dict[str, dict | None] = {}
    for platform in ("mac", "win"):
        endpoint = endpoints.get(platform)
        if not endpoint:
            filtered[platform] = endpoint
            continue
        copied = dict(endpoint)
        copied["models"] = filter_models_for_platform(endpoint.get("models", []), platform, policy)
        filtered[platform] = copied
    return filtered

# ── Probing ───────────────────────────────────────────────────────────────────

def probe_models(base_url: str, timeout: float = MODEL_API_TIMEOUT):
    try:
        req = urllib.request.Request(
            f"{base_url}/v1/models",
            headers={"Authorization": "Bearer lm-studio"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
            models = sorted(m["id"] for m in data.get("data", []))
            return models or None
    except Exception:
        return None

async def _check_port(ip: str, port: int):
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=PROBE_TIMEOUT)
        w.close(); await w.wait_closed()
        return ip
    except Exception:
        return None

async def scan_subnet_async(subnet: str, port: int, exclude: set):
    tasks = [_check_port(f"{subnet}.{i}", port) for i in range(1, 255)
             if f"{subnet}.{i}" not in exclude]
    return [ip for ip in await asyncio.gather(*tasks) if ip]

def _mac_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.254.1", 80))
        ip = s.getsockname()[0]; s.close()
        return ip if ip.startswith("192.168.254.") else None
    except Exception:
        return None

def discover_endpoints() -> dict:
    result = {"mac": None, "win": None}
    mac_models = probe_models("http://localhost:1234")
    if mac_models:
        result["mac"] = {"ip": "localhost", "models": mac_models}

    last = _load_json(LAST_DISCOVERY_JSON)
    win_last_ip = (last or {}).get("endpoints", {}).get("win", {}).get("ip", "")
    mac_lan = _mac_lan_ip()
    exclude = {"localhost", "127.0.0.1"}
    if mac_lan:
        exclude.add(mac_lan)

    if win_last_ip and win_last_ip not in exclude:
        win_models = probe_models(f"http://{win_last_ip}:1234")
        if win_models:
            result["win"] = {"ip": win_last_ip, "models": win_models}

    if not result["win"]:
        subnet = mac_lan.rsplit(".", 1)[0] if mac_lan else SUBNET
        for ip in asyncio.run(scan_subnet_async(subnet, LM_STUDIO_PORT, exclude)):
            models = probe_models(f"http://{ip}:1234")
            if models:
                result["win"] = {"ip": ip, "models": models}
                break

    return result

# ── Hash & state ──────────────────────────────────────────────────────────────

def compute_hash(endpoints: dict) -> str:
    mac = endpoints.get("mac") or {}
    win = endpoints.get("win") or {}
    key = json.dumps({
        "mac_ip": mac.get("ip", ""),
        "mac_models": sorted(mac.get("models", [])),
        "win_ip": win.get("ip", ""),
        "win_models": sorted(win.get("models", [])),
    }, sort_keys=True)
    return hashlib.sha1(key.encode()).hexdigest()

def _load_json(path: Path):
    try: return json.loads(path.read_text())
    except Exception: return None

def _lock_path() -> Path:
    if LOCK_FILE != DEFAULT_LOCK_FILE:
        return LOCK_FILE
    return STATE_DIR / ".discover.lock"

def save_discovery_state(endpoints: dict, tier: int = 1):
    endpoints = filter_endpoints_for_policy(endpoints)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    mac = endpoints.get("mac") or {}
    win = endpoints.get("win") or {}
    state = {
        "schema": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": compute_hash(endpoints),
        "recovery_tier": tier,
        "endpoints": {
            "mac": {"ip": mac.get("ip", ""), "port": LM_STUDIO_PORT, "reachable": bool(mac)},
            "win": {"ip": win.get("ip", ""), "port": LM_STUDIO_PORT, "reachable": bool(win)},
        },
        "models": {"mac": mac.get("models", []), "win": win.get("models", [])},
    }
    DISCOVERY_JSON.write_text(json.dumps(state, indent=2))
    LAST_DISCOVERY_JSON.write_text(json.dumps(state, indent=2))
    RECOVERY_SOURCE_TXT.write_text(f"tier{tier}\n")

# ── Backup / archive ──────────────────────────────────────────────────────────

def backup_current_state():
    if not LAST_DISCOVERY_JSON.exists(): return
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copy2(LAST_DISCOVERY_JSON, BACKUPS_DIR / f"{ts}.json")
    _enforce_backup_limits()

def _enforce_backup_limits():
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - (ARCHIVE_DAYS * 86400)
    backups = sorted(BACKUPS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    for f in list(backups):
        if f.stat().st_mtime < cutoff:
            shutil.move(str(f), str(ARCHIVE_DIR / f.name))
            backups.remove(f)
    backups = sorted(BACKUPS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    while len(backups) > MAX_BACKUPS:
        backups[0].unlink()
        backups = backups[1:]

# ── Config patching ───────────────────────────────────────────────────────────

def patch_openclaw_json(endpoints: dict):
    if not _resolve_perpetua_root_env():
        logging.critical(
            "PERPETUATOOLSROOT/PERPETUA_TOOLS_ROOT not set. Refusing to write openclaw.json."
        )
        raise SystemExit(1)
    if not OPENCLAW_JSON.exists(): return
    cfg = _load_json(OPENCLAW_JSON)
    if not cfg: return
    endpoints = filter_endpoints_for_policy(endpoints)
    providers = cfg.setdefault("models", {}).setdefault("providers", {})
    mac = endpoints.get("mac")
    win = endpoints.get("win")
    if mac:
        url = "http://localhost:1234/v1" if mac["ip"] == "localhost" else f"http://{mac['ip']}:1234/v1"
        providers.setdefault("lmstudio-mac", {})["baseUrl"] = url
        providers["lmstudio-mac"]["models"] = [
            {"id": m, "name": f"Mac LMS — {m}", "contextWindow": 32768,
             "maxTokens": 8192, "cost": {"input": 0, "output": 0}}
            for m in mac["models"] if "embed" not in m.lower()
        ]
    if win:
        providers.setdefault("lmstudio-win", {})["baseUrl"] = f"http://{win['ip']}:1234/v1"
        providers["lmstudio-win"]["models"] = [
            {"id": m, "name": f"Win LMS — {m}", "contextWindow": 32768,
             "maxTokens": 8192, "cost": {"input": 0, "output": 0}}
            for m in win["models"] if "embed" not in m.lower()
        ]
    cfg.setdefault("meta", {})["lastTouchedAt"] = datetime.now(timezone.utc).isoformat()
    OPENCLAW_JSON.write_text(json.dumps(cfg, indent=2))

def patch_devices_yml(mac_ip: str, win_ip: str, pt_repo: Path):
    f = pt_repo / "config" / "devices.yml"
    if not f.exists(): return
    content = original = f.read_text()
    content = re.sub(
        r'(- id: "mac-studio".*?lan_ip:\s*")[^"]+(")',
        lambda m: m.group(1) + mac_ip + m.group(2),
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'(- id: "win-rtx3080".*?lan_ip:\s*")[^"]+(")',
        lambda m: m.group(1) + win_ip + m.group(2),
        content, flags=re.DOTALL
    )
    if content != original:
        f.write_text(content)

def patch_models_yml(mac_ip: str, win_ip: str, pt_repo: Path):
    f = pt_repo / "config" / "models.yml"
    if not f.exists(): return
    content = original = f.read_text()
    mac_url = "http://localhost:1234" if mac_ip == "localhost" else f"http://{mac_ip}:1234"
    content = re.sub(r'(\$\{LM_STUDIO_MAC_ENDPOINT:-)[^}]+(\})', rf'\g<1>{mac_url}\2', content)
    content = re.sub(r'(\$\{LM_STUDIO_WIN_ENDPOINTS:-)[^}:,\n]+', rf'\g<1>http://{win_ip}', content)
    if content != original:
        f.write_text(content)

def write_env_lmstudio(endpoints: dict, repo_paths: dict):
    endpoints = filter_endpoints_for_policy(endpoints)
    mac = endpoints.get("mac") or {}
    win = endpoints.get("win") or {}
    mac_ip = mac.get("ip", "")
    win_ip = win.get("ip", "")
    mac_url = "http://localhost:1234" if mac_ip == "localhost" else f"http://{mac_ip}:1234"
    win_url = f"http://{win_ip}:1234" if win_ip else ""
    mac_models = mac.get("models", [])
    win_models = win.get("models", [])
    mac_primary = next((m for m in mac_models if "embed" not in m.lower()), "")
    win_primary = (next((m for m in win_models if "27b" in m.lower()), None) or
                   next((m for m in win_models if "embed" not in m.lower()), ""))
    win_fallback = next((m for m in win_models if m != win_primary and "embed" not in m.lower()), "")
    tier = (_load_json(LAST_DISCOVERY_JSON) or {}).get("recovery_tier", 1)
    content = (
        f"# Auto-generated by ~/.openclaw/scripts/discover.py — do not edit manually\n"
        f"# Last updated: {datetime.now(timezone.utc).isoformat()} | recovery_tier: {tier}\n"
        f"LM_STUDIO_MAC_ENDPOINT={mac_url}\n"
        f"LM_STUDIO_WIN_ENDPOINTS={win_url}\n"
        f"LMS_MAC_MODEL={mac_primary}\n"
        f"LMS_WIN_MODEL={win_primary}\n"
        f"LMS_WIN_FALLBACK_MODEL={win_fallback}\n"
        f"LM_STUDIO_API_TOKEN=lm-studio\n"
    )
    for repo_path in repo_paths.values():
        if repo_path and Path(repo_path).exists():
            (Path(repo_path) / ".env.lmstudio").write_text(content)

# ── Recovery tiers ────────────────────────────────────────────────────────────

def _state_to_ep(state):
    if not state or not state.get("endpoints"): return None
    return {
        "mac": {"ip": state["endpoints"]["mac"]["ip"], "models": state["models"]["mac"]}
              if state["endpoints"]["mac"]["reachable"] else None,
        "win": {"ip": state["endpoints"]["win"]["ip"], "models": state["models"]["win"]}
              if state["endpoints"]["win"]["reachable"] else None,
    }

def _load_tier2(): return _state_to_ep(_load_json(LAST_DISCOVERY_JSON))
def _load_tier3():
    if not BACKUPS_DIR.exists(): return None
    for b in sorted(BACKUPS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        ep = _state_to_ep(_load_json(b))
        if ep: return ep
    return None
def _load_tier4(profile="lan-full"):
    return _state_to_ep(_load_json(PROFILES_DIR / f"{profile}.json"))

# ── File lock ─────────────────────────────────────────────────────────────────

class _Lock:
    def __init__(self, timeout=10.0):
        self._timeout = timeout; self._fd = None
    def __enter__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        lock_path = _lock_path()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(lock_path, "w")
        deadline = time.time() + self._timeout
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB); return self
            except BlockingIOError:
                if time.time() > deadline: raise TimeoutError("discovery lock timeout")
                time.sleep(0.2)
    def __exit__(self, *_):
        if self._fd:
            fcntl.flock(self._fd, fcntl.LOCK_UN); self._fd.close()
            try: _lock_path().unlink()
            except FileNotFoundError: pass

# ── Main discovery flow ───────────────────────────────────────────────────────

def run_discovery(force: bool = True, cached: bool = False) -> int:
    """Probe endpoints and update configs.

    Default behaviour is always-fresh (force=True).  Pass cached=True (or
    use the --cached CLI flag) to skip the probe when gossip is still warm
    (within GOSSIP_TTL_SECONDS).  The legacy --force flag is kept for
    backwards compatibility but is now a no-op (force is already the default).
    """
    with _Lock():
        if cached and not force and DISCOVERY_JSON.exists():
            state = _load_json(DISCOVERY_JSON)
            if state:
                age = (datetime.now(timezone.utc) -
                       datetime.fromisoformat(state["timestamp"])).total_seconds()
                if age < GOSSIP_TTL_SECONDS:
                    return 0

        print("🔍 Probing LM Studio endpoints...", file=sys.stderr)
        endpoints = discover_endpoints()
        tier = 1

        if not endpoints["mac"] and not endpoints["win"]:
            print("⚠️  No live endpoints — trying recovery tiers...", file=sys.stderr)
            for fn, t, name in [(_load_tier2, 2, "last known good"),
                                  (_load_tier3, 3, "newest backup"),
                                  (lambda: _load_tier4("lan-full"), 4, "lan-full profile")]:
                ep = fn()
                if ep: endpoints = ep; tier = t; print(f"  → tier {t}: {name}", file=sys.stderr); break
            if not endpoints["mac"] and not endpoints["win"]:
                print("❌ All tiers failed.", file=sys.stderr)
                RECOVERY_SOURCE_TXT.write_text("tier_failed\n")
                return 1
        else:
            last = _load_json(LAST_DISCOVERY_JSON)
            if last:
                for role in ("mac", "win"):
                    if not endpoints[role] and last["endpoints"][role]["reachable"]:
                        endpoints[role] = {"ip": last["endpoints"][role]["ip"],
                                           "models": last["models"][role]}
                        print(f"⚠️  {role} unreachable — preserving last-good", file=sys.stderr)

        endpoints = filter_endpoints_for_policy(endpoints)
        new_hash = compute_hash(endpoints)
        last = _load_json(LAST_DISCOVERY_JSON)
        if last and last.get("hash") == new_hash:
            last["timestamp"] = datetime.now(timezone.utc).isoformat()
            if tier != last.get("recovery_tier", 1):
                last["recovery_tier"] = tier  # reflect actual recovery tier used this run
                RECOVERY_SOURCE_TXT.write_text(f"tier{tier}\n")
            DISCOVERY_JSON.write_text(json.dumps(last, indent=2))
            LAST_DISCOVERY_JSON.write_text(json.dumps(last, indent=2))
            print("✅ No changes. Config is current.", file=sys.stderr)
            return 0

        print("🔄 Changes detected — updating configs...", file=sys.stderr)
        backup_current_state()
        repo_paths = get_repo_paths()
        pt_repo = repo_paths.get("perpetua_tools")
        mac = endpoints.get("mac") or {}
        win = endpoints.get("win") or {}

        patch_openclaw_json(endpoints)
        print("  ✓ openclaw.json", file=sys.stderr)
        if pt_repo:
            patch_devices_yml(mac.get("ip", ""), win.get("ip", ""), pt_repo)
            patch_models_yml(mac.get("ip", ""), win.get("ip", ""), pt_repo)
            print("  ✓ Perpetua-Tools config/", file=sys.stderr)
        write_env_lmstudio(endpoints, repo_paths)
        print("  ✓ .env.lmstudio written", file=sys.stderr)
        save_discovery_state(endpoints, tier)
        print(f"  ✓ state saved (tier {tier})", file=sys.stderr)
        if mac.get("ip"): print(f"  Mac: {mac['ip']} — {len(mac.get('models', []))} models", file=sys.stderr)
        if win.get("ip"): print(f"  Win: {win['ip']} — {len(win.get('models', []))} models", file=sys.stderr)
        return 0

# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_status():
    state = _load_json(LAST_DISCOVERY_JSON) or _load_json(DISCOVERY_JSON)
    if not state: print("No discovery state. Run: discover.py --status (after a probe)"); return
    print(f"Tier:    {state.get('recovery_tier', '?')}")
    print(f"Updated: {state.get('timestamp', '?')}")
    for role, ep in state.get("endpoints", {}).items():
        ok = "✅" if ep["reachable"] else "❌"
        print(f"  {role}: {ok} {ep['ip']}:{ep['port']} — {len(state['models'].get(role, []))} models")
    src = RECOVERY_SOURCE_TXT.read_text().strip() if RECOVERY_SOURCE_TXT.exists() else "unknown"
    print(f"Source:  {src}")

def _cmd_restore(target: str):
    if target == "latest":
        ep = _load_tier3()
    elif target.startswith("profile:"):
        ep = _load_tier4(target.split(":", 1)[1])
    else:
        matches = sorted(BACKUPS_DIR.glob(f"{target}*.json")) if BACKUPS_DIR.exists() else []
        ep = _state_to_ep(_load_json(matches[-1])) if matches else None
    if not ep: print(f"Nothing found for '{target}'."); return
    ep = filter_endpoints_for_policy(ep)
    backup_current_state()
    repo_paths = get_repo_paths()
    pt_repo = repo_paths.get("perpetua_tools")
    mac = ep.get("mac") or {}; win = ep.get("win") or {}
    patch_openclaw_json(ep)
    if pt_repo:
        patch_devices_yml(mac.get("ip", ""), win.get("ip", ""), pt_repo)
        patch_models_yml(mac.get("ip", ""), win.get("ip", ""), pt_repo)
    write_env_lmstudio(ep, repo_paths)
    save_discovery_state(ep, tier=99)
    RECOVERY_SOURCE_TXT.write_text("manual_restore\n")
    print(f"✅ Restored: Mac={mac.get('ip', '?')} Win={win.get('ip', '?')}")

def main():
    p = argparse.ArgumentParser(
        description="LM Studio Auto-Discovery (always probes by default; use --cached to skip when warm)",
    )
    p.add_argument("--cached",  action="store_true",
                   help="Skip probe if gossip is still fresh (within TTL). Default is always re-probe.")
    p.add_argument("--force",   action="store_true",
                   help="[legacy no-op] Re-probe is now the default; kept for backwards compat.")
    p.add_argument("--status",  action="store_true", help="Show current state (no probe)")
    p.add_argument("--restore", metavar="TARGET",    help="latest | YYYY-MM-DD | profile:name")
    p.add_argument("--prune",   action="store_true", help="Manually prune backups")
    args = p.parse_args()
    if args.status:  _cmd_status(); sys.exit(0)
    if args.restore: _cmd_restore(args.restore); sys.exit(0)
    if args.prune:   _enforce_backup_limits(); print("✅ Pruned."); sys.exit(0)
    # When --cached is given, respect TTL (skip if warm); otherwise always probe.
    if args.cached:
        sys.exit(run_discovery(force=False, cached=True))
    else:
        sys.exit(run_discovery(force=True, cached=False))

if __name__ == "__main__":
    main()
