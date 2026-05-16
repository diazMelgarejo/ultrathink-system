#!/usr/bin/env bash
# install-mcp-stack.sh — Idempotent MCP orchestration stack installer
# Installs: ai-cli-mcp + OpenClaw MCP registry entries, and Gemini only when
# explicitly requested via --include-gemini
# Safe to run multiple times. Skips any step that is already complete.
# Usage: bash install-mcp-stack.sh [--dry-run] [--force] [--include-gemini] [--mirror-skills]
#
# --mirror-skills: copy SKILL.md files from bin/orama-system/*/SKILL.md to
#   ~/.claude/skills/<name>/SKILL.md, ~/.codex/skills/<name>/SKILL.md,
#   ~/.gemini/skills/<name>/SKILL.md (silently skipped if dir absent), and
#   openclaw skill registry (if openclaw CLI present). Idempotent (sha-compares).

set -euo pipefail

DRY_RUN=false
FORCE=false
INCLUDE_GEMINI=false
MIRROR_SKILLS=false
for arg in "$@"; do
  [ "$arg" = "--dry-run" ] && DRY_RUN=true
  [ "$arg" = "--force" ] && FORCE=true
  [ "$arg" = "--include-gemini" ] && INCLUDE_GEMINI=true
  [ "$arg" = "--mirror-skills" ] && MIRROR_SKILLS=true
done

_log()  { echo "[mcp-install] $*"; }
_ok()   { echo "[mcp-install] ✓ $*"; }
_skip() { echo "[mcp-install] → skip: $*"; }
_fail() { echo "[mcp-install] ✗ FATAL: $*" >&2; exit 1; }
_run()  { $DRY_RUN && echo "[dry-run] $*" || eval "$*"; }

_log "MCP orchestration stack installer — 2026-04-25"
_log "Dry-run: $DRY_RUN | Force: $FORCE"
echo ""

# ── Step 1: Node.js ≥20 hard gate ────────────────────────────────────────────
_log "Step 1: Node.js preflight"
if ! command -v node >/dev/null 2>&1; then
  _fail "Node.js not found. Install from https://nodejs.org (v20 or newer required)."
fi
NODE_MAJOR=$(node -e "process.stdout.write(String(process.version.match(/^v(\d+)/)[1]))")
if [ "$NODE_MAJOR" -lt 20 ]; then
  _fail "Node.js v${NODE_MAJOR} detected. v20 or newer required. Install from https://nodejs.org."
fi
_ok "Node.js v$(node -v) — ok"

# ── Step 2: Gemini CLI ────────────────────────────────────────────────────────
# ── Step 2: ai-cli-mcp ────────────────────────────────────────────────────────
_log "Step 2: ai-cli-mcp"
_AICLI_VER=$(ai-cli --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo '')
if command -v ai-cli >/dev/null 2>&1 && ! $FORCE; then
  _skip "ai-cli already installed (${_AICLI_VER:-via npx})"
else
  _log "Installing ai-cli-mcp globally..."
  _run "npm install -g ai-cli-mcp"
fi

_log "Step 2b: Register ai-cli-mcp in Claude Code"
if claude mcp list 2>/dev/null | grep -q "ai-cli" && ! $FORCE; then
  _skip "ai-cli already registered in Claude Code"
else
  _run "claude mcp add -s user ai-cli -- npx -y ai-cli-mcp@latest"
  _ok "ai-cli registered in Claude Code"
fi

# ── Step 3: Claude first-run acceptance ───────────────────────────────────────
_log "Step 3: ai-cli-mcp first-run acceptance"
CLAUDE_ACCEPTED_MARKER="$HOME/.claude/.dangerously-skip-accepted"
if [ -f "$CLAUDE_ACCEPTED_MARKER" ] && ! $FORCE; then
  _skip "claude first-run prompt already accepted"
