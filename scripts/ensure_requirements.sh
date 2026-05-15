#!/usr/bin/env bash
# scripts/ensure_requirements.sh — idempotent hard-requirements probe + installer
# orama-system v0.9.9.8
#
# HARD requirements (fail closed — startup aborts if absent and can't be fixed):
#   Ollama server at localhost:11434
#   qwen3.5:9b-nvfp4  (Mac inference)
#   bge-m3             (embeddings for gbrain)
#
# SOFT requirements (auto-install, non-fatal if fail):
#   Python venv + pip deps (requirements.txt)
#   ~/.gbrain/config.json presence + embedding model key
#
# Usage:
#   bash scripts/ensure_requirements.sh            # check + install
#   bash scripts/ensure_requirements.sh --check    # probe only, no install, exit 1 if missing
#   bash scripts/ensure_requirements.sh --force    # skip stamps, reinstall soft reqs
#   bash scripts/ensure_requirements.sh --quiet    # suppress INFO, only WARN/ERROR

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STAMP_FILE="${SCRIPT_DIR}/.requirements.stamp"
OLLAMA_ENDPOINT="${OLLAMA_MAC_ENDPOINT:-http://localhost:11434}"
LOG_DIR="${SCRIPT_DIR}/.logs"
mkdir -p "$LOG_DIR"

# ── flags ─────────────────────────────────────────────────────────────────────
MODE_CHECK=0; MODE_FORCE=0; MODE_QUIET=0
for _arg in "$@"; do
  case "$_arg" in
    --check) MODE_CHECK=1 ;;
    --force) MODE_FORCE=1 ;;
    --quiet) MODE_QUIET=1 ;;
  esac
done

# ── logging ───────────────────────────────────────────────────────────────────
_ts() { date +%H:%M:%S; }
_info()  { [ "$MODE_QUIET" -eq 0 ] && echo "[$(_ts)] INFO  [ensure] $*" || true; }
_warn()  { echo "[$(_ts)] WARN  [ensure] $*" >&2; }
_err()   { echo "[$(_ts)] ERROR [ensure] $*" >&2; }
_ok()    { echo "[$(_ts)] OK    [ensure] $*"; }

HARD_FAIL=0
_hard_fail() {
  _err "$*"
  HARD_FAIL=1
}

# ── stamp helpers ─────────────────────────────────────────────────────────────
_req_hash() {
  local req="${SCRIPT_DIR}/requirements.txt"
  [ -f "$req" ] && sha256sum "$req" 2>/dev/null | cut -d' ' -f1 || echo "none"
}

_stamp_current() {
  cat "$STAMP_FILE" 2>/dev/null | grep "^python_req=" | cut -d= -f2 || echo ""
}

_stamp_write() {
  {
    echo "python_req=$(_req_hash)"
    echo "ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "version=1"
  } > "$STAMP_FILE"
}

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 1 — HARD: Ollama server
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 1 — Ollama server probe"

if ! command -v ollama >/dev/null 2>&1; then
  _hard_fail "ollama binary not found in PATH. Install: https://ollama.com"
elif ! curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1; then
  if [ "$MODE_CHECK" -eq 0 ]; then
    _warn "Ollama server not running — attempting start..."
    nohup ollama serve >>"${LOG_DIR}/ollama.log" 2>&1 &
    _i=0
    while [ $_i -lt 15 ]; do
      sleep 1; _i=$((_i+1))
      curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1 && break
    done
    if ! curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1; then
      _hard_fail "Ollama server did not start within 15s — see ${LOG_DIR}/ollama.log"
    else
      _ok "Ollama server started"
    fi
  else
    _hard_fail "Ollama server not reachable at ${OLLAMA_ENDPOINT}"
  fi
else
  _ok "Ollama server reachable at ${OLLAMA_ENDPOINT}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2 — HARD: Inference model (qwen3.5:9b-nvfp4)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 2 — Inference model probe (qwen3.5:9b-nvfp4)"

if [ "$HARD_FAIL" -eq 0 ]; then
  INFERENCE_MODEL="${OLLAMA_WARM_MODEL:-qwen3.5:9b-nvfp4}"
  # Match against full name or just the base (before colon) — both are valid
  INFERENCE_BASE="${INFERENCE_MODEL%%:*}"
  _OLLAMA_LIST="$(ollama list 2>/dev/null || true)"

  if echo "$_OLLAMA_LIST" | grep -qF "${INFERENCE_MODEL}" || echo "$_OLLAMA_LIST" | grep -qF "${INFERENCE_BASE}"; then
    _ok "Model ${INFERENCE_MODEL} present"
  elif [ "$MODE_CHECK" -eq 0 ]; then
    _info "Pulling ${INFERENCE_MODEL} (this may take a while)..."
    if ollama pull "${INFERENCE_MODEL}" >>"${LOG_DIR}/ollama.log" 2>&1; then
      _ok "Model ${INFERENCE_MODEL} pulled"
    else
      _hard_fail "Failed to pull ${INFERENCE_MODEL}. Run: ollama pull ${INFERENCE_MODEL}"
    fi
  else
    _hard_fail "Model ${INFERENCE_MODEL} not installed. Run: ollama pull ${INFERENCE_MODEL}"
  fi
