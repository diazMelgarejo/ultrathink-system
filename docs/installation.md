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
cp -r bin/orama-system ~/.claude/skills/orama-system

# Cowork
cp -r bin/orama-system ~/.cowork/skills/orama-system

# Any Claude platform — place in skills dir
cp -r bin/orama-system /path/to/your/skills/orama-system
```

### ECC Tools / everything-claude-code

```bash
# Drop into existing skill library
cp -r bin/orama-system ~/.claude/skills/orama-system
# or if using ecc-tools profile
cp -r bin/orama-system ~/.ecc/skills/orama-system
```

---

## Multi-Agent Network (Clawdbot / MoltBot / OpenClaw)

### Automated

```bash
./install-multi-agent.sh
```

### Manual

```bash
cp -r bin ~/.clawdbot/agents/ultrathink-network
# or
cp -r bin ~/.openclaw/agents/ultrathink-network
```

### Start the MCP Server

```bash
cd bin/mcp_servers
python ultrathink_orchestration_server.py
```

### Claude Code MCP Integration

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ultrathink": {
      "command": "python",
      "args": ["/path/to/bin/mcp_servers/ultrathink_orchestration_server.py"]
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
✓ bin/orama-system/SKILL.md found
✓ All 7 agent files found
✅ Package integrity: VERIFIED
```
