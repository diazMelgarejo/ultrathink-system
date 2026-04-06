#!/usr/bin/env bash
# scripts/simulate_ci.sh
# ======================
# Simulate the exact GitHub Actions CI environment locally.
# Catches dependency and build errors BEFORE they reach CI.
#
# Usage:
#   bash scripts/simulate_ci.sh           # full simulation
#   bash scripts/simulate_ci.sh --quick   # tests only (skip build)
#   bash scripts/simulate_ci.sh --clean   # force fresh venv
#
# What it mirrors:
#   - .github/workflows/test.yml  (Test Suite job)
#   - .github/workflows/ci.yml    (test job, build job)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
VENV_DIR=".venv-ci-sim"
PYTHON="python3"
QUICK=false
CLEAN=false
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'

for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=true ;;
    --clean) CLEAN=true ;;
  esac
done

pass() { echo -e "${GREEN}✓ $1${RESET}"; }
fail() { echo -e "${RED}✗ $1${RESET}"; exit 1; }
info() { echo -e "${YELLOW}▶ $1${RESET}"; }
banner() { echo -e "\n${BOLD}${1}${RESET}\n$(printf '─%.0s' {1..60})"; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

banner "🚀 CI Simulation — ultrathink-system"
echo "Mirrors: test.yml + ci.yml"
echo "Mode: $([ "$QUICK" = true ] && echo "quick (tests only)" || echo "full")"

# ── Step 1: Fresh venv ────────────────────────────────────────────────────────
banner "[1/5] Creating fresh virtual environment"
if [ "$CLEAN" = true ] && [ -d "$VENV_DIR" ]; then
  info "Removing existing $VENV_DIR ..."
  rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
  $PYTHON -m venv "$VENV_DIR"
  pass "Created $VENV_DIR"
else
  pass "Reusing $VENV_DIR (use --clean to force fresh)"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── Step 2: Exact CI install sequence ─────────────────────────────────────────
banner "[2/5] Installing dependencies (mirrors CI exactly)"
info "Step: pip install --upgrade pip setuptools wheel"
$VENV_PIP install --upgrade pip setuptools wheel --quiet

# Mirror test.yml: install hatchling before editable install (prevents chicken-and-egg)
info "Step: pip install hatchling  (build backend must be pre-installed)"
$VENV_PIP install hatchling --quiet

info "Step: pip install -e \".[test]\""
$VENV_PIP install -e ".[test]" --quiet

# Verify all required modules are importable
banner "[3/5] Verifying imports (the check CI skips)"
REQUIRED=(fastapi httpx uvicorn pydantic slowapi pytest hatchling build)
ALL_OK=true
for mod in "${REQUIRED[@]}"; do
  if $VENV_PY -c "import $mod" 2>/dev/null; then
    pass "import $mod"
  else
    echo -e "${RED}✗ import $mod — NOT FOUND${RESET}"
    ALL_OK=false
  fi
done
if [ "$ALL_OK" = false ]; then
  fail "Import check failed — these modules would cause ModuleNotFoundError in CI"
fi

# ── Step 3: Run pytest (mirrors ci.yml + test.yml) ────────────────────────────
banner "[4/5] Running pytest (mirrors CI)"
info "pytest -q tests/"
if $VENV_PY -m pytest -q tests/ 2>&1; then
  pass "All tests passed"
else
  fail "Tests failed — fix before pushing"
fi

# ── Step 4: Build (mirrors ci.yml Build Package step) ────────────────────────
if [ "$QUICK" = false ]; then
  banner "[5/5] Building package (mirrors ci.yml 'Build package' step)"
  info "python -m build"
  if $VENV_PY -m build --quiet 2>&1; then
    pass "Build succeeded"
    WHEEL=$(ls dist/ultrathink_system-*.whl 2>/dev/null | tail -1)
    if [ -n "$WHEEL" ]; then
      pass "Wheel produced: $(basename "$WHEEL")"
    else
      fail "No wheel found in dist/"
    fi
  else
    fail "Build failed — 'python -m build' would fail in CI"
  fi
else
  info "[5/5] Build skipped (--quick mode)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
banner "✅ CI Simulation PASSED"
echo -e "All steps that would run in GitHub Actions completed successfully."
echo -e "Safe to push.\n"