else
  _log "Accepting Claude first-run prompts (required for ai-cli background workers)..."
  _log "Note: --dangerously-skip-permissions applies to this one-time acceptance only."
  if ! $DRY_RUN; then
    echo "" | timeout 5 claude --dangerously-skip-permissions 2>/dev/null || true
    touch "$CLAUDE_ACCEPTED_MARKER"
  fi
  _ok "Claude first-run prompt accepted"
fi

# ── Step 4: Optional Gemini analyzer lane ────────────────────────────────────
_log "Step 4: Gemini analyzer lane"
if ! $INCLUDE_GEMINI; then
  _skip "Gemini not requested; analyzer lane remains opt-in"
else
  if command -v gemini >/dev/null 2>&1 && ! $FORCE; then
    _skip "gemini already installed ($(gemini --version 2>/dev/null | head -1 || echo 'version unknown'))"
  else
    _log "Installing @google/gemini-cli..."
    _run "npm install -g @google/gemini-cli"
  fi

  _log "Step 4b: Gemini auth check"
  if gemini auth check >/dev/null 2>&1 && ! $FORCE; then
    _skip "gemini already authenticated"
  else
    _log "Launching gemini auth login (interactive — follow the browser prompt)..."
    if ! $DRY_RUN; then
      gemini auth login || _fail "Gemini auth failed. Run 'gemini auth login' manually and retry."
      gemini auth check >/dev/null 2>&1 || _fail "Gemini auth check failed after login."
    fi
    _ok "gemini authenticated"
  fi

  _log "Step 4c: Register gemini-mcp-tool in Claude Code"
  if claude mcp list 2>/dev/null | grep -q "gemini-cli" && ! $FORCE; then
    _skip "gemini-cli already registered in Claude Code"
  else
    _run "claude mcp add -s user gemini-cli -- npx -y gemini-mcp-tool@latest"
    _ok "gemini-cli registered. Restart Claude Code, then verify with /mcp"
  fi
fi

# ── Step 5: OpenClaw MCP registry ────────────────────────────────────────────
_log "Step 5: OpenClaw MCP registry"
if command -v openclaw >/dev/null 2>&1; then
  if openclaw mcp list 2>/dev/null | grep -q "ai-cli-mcp" && ! $FORCE; then
    _skip "ai-cli-mcp already in OpenClaw registry"
  else
    _run "openclaw mcp set ai-cli-mcp '{\"command\":\"npx\",\"args\":[\"-y\",\"ai-cli-mcp@latest\"],\"env\":{\"MCP_CLAUDE_DEBUG\":\"false\"}}'"
    _ok "ai-cli-mcp registered in OpenClaw"
  fi
  if $INCLUDE_GEMINI; then
    if openclaw mcp list 2>/dev/null | grep -q "gemini-cli" && ! $FORCE; then
      _skip "gemini-cli already in OpenClaw registry"
    else
      _run "openclaw mcp set gemini-cli '{\"command\":\"npx\",\"args\":[\"-y\",\"gemini-mcp-tool@latest\"]}'"
      _ok "gemini-cli registered in OpenClaw"
    fi
  fi
else
  _log "openclaw not found — skipping OpenClaw registry step"
  _log "To register manually: openclaw mcp set ai-cli-mcp '{...}'"
fi

