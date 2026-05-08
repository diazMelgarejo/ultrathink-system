# Cross-Platform Compatibility

> **Status:** v0.9.9.8 — macOS (primary), Linux (supported), Windows (via `windows/start.ps1`)
>
> **Last updated:** 2026-05-08

---

## Platform support matrix

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| `start.sh` | ✅ primary | ✅ supported | ❌ use `windows/start.ps1` |
| `start.ps1` | N/A | N/A | ✅ primary |
| Portal UI (`:8002`) | ✅ | ✅ | ✅ |
| `mac_probe.sh` | ✅ | ✅ | ❌ |
| LM Studio backend | `:1234` local | `:1234` local | `:1234` local |
| Ollama backend | `:11434` local | `:11434` local | `:11434` local |
| Service stop | `lsof` → `ss` → `fuser` | `ss` → `fuser` | `netstat -ano` + `Stop-Process` |
| Port probe | `nc -z` → `/dev/tcp` | `/dev/tcp` → `nc` | `TcpClient.ConnectAsync` |
| IP detection | `ipconfig getifaddr en0` | `ip route get 8.8.8.8` | `Get-NetRoute` gateway heuristic |
| Browser open | `open URL` | `xdg-open URL` | `Start-Process URL` |
| `setup_macos.py` | ✅ runs | ⏭ skipped (guard) | ⏭ not applicable |
| CI/Docker | ✅ with guard | ✅ minimal deps | N/A |

---

## `start.sh` — macOS vs Linux differences

### Port utilities

```bash
# pid_on_port — three-tier fallback
pid_on_port() {
  if command -v lsof &>/dev/null; then
    lsof -ti "tcp:$1" 2>/dev/null | head -1 || true         # macOS + Linux (if installed)
  elif command -v ss &>/dev/null; then
    ss -tlnp "sport = :$1" | grep -oP 'pid=\K\d+' | head -1 # Linux iproute2
  elif command -v fuser &>/dev/null; then
    fuser "$1/tcp" 2>/dev/null | awk '{print $1}' | head -1  # psmisc (last resort)
  fi
}

# _port_open — nc or bash /dev/tcp built-in
_port_open() {
  if command -v nc &>/dev/null; then
    nc -z localhost "$1" 2>/dev/null
  else
    (echo >/dev/tcp/localhost/"$1") 2>/dev/null              # always available in bash 3.2+
  fi
}
```

**Rule:** never assume `lsof` is present on Linux — Debian/Ubuntu minimal and Alpine omit it.  
**Rule:** never assume `nc` — scratch images and distroless containers omit it. Bash `/dev/tcp` is always available.

### Banner probes

All three banner probes (`mac LMS`, `win LMS`, `AlphaClaw`) run as parallel background subshells
writing to `mktemp` files. The probe helper `_nc_probe()` uses the same `nc` → `/dev/tcp` cascade:

```bash
_nc_probe() {
  local host="$1" port="$2"
  if command -v nc &>/dev/null; then
    nc -z -w 1 "$host" "$port" >/dev/null 2>&1
  else
    timeout 1 bash -c "(echo >/dev/tcp/${host}/${port})" 2>/dev/null
  fi
}
```

Total banner wall-time = `max(1s)` regardless of which three services are probed.

### macOS-only preflight guard

```bash
_OS_NAME="$(uname -s 2>/dev/null || echo Unknown)"
if [ "$_OS_NAME" = "Darwin" ] && [ -f "$SCRIPT_DIR/setup_macos.py" ]; then
  "$US_PYTHON" "$SCRIPT_DIR/setup_macos.py" --quiet 2>&1 | sed 's/^/  /' || true
elif [ "$_OS_NAME" != "Darwin" ]; then
  _info "svc" "Non-macOS host (${_OS_NAME}) — skipping setup_macos.py"
fi
```

`setup_macos.py` calls `xattr -cr` and `codesign -s -` — macOS-only binaries. The guard is
mandatory to prevent `FileNotFoundError` on Linux CI runners.

---

## Portal service controls — cross-platform implementation

The portal's `POST /api/stop` and `POST /api/restart/{service}` routes need to find and kill
processes by port — without `lsof` on all Linux variants.

```python
def _pid_on_port(port: int) -> Optional[int]:
    """lsof on macOS/Linux (if available), then ss (Linux), then fuser."""
    lsof = shutil.which("lsof")
    if lsof:
        out = subprocess.check_output([lsof, "-ti", f"tcp:{port}"], ...).decode().strip()
        pid_str = out.split("\n")[0].strip()
        return int(pid_str) if pid_str.isdigit() else None
    ss = shutil.which("ss")
    if ss:
        out = subprocess.check_output(["ss", "-tlnp", f"sport = :{port}"], ...).decode()
        m = re.search(r'pid=(\d+)', out)
        return int(m.group(1)) if m else None
    return None
```

