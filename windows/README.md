# orama-system — Windows

Windows counterpart to `start.sh`. All Windows-specific files live here.

## Files

| File | Purpose |
|------|---------|
| `start.ps1` | Full Windows equivalent of `../start.sh` — same CLI modes |
| `install.ps1` | One-time idempotent setup (venv, deps, openclaw.json defaults) |
| `requirements-windows.txt` | Windows-only Python deps (pywin32, colorama, etc.) |

## First-time setup

```powershell
# Allow local scripts (once)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Install dependencies + write openclaw.json defaults
powershell -File .\windows\install.ps1
```

## Usage

```powershell
# Start all services + open browser
.\windows\start.ps1

# Start without opening browser
.\windows\start.ps1 --no-open

# Stop all
.\windows\start.ps1 --stop

# Status (port check + policy)
.\windows\start.ps1 --status

# Re-run LAN discovery
.\windows\start.ps1 --discover

# Validate model↔hardware affinity policy
.\windows\start.ps1 --hardware-policy
```

## CLI parity table

| `start.sh` mode | `start.ps1` equivalent |
|---|---|
| `./start.sh` | `.\windows\start.ps1` |
| `./start.sh --no-open` | `.\windows\start.ps1 --no-open` |
| `./start.sh --stop` | `.\windows\start.ps1 --stop` |
| `./start.sh --status` | `.\windows\start.ps1 --status` |
| `./start.sh --discover` | `.\windows\start.ps1 --discover` |
| `./start.sh --hardware-policy` | `.\windows\start.ps1 --hardware-policy` |
| `lsof -ti tcp:PORT` | `netstat -ano` + `Stop-Process` |
| `nc -z localhost PORT` | `TcpClient.ConnectAsync` |
| `open URL` | `Start-Process URL` |
| `ipconfig getifaddr en0` | `Get-NetIPAddress` / `Get-NetRoute` |
| `pid_on_port()` | `Get-PidOnPort` (netstat-based) |

## Architecture notes

- Windows GPU loads **ONE model at a time** — never configure parallel inference
- LM Studio on Windows listens on `localhost:1234` (not LAN-exposed by default)
- The Mac machine's LM Studio IP is read from `~/.openclaw/openclaw.json`
- Services log to `../.logs/{pt,orama,portal}.log` (same as macOS)
- `.paths.ps1` caches discovered paths (gitignored, auto-generated)
