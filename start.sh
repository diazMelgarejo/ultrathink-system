#!/bin/bash
# start.sh — ultrathink v1.0 RC first-run launcher
#
# Starts three services in background, then opens the portal in your browser:
#   :8000  Perplexity-Tools orchestrator  (PT)
#   :8001  ultrathink reasoning engine    (US)
#   :8002  Portal dashboard               (this file)
#
# Usage:
#   ./start.sh            — start all, open browser
#   ./start.sh --no-open  — start all, skip browser open
#   ./start.sh --stop     — kill all three services
#   ./start.sh --status   — show which ports are listening

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PT_DIR="$(cd "$SCRIPT_DIR/../perplexity-api/Perplexity-Tools" 2>/dev/null && pwd || echo "")"

PT_PORT=${PT_PORT:-8000}
US_PORT=${US_PORT:-8001}
PORTAL_PORT=${PORTAL_PORT:-8002}
PORTAL_URL="http://localhost:${PORTAL_PORT}"

LOG_DIR="$SCRIPT_DIR/.logs"
mkdir -p "$LOG_DIR"

# ── helpers ───────────────────────────────────────────────────────────────────

pid_on_port() { lsof -ti "tcp:$1" 2>/dev/null | head -1 || true; }

wait_for_port() {
  local port=$1 label=$2 tries=0
  printf "  waiting for %s (:%s)" "$label" "$port"
  while ! nc -z localhost "$port" 2>/dev/null; do
    sleep 0.5; tries=$((tries+1))
    printf "."
    if [ $tries -ge 20 ]; then echo " TIMEOUT"; return 1; fi
  done
  echo " UP"
}

open_browser() {
  local url=$1
  if command -v open &>/dev/null; then open "$url"          # macOS
  elif command -v xdg-open &>/dev/null; then xdg-open "$url" # Linux
  fi
}

# ── --stop ────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--stop" ]]; then
  echo "Stopping ultrathink services..."
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
  echo ""
  echo "=== ultrathink service status ==="
  for port in $PT_PORT $US_PORT $PORTAL_PORT; do
    pid=$(pid_on_port "$port")
    if [ -n "$pid" ]; then
      echo "  UP   :$port  (PID $pid)"
    else
      echo "  DOWN :$port"
    fi
  done
  echo ""
  exit 0
fi

# ── start ─────────────────────────────────────────────────────────────────────

echo ""
echo "=== ultrathink v1.0 RC — starting ==="
echo ""

# 1. Perplexity-Tools (PT)
if [ -n "$PT_DIR" ] && [ -f "$PT_DIR/orchestrator.py" ]; then
  if pid_on_port "$PT_PORT" | grep -q .; then
    echo "  PT   :$PT_PORT already running"
  else
    echo "  PT   starting → $LOG_DIR/pt.log"
    (cd "$PT_DIR" && python -m uvicorn orchestrator:app \
      --host 0.0.0.0 --port "$PT_PORT" \
      >> "$LOG_DIR/pt.log" 2>&1) &
    wait_for_port "$PT_PORT" "PT"
  fi
else
  echo "  PT   skipped (not found at $PT_DIR)"
fi

# 2. ultrathink api_server (US)
if pid_on_port "$US_PORT" | grep -q .; then
  echo "  US   :$US_PORT already running"
else
  echo "  US   starting → $LOG_DIR/us.log"
  (cd "$SCRIPT_DIR" && python -m uvicorn api_server:app \
    --host 0.0.0.0 --port "$US_PORT" \
    >> "$LOG_DIR/us.log" 2>&1) &
  wait_for_port "$US_PORT" "US"
fi

# 3. Portal
if pid_on_port "$PORTAL_PORT" | grep -q .; then
  echo "  Portal :$PORTAL_PORT already running"
else
  echo "  Portal starting → $LOG_DIR/portal.log"
  (cd "$SCRIPT_DIR" && python -m uvicorn portal_server:app \
    --host 0.0.0.0 --port "$PORTAL_PORT" \
    >> "$LOG_DIR/portal.log" 2>&1) &
  wait_for_port "$PORTAL_PORT" "Portal"
fi

echo ""
echo "  PT     http://localhost:${PT_PORT}/health"
echo "  US     http://localhost:${US_PORT}/health"
echo "  Portal ${PORTAL_URL}"
echo "  JSON   ${PORTAL_URL}/api/status"
echo ""

# Open browser unless suppressed
if [[ "${1:-}" != "--no-open" ]]; then
  open_browser "$PORTAL_URL"
fi

echo "Logs: $LOG_DIR/"
echo "Stop: ./start.sh --stop"
echo ""
