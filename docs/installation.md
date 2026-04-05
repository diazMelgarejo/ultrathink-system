# Installation Guide

## Prerequisites
- Python 3.8+ (for scripts)
- Bash 4+ (for shell scripts)
- Claude Code, Cowork, Clawdbot, MoltBot, or OpenClaw installed
- Git (optional, for cloning)
- Redis (optional, for multi-agent production mode)

---

## Single-Agent (Claude Code / Cowork / Open)

### Automated
```bash
./install.sh
```

### Manual
```bash
# Claude Code
cp -r single_agent ~/.claude/skills/ultrathink-system-skill

# Cowork
cp -r single_agent ~/.cowork/skills/ultrathink-system-skill

# Any Claude platform — place in skills dir
cp -r single_agent /path/to/your/skills/ultrathink-system-skill
```

### ECC Tools / everything-claude-code
```bash
# Drop into existing skill library
cp -r single_agent ~/.claude/skills/ultrathink-system-skill
# or if using ecc-tools profile
cp -r single_agent ~/.ecc/skills/ultrathink-system-skill
```

---

## Multi-Agent Network (Clawdbot / MoltBot / OpenClaw)

### Automated
```bash
./install-multi-agent.sh
```

### Manual
```bash
cp -r multi-agent ~/.clawdbot/agents/ultrathink-network
# or
cp -r multi-agent ~/.openclaw/agents/ultrathink-network
```

### Start the MCP Server
```bash
cd multi_agent/mcp_servers
python ultrathink_orchestration_server.py
```

### Claude Code MCP Integration
Add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "ultrathink": {
      "command": "python",
      "args": ["/path/to/multi_agent/mcp_servers/ultrathink_orchestration_server.py"]
    }
  }
}
```

---

## Verify Installation
```bash
./verify-package.sh
```

Expected output:
```
✓ LICENSE found
✓ single_agent/SKILL.md found
✓ All 7 agent files found
✅ Package integrity: VERIFIED
```
