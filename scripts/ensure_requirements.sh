#!/usr/bin/env bash
# scripts/ensure_requirements.sh — idempotent hard-requirements probe + installer
# orama-system v0.9.9.8
#
# HARD requirements (fail closed — startup aborts if absent and can't be fixed):
#   Ollama binary + server at localhost:11434  (auto-installed on Linux/macOS/Docker)
#   qwen3.5:9b-nvfp4  (Mac inference — pulled if missing)
#   bge-m3             (embeddings for gbrain — pulled if missing)
#
# SOFT requirements (auto-install, non-fatal if fail):
#   Python venv + pip deps (sha256-stamped, skips if unchanged)
#   ~/.gbrain/config.json embedding_model validation (warn only)
#
# Platform support:
#   macOS (arm64/x86_64) — brew install --cask ollama OR official curl installer
#   Linux / Docker       — official curl installer (https://ollama.com/install.sh)
#   Windows              — separate ensure_requirements.ps1 handles LM Studio
#
# Usage:
#   bash scripts/ensure_requirements.sh            # check + install everything
#   bash scripts/ensure_requirements.sh --check    # probe only, exit 1 if missing
#   bash scripts/ensure_requirements.sh --force    # skip stamps, reinstall soft reqs
#   bash scripts/ensure_requirements.sh --quiet    # suppress INFO, only WARN/ERROR
#
# Env overrides:
#   ORAMA_SKIP_ENSURE=1        — bypass this script entirely (CI/pre-built images)
#   OLLAMA_MAC_ENDPOINT        — override default http://localhost:11434
#   OLLAMA_WARM_MODEL          — override default inference model
#   OLLAMA_INSTALL_METHOD      — force "brew" or "curl" (auto-detected otherwise)

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
_ts()   { date +%H:%M:%S; }
_info() { [ "$MODE_QUIET" -eq 0 ] && echo "[$(_ts)] INFO  [ensure] $*" || true; }
_warn() { echo "[$(_ts)] WARN  [ensure] $*" >&2; }
_err()  { echo "[$(_ts)] ERROR [ensure] $*" >&2; }
_ok()   { echo "[$(_ts)] OK    [ensure] $*"; }

HARD_FAIL=0
_hard_fail() { _err "$*"; HARD_FAIL=1; }

# ── OS detection ──────────────────────────────────────────────────────────────
_OS="$(uname -s 2>/dev/null || echo Unknown)"
_ARCH="$(uname -m 2>/dev/null || echo unknown)"
_IS_DOCKER=0
[ -f "/.dockerenv" ] && _IS_DOCKER=1

_os_label() {
  case "$_OS" in
    Darwin) echo "macOS ${_ARCH}" ;;
    Linux)  [ "$_IS_DOCKER" -eq 1 ] && echo "Linux/Docker ${_ARCH}" || echo "Linux ${_ARCH}" ;;
    *)      echo "$_OS ${_ARCH}" ;;
  esac
}

