# ultrathink Multi-Agent Network
**7 specialized agents for distributed problem solving**

## Quick Start
```bash
# Install
cp -r . ~/.clawdbot/agents/ultrathink-network

# Start MCP server
python mcp_servers/ultrathink_orchestration_server.py

# Use from Claude Code
# Add to .claude/settings.json mcpServers block (see docs/installation.md)
```

## Architecture
See root `README.md` for the full agent network diagram.

## Agents

| Agent | Stage | Role |
|-------|-------|------|
| Orchestrator | All | Coordinates 5-stage workflow |
| Context | 1 | Progressive context gathering |
| Architect | 2 | Modular design + interfaces |
| Refiner | 3 | Eliminate non-essential complexity |
| Executor | 4 | TDD implementation (up to 5× parallel) |
| Verifier | 4.5 | Programmatic verification |
| Crystallizer | 5 | Documentation + lessons |
