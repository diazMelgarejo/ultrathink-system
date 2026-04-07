#!/usr/bin/env bash
# install.sh
# ultrathink System — Single-Agent + ECC/Codex Harness Installer
# =================================================================
# Installs the ultrathink skill to ~/.claude/skills/ultrathink-system-skill/
# Works with Claude Code CLI, Codex/OpenCode, and ECC.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/diazMelgarejo/ultrathink-system/main/install.sh | bash
#   # or locally:
#   bash install.sh
#   bash install.sh --project     # install to ./.claude/skills/ instead of global
#   bash install.sh --uninstall   # remove the skill

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
info() { echo -e "  ${BLUE}→${RESET} $1"; }

SKILL_NAME="ultrathink-system-skill"
REPO_URL="https://github.com/diazMelgarejo/ultrathink-system"
BRANCH="main"
SKILL_SOURCE="bin/skills"

# Default: global install
INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
MODE="global"

# ─── Argument parsing ────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --project|-p)
      INSTALL_DIR="./.claude/skills/$SKILL_NAME"
      MODE="project"
      ;;
    --uninstall|-u)
      echo -e "${YELLOW}Removing ultrathink skill...${RESET}"
      rm -rf "$HOME/.claude/skills/$SKILL_NAME" 2>/dev/null
      rm -rf "./.claude/skills/$SKILL_NAME" 2>/dev/null
      rm -rf "$HOME/.ecc/skills/$SKILL_NAME" 2>/dev/null
      rm -rf "./.ecc/skills/$SKILL_NAME" 2>/dev/null
      echo -e "${GREEN}Done.${RESET}"
      exit 0
      ;;
    --help|-h)
      echo "Usage: install.sh [--project] [--uninstall]"
      echo "  --project   Install to ./.claude/skills/ (project-local)"
      echo "  --uninstall Remove the ultrathink skill"
      exit 0
      ;;
  esac
done

# ─── Detect source ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo ". ")"
LOCAL_SOURCE="$SCRIPT_DIR/$SKILL_SOURCE"
TMPDIR=""

echo ""
echo -e "${BOLD}🚀 ultrathink System — Harness Install${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Mode:    ${BLUE}$MODE${RESET}"
echo -e "  Target:  ${BLUE}$INSTALL_DIR${RESET}"
echo ""

# ─── Install Core Skill ──────────────────────────────────────────────────────
if [[ -d "$LOCAL_SOURCE" ]]; then
  # Local install — copy from adjacent single_agent/ directory
  echo -e "  ${GREEN}Found local source:${RESET} $LOCAL_SOURCE"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  rm -rf "$INSTALL_DIR"
  cp -R "$LOCAL_SOURCE" "$INSTALL_DIR"
else
  # Remote install — clone from GitHub
  echo -e "  ${BLUE}Fetching from GitHub...${RESET}"
  TMPDIR=$(mktemp -d)
  trap "rm -rf $TMPDIR" EXIT

  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMPDIR/repo" 2>/dev/null

  if [[ ! -d "$TMPDIR/repo/$SKILL_SOURCE" ]]; then
    echo -e "  ${RED}Error: $SKILL_SOURCE not found in repo${RESET}"
    exit 1
  fi

  mkdir -p "$(dirname "$INSTALL_DIR")"
  rm -rf "$INSTALL_DIR"
  cp -R "$TMPDIR/repo/$SKILL_SOURCE" "$INSTALL_DIR"
  LOCAL_SOURCE="$TMPDIR/repo/$SKILL_SOURCE"
fi

# ─── Make scripts executable ─────────────────────────────────────────────────
chmod +x "$INSTALL_DIR/scripts/"*.py "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true

# ─── ECC Harness Hook ────────────────────────────────────────────────────────
for ECC_CANDIDATE in "$SCRIPT_DIR/.ecc" "$HOME/.ecc" ".ecc"; do
  if [ -d "$ECC_CANDIDATE" ]; then
    ECC_SKILLS="$ECC_CANDIDATE/skills/$SKILL_NAME"
    mkdir -p "$ECC_SKILLS"
    cp    "$LOCAL_SOURCE/SKILL.md"   "$ECC_SKILLS/"
    cp -r "$LOCAL_SOURCE/cidf"       "$ECC_SKILLS/" 2>/dev/null || true
    cp -r "$LOCAL_SOURCE/references" "$ECC_SKILLS/" 2>/dev/null || true
    ok ".ecc/skills/$SKILL_NAME/             (ECC harness)"
    break
  fi
done
if [ ! -d "${SCRIPT_DIR}/.ecc" ] && [ ! -d "$HOME/.ecc" ] && [ ! -d ".ecc" ]; then
  warn ".ecc/ not found — skip ECC install. Run after:"
  echo "        git clone https://github.com/affaan-m/everything-claude-code .ecc"
fi

# ─── Task Template Bootstrap ──────────────────────────────────────────────────
mkdir -p "$HOME/.ultrathink/tasks"
cp "$LOCAL_SOURCE/templates/"* "$HOME/.ultrathink/tasks/" 2>/dev/null || true
ok "~/.ultrathink/tasks/                             (plan + lessons templates)"

# ─── Verify ──────────────────────────────────────────────────────────────────
if [[ -f "$INSTALL_DIR/SKILL.md" ]]; then
  FILE_COUNT=$(find "$INSTALL_DIR" -type f | wc -l | tr -d ' ')
  echo ""
  echo -e "  ${GREEN}${BOLD}Installed successfully!${RESET}"
  echo -e "  ${GREEN}$FILE_COUNT files${RESET} -> ${BLUE}$INSTALL_DIR${RESET}"
  echo ""
  echo -e "  ${BOLD}Included:${RESET}"
  echo -e "    SKILL.md          Master methodology (5-stage + router + 6 directives)"
  echo -e "    afrp/             Audience-First Response Protocol (pre-router gate)"
  echo -e "    cidf/             Content Insertion Decision Framework v1.2"
  echo -e "    references/       5 deep-dive documents (progressive disclosure)"
  echo -e "    templates/        Task plan, verification checklist, lessons log"
  echo -e "    scripts/          verify_before_done.py, capture_lesson.py, create_task_plan.sh"
  echo -e "    config/           Agent registry + routing rules (Mode 3)"
  echo ""
  echo -e "  ${BOLD}How to use:${RESET}"
  echo -e "    Claude CLI:     Auto-activates on relevant queries"
  echo -e "    Manual load:    ${BLUE}/skill ultrathink${RESET} in Claude Code"
  echo ""
else
  echo -e "  ${RED}Installation failed — SKILL.md not found${RESET}"
  exit 1
fi
