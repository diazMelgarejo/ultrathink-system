#!/bin/bash
# start.sh — orama-system thin delegator  v0.9.9.8
#
# orama-system is Layer 3 — orchestration / meta-intelligence / delegate runtime.
# All gateway/backend/mode decisions are PT's responsibility (Perpetua-Tools).
# This script: macOS preflight → delegate to PT lifecycle → start orama services.
#
# Starts three services:
#   :8000  Perpetua-Tools orchestrator    (PT — Layer 2)
#   :8001  orama-system reasoning engine  (US)
#   :8002  Portal dashboard
#
# Usage:
#   ./start.sh             — start all, open browser
#   ./start.sh --no-open   — start all, skip browser
#   ./start.sh --stop      — kill all three services
#   ./start.sh --status    — show which ports are listening
#   ./start.sh --discover  — re-run path discovery, rewrite .paths, exit
#   ./start.sh --hardware-policy — validate model↔hardware affinity and exit
#
# Path config: .paths (gitignored, auto-generated, user-editable)
# Template:    .paths.example

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PATHS_FILE="$SCRIPT_DIR/.paths"

# ── structured logging ─────────────────────────────────────────────────────────
# Levels: INFO (normal flow), WARN (non-fatal, needs attention), ERROR (fatal),
#         DEBUG (variable tracing — set ORAMA_DEBUG=1 to enable)
# Format: [HH:MM:SS] LEVEL  stage  message
#   stage = path|ip|pt|svc — makes grep-based debugging trivial:
#   e.g.  grep '\[ip\]' start.sh.log
#         grep 'WARN'    start.sh.log
_LOG_START="$(date +%s)"
_log() {
  local level="$1" stage="$2"; shift 2
  local ts; ts="$(date +%H:%M:%S)"
  local elapsed=$(( $(date +%s) - _LOG_START ))
  local msg="[${ts}] ${level}  [${stage}]  $*  (+${elapsed}s)"
  echo "$msg"
  # Append to session log for post-mortem analysis
  echo "$msg" >> "${SCRIPT_DIR}/.logs/startup-$(date +%Y%m%d).log" 2>/dev/null || true
}
_info()  { _log "INFO " "$@"; }
_warn()  { _log "WARN " "$@"; }
_err()   { _log "ERROR" "$@"; }
_debug() { [[ "${ORAMA_DEBUG:-0}" == "1" ]] && _log "DEBUG" "$@" || true; }
_var()   {
  # Trace a variable: _var stage VAR_NAME value [source]
  local stage="$1" name="$2" val="$3" src="${4:-}"
  local src_tag="${src:+  ← ${src}}"
  _debug "$stage" "${name}=${val}${src_tag}"
}

# ── path resolution: .paths → git siblings → hardcoded sibling default ─────────