# ── Step 6: Final verification ───────────────────────────────────────────────
echo ""
# ── Step 5b: Mirror orama SKILL.md to platform skill directories ─────────────
if $MIRROR_SKILLS; then
  _log "Step 5b: Mirroring orama SKILL.md files to platform skill dirs"
  # Resolve the bin/orama-system root relative to this script.
  _SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  _SKILLS_ROOT="$(cd "$_SCRIPT_DIR/.." && pwd)"
  # Target platform skill dirs — silently skipped if absent (and tool absent).
  _PLATFORMS=(
    "$HOME/.claude/skills:claude"
    "$HOME/.codex/skills:codex"
    "$HOME/.gemini/skills:gemini"
  )
  # Each subdir of $_SKILLS_ROOT that has a SKILL.md is a mirrorable skill.
  for _src_skill in "$_SKILLS_ROOT"/*/SKILL.md "$_SKILLS_ROOT/SKILL.md"; do
    [ -f "$_src_skill" ] || continue
    if [ "$_src_skill" = "$_SKILLS_ROOT/SKILL.md" ]; then
      _skill_name="orama-system"
    else
      _skill_name="$(basename "$(dirname "$_src_skill")")"
    fi
    for _plat in "${_PLATFORMS[@]}"; do
      _dst_root="${_plat%%:*}"
      _tool="${_plat##*:}"
      _dst_dir="$_dst_root/$_skill_name"
      _dst="$_dst_dir/SKILL.md"
      # Only mirror if root exists OR force is set
      if [ ! -d "$_dst_root" ] && ! $FORCE; then
        _skip "$_tool (no $_dst_root)"
        continue
      fi
      # Sha-compare for idempotency
      if [ -f "$_dst" ] && command -v shasum >/dev/null 2>&1; then
        _src_hash=$(shasum -a 256 "$_src_skill" | awk '{print $1}')
        _dst_hash=$(shasum -a 256 "$_dst" | awk '{print $1}')
        if [ "$_src_hash" = "$_dst_hash" ]; then
          _skip "$_tool/$_skill_name (identical)"
          continue
        fi
      fi
      _run "mkdir -p \"$_dst_dir\" && install -m 0644 \"$_src_skill\" \"$_dst\""
      _ok "mirror $_skill_name → $_tool"
    done
  done
  # OpenClaw skill registry (if openclaw CLI present)
  if command -v openclaw >/dev/null 2>&1; then
    for _src_skill in "$_SKILLS_ROOT"/*/SKILL.md; do
      [ -f "$_src_skill" ] || continue
      _skill_name="$(basename "$(dirname "$_src_skill")")"
      _run "openclaw skill set \"$_skill_name\" \"$_src_skill\""
      _ok "openclaw skill set $_skill_name"
    done
  else
    _skip "openclaw skill registry (openclaw CLI not installed)"
  fi
  echo ""
fi

_log "Step 6: Verification summary"
echo ""
echo "  node:    $(node -v 2>/dev/null || echo 'missing')"
echo "  ai-cli:  $(ai-cli --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo 'via npx (ok)')"
echo "  claude mcp list:"
claude mcp list 2>/dev/null | grep -E "gemini-cli|ai-cli" | sed 's/^/    /' || echo "    (run 'claude mcp list' manually)"
if command -v openclaw >/dev/null 2>&1; then
  echo "  openclaw mcp list:"
  openclaw mcp list 2>/dev/null | grep -E "gemini-cli|ai-cli" | sed 's/^/    /' || echo "    (empty)"
fi
echo ""
_log "Installation complete."
if $INCLUDE_GEMINI; then
  _log "Restart Claude Code, then run /mcp to confirm gemini-cli and ai-cli-mcp are active."
else
  _log "Restart Claude Code, then run /mcp to confirm ai-cli-mcp is active."
fi

# ── Rollback instructions ────────────────────────────────────────────────────
cat << 'ROLLBACK'

── ROLLBACK (if something went wrong) ──────────────────────────────────────────
  npm uninstall -g @google/gemini-cli ai-cli-mcp
  claude mcp remove -s user gemini-cli 2>/dev/null || claude mcp remove gemini-cli 2>/dev/null || true
  claude mcp remove -s user ai-cli 2>/dev/null || claude mcp remove ai-cli 2>/dev/null || true
  openclaw mcp unset gemini-cli 2>/dev/null || true
  openclaw mcp unset ai-cli-mcp 2>/dev/null || true
────────────────────────────────────────────────────────────────────────────────
ROLLBACK
