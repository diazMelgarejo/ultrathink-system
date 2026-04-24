#!/usr/bin/env bash
# install-multi-agent.sh
# The ὅραμα System — Multi-Agent Network Installer
# Installs the 7 agent markdown files to .claude/agents/ (Claude Code native
# subagent path) AND to the Clawdbot/MoltBot/OpenClaw-specific paths.
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
info() { echo -e "  ${BLUE}→${RESET} $1"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_SRC="$REPO_ROOT/bin/agents"

echo -e "${BOLD}🚀 ultrathink Multi-Agent Network Installer${RESET}"
echo "=============================================="
echo ""

# ── 1. .claude/agents/  (Claude Code native — THIS is the right path) ─────────
# These are the files Claude Code reads when spawning subagents.
# Already committed in the repo at .claude/agents/ultrathink-*.md
ok ".claude/agents/ultrathink-*.md  (committed in repo — Claude Code native subagents)"
echo "     Files present:"
for f in "$REPO_ROOT/.claude/agents"/ultrathink-*.md; do
  echo "       $(basename "$f")"
done

# ── 2. ~/.claude/agents/  (Claude Code global — available across all projects) ─
GLOBAL_AGENTS="$HOME/.claude/agents"
mkdir -p "$GLOBAL_AGENTS"
cp "$AGENTS_SRC/orchestrator/agent.md"   "$GLOBAL_AGENTS/ultrathink-orchestrator.md"
cp "$AGENTS_SRC/context/agent.md"        "$GLOBAL_AGENTS/ultrathink-context-agent.md"
cp "$AGENTS_SRC/architect/agent.md"      "$GLOBAL_AGENTS/ultrathink-architect-agent.md"
cp "$AGENTS_SRC/refiner/agent.md"        "$GLOBAL_AGENTS/ultrathink-refiner-agent.md"
cp "$AGENTS_SRC/executor/agent.md"       "$GLOBAL_AGENTS/ultrathink-executor-agent.md"
cp "$AGENTS_SRC/verifier/agent.md"       "$GLOBAL_AGENTS/ultrathink-verifier-agent.md"
cp "$AGENTS_SRC/crystallizer/agent.md"   "$GLOBAL_AGENTS/ultrathink-crystallizer-agent.md"
ok "~/.claude/agents/ultrathink-*.md  (Claude Code global subagents)"

# ── 3. Platform-specific paths ────────────────────────────────────────────────
if [ -d "$HOME/.clawdbot" ]; then
  mkdir -p "$HOME/.clawdbot/agents"
  cp -r "$REPO_ROOT/bin" "$HOME/.clawdbot/agents/ultrathink-network"
  ok "~/.clawdbot/agents/ultrathink-network/  (Clawdbot)"
fi
if [ -d "$HOME/.moltbot" ]; then
  mkdir -p "$HOME/.moltbot/agents"
  cp -r "$REPO_ROOT/bin" "$HOME/.moltbot/agents/ultrathink-network"
  ok "~/.moltbot/agents/ultrathink-network/  (MoltBot)"
fi
if [ -d "$HOME/.openclaw" ]; then
  mkdir -p "$HOME/.openclaw/agents"
  cp -r "$REPO_ROOT/bin" "$HOME/.openclaw/agents/ultrathink-network"
  ok "~/.openclaw/agents/ultrathink-network/  (OpenClaw)"
fi

# ── 4. Shared state dir ────────────────────────────────────────────────────────
mkdir -p "$HOME/.ultrathink/state"
ok "~/.ultrathink/state/  (shared agent state)"

# ── 5. Python deps check ────────────────────────────────────────────────────────
if python3 -c "import redis" 2>/dev/null; then
  ok "Redis available — production state backend ready"
else
  warn "Redis not installed — will use in-memory backend"
  echo "       pip install redis  (optional, for production deployments)"
fi

echo ""
echo -e "${BOLD}✅ Multi-agent network installed.${RESET}"
echo ""
echo "  Runtime path summary (Claude Code native):"
echo "  ──────────────────────────────────────────────────────────────────────"
echo "  .claude/agents/ultrathink-orchestrator.md    ← spawned by Mode 3 router"
echo "  .claude/agents/ultrathink-context-agent.md"
echo "  .claude/agents/ultrathink-architect-agent.md"
echo "  .claude/agents/ultrathink-refiner-agent.md"
echo "  .claude/agents/ultrathink-executor-agent.md"
echo "  .claude/agents/ultrathink-verifier-agent.md"
echo "  .claude/agents/ultrathink-crystallizer-agent.md"
echo ""
echo "  MCP server (for Clawdbot/OpenClaw orchestration):"
echo "  python bin/mcp_servers/ultrathink_orchestration_server.py"
echo ""
echo "  Claude Code .claude/settings.json MCP block:"
cat << JSON
  {
    "mcpServers": {
      "ultrathink": {
        "command": "python",
        "args": ["$REPO_ROOT/bin/mcp_servers/ultrathink_orchestration_server.py"]
      }
    }
  }
JSON