# ── stamp helpers ─────────────────────────────────────────────────────────────
_req_hash() {
  local req="${SCRIPT_DIR}/requirements.txt"
  [ -f "$req" ] && sha256sum "$req" 2>/dev/null | cut -d' ' -f1 || echo "none"
}
_stamp_current() { cat "$STAMP_FILE" 2>/dev/null | grep "^python_req=" | cut -d= -f2 || echo ""; }
_stamp_write() {
  { echo "python_req=$(_req_hash)"; echo "ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "version=1"; } > "$STAMP_FILE"
}

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 0 — OS fingerprint
# ──────────────────────────────────────────────────────────────────────────────
_info "Platform: $(_os_label)"

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 1 — HARD: Ollama binary (auto-install on Linux/macOS/Docker)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 1 — Ollama binary"

_install_ollama() {
  local method="${OLLAMA_INSTALL_METHOD:-auto}"

  if [ "$MODE_CHECK" -eq 1 ]; then
    _hard_fail "Ollama not installed. Run: bash scripts/ensure_requirements.sh"
    return
  fi

  case "$_OS" in
    Darwin)
      # Prefer Homebrew cask (manages updates, launchd service, PATH).
      # Fall back to official curl installer if brew unavailable.
      if [ "$method" = "curl" ]; then
        _info "Installing Ollama via official curl installer (forced)..."
        curl -fsSL https://ollama.com/install.sh | sh >>"${LOG_DIR}/ollama-install.log" 2>&1 \
          && _ok "Ollama installed via curl" \
          || { _hard_fail "Ollama curl install failed — see ${LOG_DIR}/ollama-install.log"; return; }
      elif command -v brew >/dev/null 2>&1; then
        _info "Installing Ollama via Homebrew cask..."
        brew install --cask ollama >>"${LOG_DIR}/ollama-install.log" 2>&1 \
          && _ok "Ollama installed via Homebrew" \
          || {
            _warn "Homebrew install failed — falling back to official installer"
            curl -fsSL https://ollama.com/install.sh | sh >>"${LOG_DIR}/ollama-install.log" 2>&1 \
              && _ok "Ollama installed via curl" \
              || { _hard_fail "Ollama install failed — see ${LOG_DIR}/ollama-install.log"; return; }
          }
      else
        _info "brew not found — using official curl installer..."
        curl -fsSL https://ollama.com/install.sh | sh >>"${LOG_DIR}/ollama-install.log" 2>&1 \
          && _ok "Ollama installed via curl" \
          || { _hard_fail "Ollama curl install failed — see ${LOG_DIR}/ollama-install.log"; return; }
      fi
      ;;

    Linux)
      _info "Installing Ollama via official installer (Linux/${_ARCH})..."
      curl -fsSL https://ollama.com/install.sh | sh >>"${LOG_DIR}/ollama-install.log" 2>&1 \
        && _ok "Ollama installed" \
        || { _hard_fail "Ollama install failed — see ${LOG_DIR}/ollama-install.log"; return; }
      ;;

    *)
      _hard_fail "Unsupported platform: $_OS — install Ollama manually: https://ollama.com"
      return
      ;;
  esac

  # Reload PATH so the newly installed binary is visible
  hash -r 2>/dev/null || true
}

if ! command -v ollama >/dev/null 2>&1; then
  _warn "Ollama binary not found — installing..."
  _install_ollama
fi

# Verify binary is now reachable
if ! command -v ollama >/dev/null 2>&1; then
  _hard_fail "Ollama binary still not found after install attempt. PATH=${PATH}"
else
  _OLLAMA_VER="$(ollama --version 2>/dev/null | tr -d '\n' || echo unknown)"
  _ok "Ollama binary present — ${_OLLAMA_VER}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2 — HARD: Ollama server running
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 2 — Ollama server probe"

if [ "$HARD_FAIL" -eq 0 ]; then
  if ! curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1; then
    if [ "$MODE_CHECK" -eq 0 ]; then
      _warn "Ollama server not running — starting..."
      nohup ollama serve >>"${LOG_DIR}/ollama.log" 2>&1 &
      _i=0
      while [ $_i -lt 15 ]; do sleep 1; _i=$((_i+1))
        curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1 && break
      done
      if ! curl -sf "${OLLAMA_ENDPOINT}/api/version" >/dev/null 2>&1; then
        _hard_fail "Ollama server did not start in 15s — see ${LOG_DIR}/ollama.log"
      else
        _ok "Ollama server started"
      fi
    else
      _hard_fail "Ollama server not reachable at ${OLLAMA_ENDPOINT}"
    fi
  else
    _OLLAMA_SERVER_VER="$(curl -sf "${OLLAMA_ENDPOINT}/api/version" 2>/dev/null \
      | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null || echo '?')"
    _ok "Ollama server running — v${_OLLAMA_SERVER_VER} at ${OLLAMA_ENDPOINT}"
  fi
else
  _warn "Phase 2 skipped — Ollama binary unavailable"
fi

# Cache ollama list output once (used in phases 3 + 4)
_OLLAMA_LIST=""
if [ "$HARD_FAIL" -eq 0 ]; then
  _OLLAMA_LIST="$(ollama list 2>/dev/null || true)"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 3 — HARD: Inference model (qwen3.5:9b-nvfp4)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 3 — Inference model probe (qwen3.5:9b-nvfp4)"

