#!/usr/bin/env bash
# install-single_agent.sh
# ultrathink System — Single-Agent Installer
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

echo -e "${BOLD}🚀 ultrathink Single-Agent Installation${RESET}"
echo "========================================"
echo ""

# Detect platform
if command -v claude &>/dev/null; then
    CLAUDE_DIR="$HOME/.claude/skills"
    PLATFORM="Claude Code"
elif [ -d "$HOME/.cowork" ]; then
    CLAUDE_DIR="$HOME/.cowork/skills"
    PLATFORM="Cowork"
elif [ -d "$HOME/.ecc/skills" ]; then
    CLAUDE_DIR="$HOME/.ecc/skills"
    PLATFORM="ECC Tools"
else
    CLAUDE_DIR="$HOME/.claude/skills"
    PLATFORM="Generic Claude"
fi

echo -e "  ${BLUE}Platform${RESET}: $PLATFORM"
echo -e "  ${BLUE}Directory${RESET}: $CLAUDE_DIR"
echo ""

mkdir -p "$CLAUDE_DIR"

# Copy or symlink
if [[ "${1:-}" == "--symlink" ]]; then
    ln -sf "$(pwd)/single_agent" "$CLAUDE_DIR/ultrathink-system-skill"
    echo -e "  ${GREEN}✓${RESET} Symlinked ultrathink-system-skill (updates automatically)"
else
    cp -r single_agent "$CLAUDE_DIR/ultrathink-system-skill"
    echo -e "  ${GREEN}✓${RESET} Installed ultrathink-system-skill"
fi

# Bootstrap tasks dir
mkdir -p "$HOME/.ultrathink/tasks"
cp single_agent/templates/* "$HOME/.ultrathink/tasks/" 2>/dev/null || true

# Make scripts executable
chmod +x "$CLAUDE_DIR/ultrathink-system-skill/scripts/"*.py \
         "$CLAUDE_DIR/ultrathink-system-skill/scripts/"*.sh 2>/dev/null || true

echo ""
echo -e "${BOLD}✅ Installation complete!${RESET}"
echo ""
echo -e "  ${GREEN}Quick Start:${RESET}"
echo "  1. Open your Claude interface"
echo "  2. Say: 'Apply ultrathink system to: [your task]'"
echo "  3. Or: 'ultrathink this'"
echo ""
echo -e "  ${YELLOW}Scripts:${RESET}"
echo "  ./single_agent/scripts/create_task_plan.sh 'Task name'"
echo "  python single_agent/scripts/verify_before_done.py --task 'Task'"
echo "  python single_agent/scripts/capture_lesson.py"
echo ""
echo -e "  ${BLUE}Docs:${RESET} $CLAUDE_DIR/ultrathink-system-skill/README.md"
