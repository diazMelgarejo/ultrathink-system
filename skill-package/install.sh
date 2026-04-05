#!/usr/bin/env bash
# install.sh — One-click installer for the ultrathink Claude Skill
# =================================================================
# Installs the ultrathink skill into ~/.claude/skills/ultrathink/
# Works with Claude Code CLI and Claude Desktop.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/diazMelgarejo/ultrathink-system/main/skill-package/install.sh | bash
#   # or locally:
#   bash install.sh
#   bash install.sh --project     # install to ./.claude/skills/ instead of global
#   bash install.sh --uninstall   # remove the skill

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

SKILL_NAME="ultrathink"
REPO_URL="https://github.com/diazMelgarejo/ultrathink-system"
BRANCH="main"
SKILL_SOURCE="skill-package/ultrathink"

# Default: global install to ~/.claude/skills/
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_SOURCE="$SCRIPT_DIR/ultrathink"

echo ""
echo -e "${BOLD}ultrathink Skill Installer${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Mode:    ${BLUE}$MODE${RESET}"
echo -e "  Target:  ${BLUE}$INSTALL_DIR${RESET}"
echo ""

# ─── Install ─────────────────────────────────────────────────────────────────
if [[ -d "$LOCAL_SOURCE" ]]; then
  # Local install — copy from adjacent ultrathink/ directory
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
    echo -e "  ${RED}Error: skill-package/ultrathink not found in repo${RESET}"
    exit 1
  fi

  mkdir -p "$(dirname "$INSTALL_DIR")"
  rm -rf "$INSTALL_DIR"
  cp -R "$TMPDIR/repo/$SKILL_SOURCE" "$INSTALL_DIR"
fi

# ─── Make scripts executable ─────────────────────────────────────────────────
chmod +x "$INSTALL_DIR/scripts/"*.py "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true

# ─── Verify ──────────────────────────────────────────────────────────────────
if [[ -f "$INSTALL_DIR/SKILL.md" ]]; then
  FILE_COUNT=$(find "$INSTALL_DIR" -type f | wc -l | tr -d ' ')
  echo ""
  echo -e "  ${GREEN}${BOLD}Installed successfully!${RESET}"
  echo -e "  ${GREEN}$FILE_COUNT files${RESET} -> ${BLUE}$INSTALL_DIR${RESET}"
  echo ""
  echo -e "  ${BOLD}Installed structure:${RESET}"
  find "$INSTALL_DIR" -type f | sort | while read -r f; do
    echo -e "    ${BLUE}$(echo "$f" | sed "s|$INSTALL_DIR/||")${RESET}"
  done
  echo ""
  echo -e "  ${BOLD}How to use:${RESET}"
  echo -e "    Claude CLI:     The skill auto-activates on relevant queries"
  echo -e "    Claude Desktop: The skill auto-activates on relevant queries"
  echo -e "    Manual load:    ${CYAN:-\033[0;36m}/skill ultrathink${RESET} in Claude Code"
  echo ""
  echo -e "  ${BOLD}Included:${RESET}"
  echo -e "    SKILL.md          Master methodology (5-stage + router + 6 directives)"
  echo -e "    afrp/SKILL.md     Audience-First Response Protocol (pre-router gate)"
  echo -e "    cidf/SKILL.md     Content Insertion Decision Framework v1.2"
  echo -e "    references/       5 deep-dive documents (progressive disclosure)"
  echo -e "    templates/        Task plan, verification checklist, lessons log"
  echo -e "    scripts/          verify_before_done.py, capture_lesson.py, create_task_plan.sh"
  echo -e "    config/           Agent registry + routing rules (Mode 3)"
  echo ""
else
  echo -e "  ${RED}Installation failed — SKILL.md not found${RESET}"
  exit 1
fi