if [ "$HARD_FAIL" -eq 0 ]; then
  INFERENCE_MODEL="${OLLAMA_WARM_MODEL:-qwen3.5:9b-nvfp4}"
  INFERENCE_BASE="${INFERENCE_MODEL%%:*}"

  if echo "$_OLLAMA_LIST" | grep -qF "${INFERENCE_MODEL}" || echo "$_OLLAMA_LIST" | grep -qF "${INFERENCE_BASE}"; then
    _ok "Model ${INFERENCE_MODEL} present"
  elif [ "$MODE_CHECK" -eq 0 ]; then
    _info "Pulling ${INFERENCE_MODEL} (this may take several minutes)..."
    if ollama pull "${INFERENCE_MODEL}" 2>&1 | tee -a "${LOG_DIR}/ollama.log" | grep -v "^$"; then
      _ok "Model ${INFERENCE_MODEL} pulled"
      _OLLAMA_LIST="$(ollama list 2>/dev/null || true)"
    else
      _hard_fail "Failed to pull ${INFERENCE_MODEL}. Run: ollama pull ${INFERENCE_MODEL}"
    fi
  else
    _hard_fail "Model ${INFERENCE_MODEL} not installed. Run: ollama pull ${INFERENCE_MODEL}"
  fi
else
  _warn "Phase 3 skipped — Ollama unavailable"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 4 — HARD: Embedding model (bge-m3)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 4 — Embedding model probe (bge-m3)"

if [ "$HARD_FAIL" -eq 0 ]; then
  if echo "$_OLLAMA_LIST" | grep -qF "bge-m3"; then
    _ok "Model bge-m3 present"
  elif [ "$MODE_CHECK" -eq 0 ]; then
    _info "Pulling bge-m3 (required for gbrain embeddings)..."
    if ollama pull bge-m3 2>&1 | tee -a "${LOG_DIR}/ollama.log" | grep -v "^$"; then
      _ok "Model bge-m3 pulled"
    else
      _hard_fail "Failed to pull bge-m3. Run: ollama pull bge-m3"
    fi
  else
    _hard_fail "Model bge-m3 not installed. Run: ollama pull bge-m3"
  fi
else
  _warn "Phase 4 skipped — Ollama unavailable"
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 5 — SOFT: gbrain config validation
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 5 — gbrain config validation"

GBRAIN_CONFIG="${HOME}/.gbrain/config.json"
if [ ! -f "$GBRAIN_CONFIG" ]; then
  _warn "~/.gbrain/config.json not found — gbrain semantic search unavailable"
  _warn "Run: gbrain init  (see CLAUDE-instru.md §5)"
else
  _GBRAIN_MODEL=$(python3 -c "
import json, pathlib
try:
    d = json.loads(pathlib.Path('${GBRAIN_CONFIG}').read_text())
    print(d.get('embedding_model','missing'))
except Exception as e:
    print('error')
" 2>/dev/null || echo "parse-error")
  case "$_GBRAIN_MODEL" in
    "ollama:bge-m3") _ok "gbrain config: embedding_model=ollama:bge-m3 ✓" ;;
    "missing")       _warn "gbrain config: embedding_model key missing — add it (see CLAUDE-instru.md §5)" ;;
    *)               _warn "gbrain config: embedding_model=${_GBRAIN_MODEL} (expected ollama:bge-m3)" ;;
  esac
fi

# ──────────────────────────────────────────────────────────────────────────────
# PHASE 6 — SOFT: Python venv + pip deps (sha256-stamped)
# ──────────────────────────────────────────────────────────────────────────────
_info "Phase 6 — Python venv + dependencies"

VENV_FRESH=0
if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
  if [ "$MODE_CHECK" -eq 0 ]; then
    _info "Creating Python venv..."
    python3 -m venv "${SCRIPT_DIR}/.venv" >>"${LOG_DIR}/install.log" 2>&1 \
      || { _warn "venv creation failed — see ${LOG_DIR}/install.log"; }
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
      _info "Installing Python deps (requirements.txt changed)..."
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
  _err "Hard requirements FAILED — system cannot start. See output above."
  _err "Full probe spec: CLAUDE-instru.md §6"
  echo ""
  exit 1
else
  _ok "All hard requirements satisfied — $(_os_label) ready"
  echo ""
  exit 0
fi