`POST /api/restart/{service}` spawns a detached child via `subprocess.Popen(start_new_session=True)`:

```python
subprocess.Popen(
    cmd, cwd=cwd, env=env,
    stdout=lf, stderr=lf,
    start_new_session=True,   # detach from portal's process group
)
```

> **Known limitation:** `POST /api/restart/portal` kills the process that is currently serving the
> response. The HTTP reply may not be fully delivered before the process dies. To self-restart reliably
> the portal needs a supervisor (systemd, launchd, or a watchdog process). Deferred to v2.

---

## Windows (`windows/start.ps1`)

### CLI parity

| `start.sh` | `start.ps1` |
|---|---|
| `./start.sh` | `.\windows\start.ps1` |
| `./start.sh --no-open` | `.\windows\start.ps1 --no-open` |
| `./start.sh --stop` | `.\windows\start.ps1 --stop` (or `-Stop`) |
| `./start.sh --status` | `.\windows\start.ps1 --status` |
| `./start.sh --discover` | `.\windows\start.ps1 --discover` |
| `./start.sh --hardware-policy` | `.\windows\start.ps1 --hardware-policy` |

### Tool translations

| Unix tool | PowerShell equivalent |
|---|---|
| `lsof -ti tcp:PORT` | `netstat -ano` → LISTENING line → PID column |
| `nc -z localhost PORT` | `New-Object TcpClient; ConnectAsync().Wait(500ms)` |
| `open URL` | `Start-Process URL` |
| `ipconfig getifaddr en0` | `Get-NetRoute -DestPfx 0.0.0.0/0` → gateway → `.110` heuristic |
| `kill PID` | `Stop-Process -Id PID -Force` |
| `` cmd & `` (background) | `ProcessStartInfo(CreateNoWindow=true)` + async stream copy |
| `. .paths` | `. .paths.ps1` (dot-source) |

### UTF-8 requirement

PowerShell on Windows defaults to the system ANSI code page. The first two lines of
`start.ps1` and `install.ps1` force UTF-8 everywhere:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8       = '1'
```

Without this, JSON containing non-ASCII characters (model names, file paths with
accented characters) may be silently corrupted in subprocess stdout.

### GPU rule (Windows)

Windows loads **one model at a time** on the GPU. `install.ps1` prints this as a hard warning.
Never set `LM_STUDIO_WIN_ENDPOINTS` to multiple comma-separated URLs on a Windows node.

---

## `mac_probe.sh` — cross-platform hardware detection

See [`Perpetua-Tools/docs/cross-platform.md`](../../perplexity-api/Perpetua-Tools/docs/cross-platform.md) for full details.

Quick reference:

| Field | macOS | Linux |
|-------|-------|-------|
| `ram_gb` | `sysctl -n hw.memsize` ÷ 1GiB | `MemTotal` in `/proc/meminfo` ÷ 1GiB |
| `model_id` | `sysctl -n hw.model` | `/sys/devices/virtual/dmi/id/product_name` or `/proc/device-tree/model` |
| `gpu_cores` | `system_profiler SPDisplaysDataType` | `nvidia-smi --query-gpu=multiprocessor_count` → `lspci` device count |
| `private_ip` | `ipconfig getifaddr en0` | `ip route get 8.8.8.8` src field |
| `os` (new) | `"Darwin"` | `"Linux"` |

---

## Adding a new platform (checklist)

When extending to a new OS (e.g., Windows WSL, FreeBSD, Raspberry Pi OS):

- [ ] Run `bash scripts/mac_probe.sh` and verify JSON output is valid
- [ ] Check `pid_on_port()` cascade: does the OS have `lsof`, `ss`, or `fuser`?
- [ ] Check `_port_open()`: is `nc` present, or is `/dev/tcp` the only option?
- [ ] Verify `ipconfig`/`ip route`/`hostname -I` produces a non-loopback IP
- [ ] Does `setup_macos.py` need a guard? (Answer: yes for any non-Darwin OS)
- [ ] Update the support matrix table at the top of this file
- [ ] Add a platform-specific section below with tool translations
- [ ] Run `./start.sh --status` and confirm no `command not found` errors

---

## Known remaining macOS-only assumptions

| Location | Assumption | Impact if Linux |
|----------|------------|-----------------|
| `setup_macos.py` | `xattr`, `codesign` binaries | `FileNotFoundError` — guarded |
| `scripts/setup_codex.sh` | `/opt/homebrew/bin/codex` path | Codex symlink skipped — non-fatal |
| `scripts/refresh_policy_cache.py` | No platform guard | Should be fine — pure Python |
| Portal `_render_service_control_section()` hint text | Shows `./start.sh --stop` | Minor: shows wrong command on Windows — cosmetic only |
| `start.sh` IP detection (priority 3) | `network_autoconfig.py` uses `netifaces` | Needs `pip install netifaces` on Linux |
