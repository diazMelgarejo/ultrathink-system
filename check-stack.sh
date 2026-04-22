#!/bin/bash
# check-stack.sh — Full 4-layer stack health check
# orama-system | Perpetua-Tools | Ollama | Redis
#
# Usage:
#   chmod +x check-stack.sh
#   ./check-stack.sh
#
# Exits 0 if all required services are up, non-zero otherwise.

set -euo pipefail

PT_PORT=${PT_PORT:-8000}
UT_PORT=${UT_PORT:-8001}
OLLAMA_MAC=${OLLAMA_MAC_ENDPOINT:-http://192.168.1.101:11434}
OLLAMA_WIN=${OLLAMA_WINDOWS_ENDPOINT:-http://192.168.1.100:11434}
REDIS_HOST=${REDIS_HOST:-192.168.1.100}
REDIS_PORT=${REDIS_PORT:-6379}

PASS=0
FAIL=0

check() {
  local label="$1"
  local url="$2"
  if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
    echo "  OK    $label"
    ((PASS++))
  else
    echo "  DOWN  $label  ($url)"
    ((FAIL++))
  fi
}

# NOTE: Redis is a PT-only dependency (deferred to v1.1+).
# This check is informational only — ultrathink does not require Redis.
check_redis() {
  if command -v redis-cli &>/dev/null; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
      echo "  OK    Redis  ($REDIS_HOST:$REDIS_PORT)"
      ((PASS++))
    else
      echo "  DOWN  Redis  ($REDIS_HOST:$REDIS_PORT)"
      ((FAIL++))
    fi
  else
    echo "  SKIP  Redis  (redis-cli not installed)"
  fi
}

echo ""
echo "=== Stack Health Check === $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

echo "[Layer 1] Perpetua-Tools orchestrator"
check "PT health" "http://localhost:${PT_PORT}/health"

echo ""
echo "[Layer 2] orama-system reasoning engine"
check "UltraThink health" "http://localhost:${UT_PORT}/health"

echo ""
echo "[Layer 3a] Ollama — Mac (primary)"
check "Ollama Mac" "${OLLAMA_MAC}/api/tags"

echo ""
echo "[Layer 3b] Ollama — Windows RTX 3080"
check "Ollama Windows" "${OLLAMA_WIN}/api/tags"

echo ""
echo "[State] Redis"
check_redis

echo ""
echo "=== Result: ${PASS} OK, ${FAIL} DOWN ==="

if [ "$FAIL" -gt 0 ]; then
  echo "WARNING: $FAIL service(s) unreachable. Check your LAN setup."
  exit 1
fi

echo "All services healthy."
exit 0
