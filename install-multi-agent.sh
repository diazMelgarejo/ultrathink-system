#!/usr/bin/env bash
# install-multi_agent.sh
# ultrathink System — Multi-Agent Network Installer
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

echo -e "${BOLD}🚀 ultrathink Multi-Agent Network Installation${RESET}"
echo "=============================================="
echo ""

# Detect platform
if [ -d "$HOME/.clawdbot" ]; then
    INSTALL_DIR="$HOME/.clawdbot/agents";  PLATFORM="Clawdbot"
elif [ -d "$HOME/.moltbot" ]; then
    INSTALL_DIR="$HOME/.moltbot/agents";   PLATFORM="MoltBot"
elif [ -d "$HOME/.openclaw" ]; then
    INSTALL_DIR="$HOME/.openclaw/agents";  PLATFORM="OpenClaw"
else
    INSTALL_DIR="$HOME/.ultrathink/agents"; PLATFORM="Generic"
fi

echo -e "  ${BLUE}Platform${RESET}: $PLATFORM"
echo -e "  ${BLUE}Directory${RESET}: $INSTALL_DIR"
echo ""

mkdir -p "$INSTALL_DIR"
cp -r multi_agent "$INSTALL_DIR/ultrathink-network"
mkdir -p "$HOME/.ultrathink/state"

find "$INSTALL_DIR/ultrathink-network" -name "*.py" -exec chmod +x {} \;
find "$INSTALL_DIR/ultrathink-network" -name "*.sh" -exec chmod +x {} \;

echo -e "  ${GREEN}✓${RESET} Installed ultrathink-network (7 agents)"

# Check Python deps
if python3 -c "import redis" &>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} Redis available (production state backend)"
else
    echo -e "  ${YELLOW}⚠${RESET}  Redis not installed — will use in-memory backend"
    echo "     To install: pip install redis"
fi

echo ""
echo -e "${BOLD}✅ Installation complete!${RESET}"
echo ""
echo -e "  ${GREEN}Next Steps:${RESET}"
echo "  1. Start MCP server:"
echo -e "     ${BLUE}cd $INSTALL_DIR/ultrathink-network/mcp_servers${RESET}"
echo "     python ultrathink_orchestration_server.py"
echo ""
echo "  2. Add to .claude/settings.json:"
cat << JSON
     {
       "mcpServers": {
         "ultrathink": {
           "command": "python",
           "args": ["$INSTALL_DIR/ultrathink-network/mcp_servers/ultrathink_orchestration_server.py"]
         }
       }
     }
JSON
echo ""
echo -e "  ${BLUE}Docs:${RESET} $INSTALL_DIR/ultrathink-network/README.md"