else
  _warn "Phase 2 skipped — Ollama not available"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 3 — HARD: Embedding model (bge-m3)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 3 — Embedding model probe (bge-m3)"

if [ "$HARD_FAIL" -eq 0 ]; then
  if echo "${_OLLAMA_LIST:-$(ollama list 2>/dev/null || true)}" | grep -qF "bge-m3"; then
    _ok "Model bge-m3 present"
  elif [ "$MODE_CHECK" -eq 0 ]; then
    _info "Pulling bge-m3 (required for gbrain embeddings)..."
    if ollama pull bge-m3 >>"${LOG_DIR}/ollama.log" 2>&1; then
      _ok "Model bge-m3 pulled"
    else
      _hard_fail "Failed to pull bge-m3. Run: ollama pull bge-m3"
    fi
  else
    _hard_fail "Model bge-m3 not installed. Run: ollama pull bge-m3"
  fi
else
  _warn "Phase 3 skipped — Ollama not available"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 4 — SOFT: gbrain config validation
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 4 — gbrain config validation"

GBRAIN_CONFIG="${HOME}/.gbrain/config.json"
if [ ! -f "$GBRAIN_CONFIG" ]; then
  _warn "~/.gbrain/config.json not found — gbrain semantic search will be unavailable"
  _warn "Run: gbrain init  (or see CLAUDE-instru.md §5)"
else
  _GBRAIN_MODEL=$(python3 -c "
import json, pathlib
try:
    d = json.loads(pathlib.Path('${GBRAIN_CONFIG}').read_text())
    print(d.get('embedding_model','missing'))
except Exception as e:
    print('error:' + str(e))
" 2>/dev/null || echo "parse-error")

  if [[ "$_GBRAIN_MODEL" == "ollama:bge-m3" ]]; then
    _ok "gbrain config: embedding_model=ollama:bge-m3 ✓"
  elif [[ "$_GBRAIN_MODEL" == "missing" ]]; then
    _warn "gbrain config: embedding_model key missing — semantic search may use wrong model"
  else
    _warn "gbrain config: embedding_model=${_GBRAIN_MODEL} (expected ollama:bge-m3)"
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 5 — SOFT: Python venv + pip deps (stamp-gated)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 5 — Python venv + dependencies"

PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"
VENV_FRESH=0

if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
  if [ "$MODE_CHECK" -eq 0 ]; then
    _info "Creating Python venv..."
    python3 -m venv "${SCRIPT_DIR}/.venv" >>"${LOG_DIR}/install.log" 2>&1 || {
      _warn "venv creation failed — see ${LOG_DIR}/install.log"
    }
    VENV_FRESH=1
  else
    _warn ".venv not found — run without --check to create"
  fi
else
  _ok "Python venv exists"
fi

if [ -d "${SCRIPT_DIR}/.venv" ]; then
  CURRENT_HASH="$(_stamp_current)"
  EXPECTED_HASH="$(_req_hash)"

  if [ "$MODE_FORCE" -eq 1 ] || [ "$VENV_FRESH" -eq 1 ] || [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
    if [ "$MODE_CHECK" -eq 0 ]; then
      _info "requirements.txt changed (or --force) — reinstalling deps..."
      "${SCRIPT_DIR}/.venv/bin/pip" install -q -r "${SCRIPT_DIR}/requirements.txt" \
        >>"${LOG_DIR}/install.log" 2>&1 && {
        _stamp_write
        _ok "Python deps installed (stamp updated)"
      } || _warn "pip install failed — see ${LOG_DIR}/install.log"
    else
      _warn "requirements.txt hash mismatch — run without --check to update"
    fi
  else
    _ok "Python deps up-to-date (stamp matches)"
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# RESULT
# ──────────────────────────────────────────────────────────────────────────────
echo ""
if [ "$HARD_FAIL" -gt 0 ]; then
  _err "Hard requirements check FAILED — system cannot start without the above."
  _err "See CLAUDE-instru.md §6 for the probe spec and rationale."
  echo ""
  exit 1
else
  _ok "All hard requirements satisfied — system ready to start"
  echo ""
  exit 0
fi