_discover_pt_dir() {
  local candidate
  candidate="$(cd "$SCRIPT_DIR/../perplexity-api/Perpetua-Tools" 2>/dev/null && pwd || true)"
  if [ -f "${candidate}/orchestrator/fastapi_app.py" ]; then
    echo "$candidate"; return
  fi
  local root
  root="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || echo "")"
  if [ -n "$root" ]; then
    local parent; parent="$(dirname "$root")"
    for d in "$parent"/*/; do
      if [ -f "${d}orchestrator/fastapi_app.py" ]; then
        cd "$d" && pwd; return
      fi
    done
  fi
  echo "$candidate"
}

_best_python() {
  local dir="$1"
  local venv_py="${dir}/.venv/bin/python"
  if [ -x "$venv_py" ]; then echo "$venv_py"
  else which python3 2>/dev/null || which python
  fi
}

# Load .paths if it exists
PT_DIR=""; PT_PYTHON=""; US_PYTHON=""
if [ -f "$PATHS_FILE" ]; then
  # shellcheck source=/dev/null
  source "$PATHS_FILE"
  _debug "path" "loaded .paths — PT_DIR=${PT_DIR}"
else
  _debug "path" ".paths not found — will discover"
fi

# Fill in any missing values via discovery
if [ -z "${PT_DIR:-}" ]; then
  PT_DIR="$(_discover_pt_dir)"
  _debug "path" "PT_DIR discovered=${PT_DIR}"
fi
if [ -z "${PT_PYTHON:-}" ]; then
  PT_PYTHON="$(_best_python "${PT_DIR:-$SCRIPT_DIR}")"
  _debug "path" "PT_PYTHON=${PT_PYTHON}"
fi
if [ -z "${US_PYTHON:-}" ]; then
  US_PYTHON="$(_best_python "$SCRIPT_DIR")"
  _debug "path" "US_PYTHON=${US_PYTHON}"
fi

if [ -z "${PT_DIR:-}" ] || [ ! -f "${PT_DIR}/orchestrator/alphaclaw_manager.py" ]; then
  _warn "path" "PT_DIR not found or missing alphaclaw_manager.py — PT resolve will be skipped"
else
  _info "path" "PT_DIR=${PT_DIR}"
fi

# ── Symlink Validation (from 1675ab4 — auto-repair PT sibling symlinks) ──────
# Ensures network_autoconfig.py and lib/shared/agentic_stack are wired to live
# PT paths. Uses relative path calculation so symlinks survive directory moves.
_ensure_symlink() {
  local link="$1" target="$2"
  if [ ! -L "$link" ]; then
    _info "link" "creating missing symlink: $link → $target"
    ln -s "$target" "$link"
  elif [ ! -e "$link" ]; then
    _warn "link" "broken symlink: $link — attempting re-link to $target"
    if [ -e "$target" ]; then
      rm "$link"
      ln -s "$target" "$link"
      _info "link" "re-linked: $link → $target"
    fi
  fi
}

if [ -n "${PT_DIR:-}" ]; then
  # network_autoconfig.py — Python module for LAN IP detection
  _PT_NET_CONFIG="${PT_DIR}/packages/net_utils/network_autoconfig.py"
  if [ -f "$_PT_NET_CONFIG" ]; then
    _REL_NET_CONFIG="$(_PYLINK_SRC="$_PT_NET_CONFIG" _PYLINK_BASE="$SCRIPT_DIR" \
      python3 -c "import os; print(os.path.relpath(os.environ['_PYLINK_SRC'],os.environ['_PYLINK_BASE']))" 2>/dev/null || true)"
    [ -n "$_REL_NET_CONFIG" ] && _ensure_symlink "network_autoconfig.py" "$_REL_NET_CONFIG"
  fi

  # lib/shared/agentic_stack — shared library from PT
  _PT_STACK="${PT_DIR}/packages/agentic-stack"
  if [ -d "$_PT_STACK" ]; then
    mkdir -p "$SCRIPT_DIR/lib/shared"
    _REL_STACK="$(_PYLINK_SRC="$_PT_STACK" _PYLINK_BASE="$SCRIPT_DIR/lib/shared" \
      python3 -c "import os; print(os.path.relpath(os.environ['_PYLINK_SRC'],os.environ['_PYLINK_BASE']))" 2>/dev/null || true)"
    if [ -n "$_REL_STACK" ]; then
      (cd "$SCRIPT_DIR/lib/shared" && _ensure_symlink "agentic_stack" "$_REL_STACK")
    fi
  fi
fi

# Write .paths on first run (or if --discover requested)
if [ ! -f "$PATHS_FILE" ] || [[ "${1:-}" == "--discover" ]]; then
  cat > "$PATHS_FILE" << PATHSEOF
# .paths — auto-generated by ./start.sh on $(date '+%Y-%m-%d %H:%M:%S')
# Edit to override. See .paths.example for documentation.
# Regenerate: rm .paths && ./start.sh

PT_DIR="${PT_DIR}"
PT_PYTHON="${PT_PYTHON}"
US_PYTHON="${US_PYTHON}"
PATHSEOF
  echo "  Paths written to .paths (gitignored)"
  [[ "${1:-}" == "--discover" ]] && exit 0
fi

PT_PORT=${PT_PORT:-8000}
US_PORT=${US_PORT:-8001}
PORTAL_PORT=${PORTAL_PORT:-8002}
PORTAL_URL="http://localhost:${PORTAL_PORT}"

LOG_DIR="$SCRIPT_DIR/.logs"
mkdir -p "$LOG_DIR"

# ── Hardware policy check (existing CLI surface; helper lives in PT) ──────────

run_hardware_policy_check() {
  local cli="${PT_DIR}/scripts/hardware_policy_cli.py"
  if [ -n "${PT_DIR:-}" ] && [ -f "$cli" ]; then
    echo ""
    echo "=== Hardware model affinity policy ==="
    PYTHONPATH="${PT_DIR}" "$PT_PYTHON" "$cli" --list || true
    echo ""
    PYTHONPATH="${PT_DIR}" "$PT_PYTHON" "$cli" --check-openclaw
  else
    _warn "policy" "hardware policy helper not found at ${cli:-unknown}"
    return 1
  fi
}

if [[ "${1:-}" == "--hardware-policy" ]]; then
  run_hardware_policy_check
  exit $?
fi

# ── macOS pre-flight ──────────────────────────────────────────────────────────
# Applies idempotent fixes to the AlphaClaw binary (macOS compat patches).
# Non-fatal — startup continues on any error.
if [ -f "$SCRIPT_DIR/setup_macos.py" ]; then
  "$US_PYTHON" "$SCRIPT_DIR/setup_macos.py" --quiet 2>&1 | sed 's/^/  /' || true
fi

# ── Codex PATH fix (idempotent) ───────────────────────────────────────────────
# Ensures ~/.local/bin/codex → /opt/homebrew/bin/codex so Codex is always
# callable regardless of which nvm version is active in this shell session.
if [ -f "$SCRIPT_DIR/scripts/setup_codex.sh" ]; then
  bash "$SCRIPT_DIR/scripts/setup_codex.sh" 2>&1 | sed 's/^/  [codex] /' || true
fi

# ── Hardware policy cache refresh (L2 disaster recovery) ─────────────────────
# Refreshes config/hardware_policy_cache.yml from PT's authoritative source.
# Non-fatal — if PT is absent the existing cache (L2) remains valid.
if [ -f "$SCRIPT_DIR/scripts/refresh_policy_cache.py" ]; then
  "$US_PYTHON" "$SCRIPT_DIR/scripts/refresh_policy_cache.py" 2>&1 | sed 's/^/  [policy] /' || true
fi

# ── LAN live probe — always run on startup (LAN is dynamic) ──────────────────
# LAN topology changes: DHCP leases expire, machines reboot, IPs shift.
# We ALWAYS run discover.py --force before reading any IP so the IP detection
# block below always reads fresh data, not a cache that might be days old.
#
# discover.py --force:
#   • Probes localhost:1234 for Mac LM Studio (fast, always local)
#   • Async-scans entire subnet (0.2s timeout per host, all 254 in parallel)
#   • Writes updated IPs to ~/.openclaw/openclaw.json and state/discovery.json
#   • Patches Perpetua-Tools config/ YAML files
#   • Total time: ~0.5s if Win offline, ~4-5s if Win online (model fetch)
_DISCOVER_SCRIPT="$HOME/.openclaw/scripts/discover.py"
if [ -f "$_DISCOVER_SCRIPT" ]; then
  _info "ip" "probing LAN topology (discover.py --force)..."
  if timeout 30 "$US_PYTHON" "$_DISCOVER_SCRIPT" --force \
       2>&1 | tee -a "$LOG_DIR/startup-$(date +%Y%m%d).log" | sed 's/^/  [discover] /'; then
    _info "ip" "LAN probe complete — openclaw.json is up to date"
  else
    _exit=$?
    if [ "$_exit" -eq 124 ]; then
      _warn "ip" "discover.py timed out (>30s, macOS ICMP limit?) — falling back to cached/static IPs"
    else
      _warn "ip" "discover.py --force exited ${_exit} — falling back to cached/static IPs"
    fi
  fi
else
  _warn "ip" "discover.py not found at $_DISCOVER_SCRIPT — skipping live LAN probe"
fi

# ── IP auto-detection (priority-based, reads fresh discover.py output above) ──
#
# Priority chain — first success wins:
#   1. ~/.openclaw/openclaw.json   (discover.py just patched it above)
#   2. discover.py --status        (reads state written by the --force run above)
#   3. network_autoconfig netifaces (dynamic interface detection — no prior state)
#   4. Subnet .103 constant        (subnet-portable: works on any /24, never a fixed IP)
#
# Old stale IPs are archived here only — NEVER used as source:
#   Windows was: .108 → .100 → .101 — all stale, replaced by dynamic detection

_IP_VARS="$("$US_PYTHON" -c "
import json, re, subprocess, sys
from pathlib import Path

MAC_IP = 'localhost'   # Mac always probes itself via localhost
WIN_IP = ''
source  = 'unknown'

# ── Priority 1: ~/.openclaw/openclaw.json ─────────────────────────────────────
# discover.py patches this file on every successful scan — authoritative.
try:
    cfg = json.loads(Path.home().joinpath('.openclaw/openclaw.json').read_text())
    url = cfg['models']['providers']['lmstudio-win']['baseUrl']
    WIN_IP = url.split('//')[-1].split(':')[0]
    source = 'openclaw.json'
except Exception:
    pass

# ── Priority 2: discover.py --status ─────────────────────────────────────────
# Reads cached discovery state (~/.openclaw/state/discovery.json). Fast, no probe.
if not WIN_IP:
    try:
        out = subprocess.check_output(
            [sys.executable, str(Path.home() / '.openclaw/scripts/discover.py'), '--status'],
            stderr=subprocess.DEVNULL, timeout=8
        ).decode()
        m = re.search(r'win:.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', out)
        if m:
            WIN_IP = m.group(1)
            source = 'discover.py'
    except Exception:
        pass

# ── Priority 3: network_autoconfig dynamic netifaces scan ────────────────────
# Uses OS network interface list — reflects current topology without prior state.
if not WIN_IP:
    try:
        sys.path.insert(0, '$SCRIPT_DIR')
        from network_autoconfig import NetworkAutoConfig
        cfg2 = NetworkAutoConfig()
        WIN_IP = cfg2.preferred_ips.get('Windows', '')
        source = 'network_autoconfig'
    except Exception:
        pass

# ── Priority 4: subnet.104 constant (subnet-portable, not a fixed IP) ────────
# Derives Win IP from Mac's own outbound interface subnet.
# If Mac is on 192.168.1.x → Win = 192.168.1.104 (works on any /24 without change).
# This is ONLY reached if discover.py failed AND openclaw.json is unreadable.
if not WIN_IP:
    try:
        import socket as _s
        with _s.socket(_s.AF_INET, _s.SOCK_DGRAM) as _sk:
            _sk.connect(('8.8.8.8', 80))
            _local = _sk.getsockname()[0]
        WIN_IP = '.'.join(_local.split('.')[:3]) + '.104'
        source = 'subnet.104'
    except Exception:
        WIN_IP = '192.168.254.104'   # absolute last resort — static /24 constant
        source = 'hardcoded-constant'

print(f'MAC_IP={MAC_IP}')
print(f'WIN_IP={WIN_IP}')
print(f'IP_SOURCE={source}')
" 2>/dev/null)"

eval "$_IP_VARS"
MAC_IP="${MAC_IP:-localhost}"
WIN_IP="${WIN_IP:-192.168.254.104}"
IP_SOURCE="${IP_SOURCE:-last-resort-constant}"

_info  "ip" "MAC_IP=${MAC_IP}  WIN_IP=${WIN_IP}  source=${IP_SOURCE}"
if [[ "$IP_SOURCE" == "last-resort-constant" ]]; then
  _warn "ip" "IP detection fell through to last-resort constant — run 'discover.py --force' if Win is unreachable"
fi
_var   "ip" "MAC_IP" "$MAC_IP" "$IP_SOURCE"
_var   "ip" "WIN_IP" "$WIN_IP" "$IP_SOURCE"

# ── PT resolve — backend probe + AlphaClaw bootstrap ─────────────────────────
# Delegates ALL gateway decisions to Perpetua-Tools (Layer 2).
# PT probes backends, determines mode, bootstraps AlphaClaw, and returns
# a JSON payload. orama reads that payload — it makes zero gateway decisions.
#
# PT owns: backend probe (was start.sh §2a), AlphaClaw bootstrap (§2b),
#          mode determination (was §2c).
# See: orchestrator/alphaclaw_manager.py
PT_RESOLVE_OK=0
PT_MODE="offline"
PT_DISTRIBUTED="no"
PT_ALPHACLAW_PORT=""

if [ -n "${PT_DIR:-}" ] && [ -f "${PT_DIR}/orchestrator/alphaclaw_manager.py" ]; then
  _info "pt" "resolving runtime — passing MAC_IP=${MAC_IP} WIN_IP=${WIN_IP}"
  _PT_ENV_EXPORTS="$(
    MAC_IP="${MAC_IP}" WIN_IP="${WIN_IP}" \
    PYTHONPATH="${PT_DIR}" \
    "$PT_PYTHON" -m orchestrator.alphaclaw_manager \
      --resolve --env-only \
      --mac-ip "${MAC_IP}" --win-ip "${WIN_IP}" \
      2>&1 | tee /dev/stderr | grep '^export '
  )" && PT_RESOLVE_OK=1 || true

  if [ "$PT_RESOLVE_OK" -eq 1 ] && [ -n "$_PT_ENV_EXPORTS" ]; then
    eval "$_PT_ENV_EXPORTS"
    PT_MODE="${PT_MODE:-offline}"
    PT_DISTRIBUTED="${PT_DISTRIBUTED:-no}"
    PT_ALPHACLAW_PORT="${PT_ALPHACLAW_PORT:-}"
    export PT_AGENTS_STATE="${PT_DIR}/.state/routing.json"
    _info "pt" "resolved — mode=${PT_MODE}  distributed=${PT_DISTRIBUTED}  alphaclaw_port=${PT_ALPHACLAW_PORT}"
    _var  "pt" "PT_MODE"          "$PT_MODE"          "alphaclaw_manager"
    _var  "pt" "PT_DISTRIBUTED"   "$PT_DISTRIBUTED"   "alphaclaw_manager"
    _var  "pt" "PT_ALPHACLAW_PORT" "$PT_ALPHACLAW_PORT" "alphaclaw_manager"
    _var  "pt" "PT_AGENTS_STATE"  "$PT_AGENTS_STATE"  "derived"
  else
    _warn "pt" "resolve non-fatal (exit=${PT_RESOLVE_OK}) — continuing with offline defaults"
  fi
else
  # Fallback: PT manager not available — delegate to bootstrap script directly
  PT_HOME="${PT_HOME:-$HOME/Perpetua-Tools}"
  ALPHACLAW_SCRIPT="$PT_HOME/alphaclaw_bootstrap.py"
  if [ -f "$ALPHACLAW_SCRIPT" ]; then
    _warn "pt" "alphaclaw_manager.py not found — using fallback bootstrap at ${ALPHACLAW_SCRIPT}"
    PT_HOME="$PT_HOME" UTS_HOME="$SCRIPT_DIR" \
      MAC_IP="${MAC_IP}" WIN_IP="${WIN_IP}" \
      "$US_PYTHON" "$ALPHACLAW_SCRIPT" --bootstrap \
      </dev/null 2>&1 | sed 's/^/  /' \
      || _warn "pt" "fallback bootstrap non-fatal — continuing without gateway"
  else
    _warn "pt" "PT not found at ${PT_DIR:-$PT_HOME} — skipping AlphaClaw bootstrap entirely"
  fi
fi

# Export env vars all services read (with user overrides respected)
# _var traces show exactly what value each service will receive
export OLLAMA_MAC_ENDPOINT="${OLLAMA_MAC_ENDPOINT:-http://localhost:11434}"
export OLLAMA_WINDOWS_ENDPOINT="${OLLAMA_WINDOWS_ENDPOINT:-http://${WIN_IP}:11434}"
export LM_STUDIO_MAC_ENDPOINT="${LM_STUDIO_MAC_ENDPOINT:-http://localhost:1234}"
export LM_STUDIO_WIN_ENDPOINTS="${LM_STUDIO_WIN_ENDPOINTS:-http://${WIN_IP}:1234}"
export WINDOWS_IP="${WINDOWS_IP:-${WIN_IP}}"
export GPU_BOX="${GPU_BOX:-WINUSER@${WIN_IP}}"
# WIN_LM_STUDIO_HOST — consumed by api_server.py to enable Windows LM Studio provider
export WIN_LM_STUDIO_HOST="${WIN_LM_STUDIO_HOST:-${WIN_IP}}"

_info "env" "endpoints exported to child processes"
_var  "env" "OLLAMA_MAC_ENDPOINT"    "$OLLAMA_MAC_ENDPOINT"    "derived"
_var  "env" "OLLAMA_WINDOWS_ENDPOINT" "$OLLAMA_WINDOWS_ENDPOINT" "derived"
_var  "env" "LM_STUDIO_MAC_ENDPOINT" "$LM_STUDIO_MAC_ENDPOINT" "derived"
_var  "env" "LM_STUDIO_WIN_ENDPOINTS" "$LM_STUDIO_WIN_ENDPOINTS" "derived"
_var  "env" "WINDOWS_IP"             "$WINDOWS_IP"             "derived"

# AlphaClaw security warning — show if running on default password
_AC_PT_HOME="${PT_DIR:-${PT_HOME:-$HOME/Perpetua-Tools}}"
_AC_ONBOARDING="${_AC_PT_HOME}/.state/onboarding.json"
if [ -f "$_AC_ONBOARDING" ]; then
  if "$US_PYTHON" -c "
import json, sys, pathlib
f = pathlib.Path('${_AC_ONBOARDING}')
d = json.loads(f.read_text(encoding='utf-8'))
sys.exit(0 if d.get('alphaclaw', {}).get('password_is_default') else 1)
" 2>/dev/null; then
    echo ""
    echo "  ┌────────────────────────────────────────────────────────────────┐"
    echo "  │  SECURITY  AlphaClaw is running on the DEFAULT password         │"
    echo "  │  Set SETUP_PASSWORD=<yourpassword> in .env and restart          │"
    echo "  └────────────────────────────────────────────────────────────────┘"
    echo ""
  fi
fi

# ── helpers ───────────────────────────────────────────────────────────────────

pid_on_port() { lsof -ti "tcp:$1" 2>/dev/null | head -1 || true; }

wait_for_port() {
  local port=$1 label=$2 tries=0
  printf "  waiting for %s (:%s)" "$label" "$port"
  while ! nc -z localhost "$port" 2>/dev/null; do
    sleep 0.5; tries=$((tries+1))
    printf "."
    if [ $((tries % 60)) -eq 0 ] && [ $tries -gt 0 ]; then
      local elapsed=$((tries / 2))
      local logfile="$LOG_DIR/$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]').log"
      printf "\n  ⚠  %s (:%s) unresponsive for %ds\n" "$label" "$port" "$elapsed"
      if [ -f "$logfile" ]; then
        echo "  last 5 lines of ${logfile}:"
        tail -5 "$logfile" | sed 's/^/    /'
      fi
      printf "  still waiting for %s (:%s)" "$label" "$port"
    fi
    if [ $tries -ge 150 ]; then
      local logfile="$LOG_DIR/$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]').log"
      printf " TIMEOUT — check %s\n" "$logfile"
      return 0  # non-fatal: continue starting remaining services
    fi
  done
  echo " UP"
}

open_browser() {
  local url=$1
  if command -v open &>/dev/null; then open "$url"
  elif command -v xdg-open &>/dev/null; then xdg-open "$url"
  fi
}

# ── ASCII art banner ───────────────────────────────────────────────────────────
# Displays at every startup (not --stop/--status). Shows live tier + agent grid.
_print_banner() {
  local mode="${PT_MODE:-offline}"
  local mac_ip="${MAC_IP:-localhost}"
  local win_ip="${WIN_IP:-?}"
  local tier="?"
  local tier_label=""
  # tier_color: reserved for future ANSI colour output

  # Determine tier from reachability (-w 1 = 1s timeout per probe, avoids 30s OS hang)
  local mac_up=0 win_up=0 oc_up=0
  nc -z -w 1 localhost 1234   >/dev/null 2>&1 && mac_up=1
  nc -z -w 1 "$win_ip" 1234   >/dev/null 2>&1 && win_up=1
  nc -z -w 1 localhost 18789  >/dev/null 2>&1 && oc_up=1

  if   [ "$mac_up" -eq 1 ] && [ "$win_up" -eq 1 ]; then tier=1; tier_label="FULL  · Mac + Win (both nodes)"
  elif [ "$mac_up" -eq 1 ];                          then tier=2; tier_label="MAC   · Mac only"
  elif [ "$win_up" -eq 1 ];                          then tier=4; tier_label="WIN   · Win only"
  else                                                    tier=3; tier_label="LOCAL DOWN · cloud fallback (check network)"
  fi

  local oc_status="●"; [ "$oc_up" -eq 0 ] && oc_status="○"

  # Agent readiness per tier
  local mac_agents="main  mac-researcher  orchestrator"
  local win_agents="win-researcher  coder  autoresearcher"
  local mac_mark="✓"; [ "$mac_up" -eq 0 ] && mac_mark="✗"
  local win_mark="✓"; [ "$win_up" -eq 0 ] && win_mark="✗"

  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║                                                                  ║"
  printf "║   ██████╗ ██████╗  █████╗ ███╗   ███╗ █████╗                   ║\n"
  printf "║  ██╔═══██╗██╔══██╗██╔══██╗████╗ ████║██╔══██╗                  ║\n"
  printf "║  ██║   ██║██████╔╝███████║██╔████╔██║███████║                  ║\n"
  printf "║  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║██╔══██║                  ║\n"
  printf "║  ╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║                  ║\n"
  printf "║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝  v0.9.9.8      ║\n"
  echo "║                                                                  ║"
  echo "║  ὅραμα — vision/revelation · Layer 3 orchestration/meta-intel   ║"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf "║  OpenClaw  %s %-8s  AlphaClaw → Perpetua-Tools → orama     ║\n" "$oc_status" ":18789"
  printf "║  Tier %-1s    %-52s║\n" "$tier" "$tier_label"
  printf "║  Mode      %-52s║\n" "$mode"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf "║  Mac %s  %-9s  %-45s║\n" "$mac_mark" "localhost" "qwen3.5-9b-mlx (MLX · ctx 56k)"
  printf "║       %-63s║\n" "agents: $mac_agents"
  printf "║  Win %s  %-9s  %-45s║\n" "$win_mark" "$win_ip" "qwen3.5-27b (GGUF RTX 3080 · ctx 131k)"
  printf "║       %-63s║\n" "agents: $win_agents"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf "║  PT   :%-5s   orama :%-5s   Portal :%-5s                      ║\n" \
    "${PT_PORT:-8000}" "${US_PORT:-8001}" "${PORTAL_PORT:-8002}"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
}

# ── --stop ────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--stop" ]]; then
  echo "Stopping orama-system services..."
  for port in $PT_PORT $US_PORT $PORTAL_PORT; do
    pid=$(pid_on_port "$port")
    if [ -n "$pid" ]; then
      kill "$pid" 2>/dev/null && echo "  killed PID $pid (:$port)" || true
    else
      echo "  nothing on :$port"
    fi
  done
  exit 0
fi

# ── --status ──────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--status" ]]; then
  _print_banner
  echo "── service status ───────────────────────────────────────────────────"
  for port in $PT_PORT $US_PORT $PORTAL_PORT; do
    pid=$(pid_on_port "$port")
    if [ -n "$pid" ]; then
      printf "  %-8s :%-5s  ● UP    (PID %s)\n" "" "$port" "$pid"
    else
      printf "  %-8s :%-5s  ○ DOWN\n" "" "$port"
    fi
  done
  run_hardware_policy_check || true
  echo ""
  exit 0
fi

# ── start services ────────────────────────────────────────────────────────────

_print_banner

# 1. Perpetua-Tools (PT) orchestrator
if [ -n "$PT_DIR" ] && [ -f "$PT_DIR/orchestrator.py" ]; then
  if pid_on_port "$PT_PORT" | grep -q .; then
    echo "  PT   :$PT_PORT already running"
  else
    echo "  PT   starting → $LOG_DIR/pt.log"
    (cd "$PT_DIR" && PYTHONPATH="$PT_DIR" "$PT_PYTHON" -m uvicorn orchestrator.fastapi_app:app \
      --host 0.0.0.0 --port "$PT_PORT" \
      >> "$LOG_DIR/pt.log" 2>&1) &
    wait_for_port "$PT_PORT" "PT"
  fi
else
  echo "  PT   skipped (not found at ${PT_DIR:-unknown})"
fi

# 2. orama-system reasoning engine
if pid_on_port "$US_PORT" | grep -q .; then
  echo "  orama :$US_PORT already running"
else
  echo "  orama starting → $LOG_DIR/us.log"
  (cd "$SCRIPT_DIR" && PYTHONPATH="$SCRIPT_DIR" "$US_PYTHON" -m uvicorn api_server:app \
    --host 0.0.0.0 --port "$US_PORT" \
    >> "$LOG_DIR/us.log" 2>&1) &
  wait_for_port "$US_PORT" "orama"
fi

# 3. Portal
if pid_on_port "$PORTAL_PORT" | grep -q .; then
  echo "  Portal :$PORTAL_PORT already running"
else
  echo "  Portal starting → $LOG_DIR/portal.log"
  (cd "$SCRIPT_DIR" && PYTHONPATH="$SCRIPT_DIR" "$US_PYTHON" -m uvicorn portal_server:app \
    --host 0.0.0.0 --port "$PORTAL_PORT" \
    >> "$LOG_DIR/portal.log" 2>&1) &
  wait_for_port "$PORTAL_PORT" "Portal"
fi

echo "── services ready ───────────────────────────────────────────────────"
printf "  ●  PT      http://localhost:%s/health\n" "$PT_PORT"
printf "  ●  orama   http://localhost:%s/health\n" "$US_PORT"
printf "  ●  Portal  %s\n" "$PORTAL_URL"
printf "  ○  JSON    %s/api/status\n" "$PORTAL_URL"
echo ""
printf "  Logs  : %s/\n" "$LOG_DIR"
printf "  Stop  : ./start.sh --stop\n"
printf "  Debug : ORAMA_DEBUG=1 ./start.sh\n"
echo "────────────────────────────────────────────────────────────────────"
echo ""

if [[ "${1:-}" != "--no-open" ]]; then
  open_browser "$PORTAL_URL"
fi
