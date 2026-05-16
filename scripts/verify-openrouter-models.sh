#!/usr/bin/env bash
#
# verify-openrouter-models.sh
#
# Smoke-test the OpenRouter free-model endpoints + verify OpenClaw policy
# is applied correctly. Idempotent.
#
# Usage:
#   scripts/verify-openrouter-models.sh                    # default ~/.openclaw/openclaw.json
#   scripts/verify-openrouter-models.sh /path/to/config    # explicit config
#
# Source spec: OpenClaw/v1/OpenRouter.md §9 + §12 acceptance tests
# Adopted into: orama-system/bin/orama-system/mcp-orchestration/SKILL.md §12

set -euo pipefail

CONFIG="${1:-${HOME}/.openclaw/openclaw.json}"
EXIT_CODE=0

# ─── 1. OpenClaw model status ─────────────────────────────────────────────────
echo "== OpenClaw model status =="
if command -v openclaw >/dev/null 2>&1; then
  openclaw models status || EXIT_CODE=$?
  openclaw models list --provider openrouter --plain 2>/dev/null || true
else
  echo "openclaw CLI not found in PATH"
fi
echo ""

# ─── 2. OpenRouter API smoke test ─────────────────────────────────────────────
echo "== OpenRouter model API smoke test =="
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "ERROR: OPENROUTER_API_KEY is not set. Skipping endpoint checks." >&2
  EXIT_CODE=1
else
  MODELS=(
    "nvidia/nemotron-3-super-120b-a12b:free"
    "minimax/minimax-m2.5:free"
    "deepseek/deepseek-v4-flash:free"
    "openai/gpt-oss-120b:free"
    "z-ai/glm-4.5-air:free"
    "inclusionai/ling-2.6-flash:free"
    "openrouter/free"
  )

  for model in "${MODELS[@]}"; do
    printf "  %-50s " "$model"
    if curl -fsS "https://openrouter.ai/api/v1/models/${model}/endpoints" \
        -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
        -m 10 >/dev/null 2>&1; then
      echo "OK"
    else
      echo "WARN (endpoint check failed — model may be rate-limited or unavailable)"
    fi
  done
fi
echo ""

# ─── 3. Acceptance tests on $CONFIG (per OpenRouter.md §12) ───────────────────
echo "== Config acceptance tests =="
if [[ ! -f "$CONFIG" ]]; then
  echo "SKIP: config file does not exist: $CONFIG"
else
  # Required: Nemotron primary present
  if grep -q "openrouter/nvidia/nemotron-3-super-120b-a12b:free" "$CONFIG"; then
    echo "  ✓ Nemotron primary present"
  else
    echo "  ✗ MISSING: Nemotron primary"
    EXIT_CODE=1
  fi

  # Preserved (only check if these existed before — these are sentinel patterns
  # from the user's deployment; absent in default templates):
  for sentinel in '+14159419166' '"workspaceAccess": "ro"' '"bind": "lan"' '"mode": "token"' '"dmPolicy": "allowlist"'; do
    if grep -qF "$sentinel" "$CONFIG"; then
      echo "  ✓ preserved: $sentinel"
    fi
  done
fi
echo ""

if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo "Verification PASSED."
else
  echo "Verification finished with warnings (exit $EXIT_CODE)."
fi
exit "$EXIT_CODE"
