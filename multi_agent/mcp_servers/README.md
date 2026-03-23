# MCP Servers

## ultrathink_orchestration_server.py
Main orchestration entry point. Exposes: `ultrathink_solve`, `ultrathink_delegate`, `ultrathink_status`, `ultrathink_lessons`.

```bash
python ultrathink_orchestration_server.py    # stdio transport (Claude Code)
```

**openclaw.json integration**:
```json
{ "agents": [{ "id": "ultrathink", "mcp_url": "stdio:///path/to/ultrathink_orchestration_server.py" }] }
```

## agent_communication_server.py
Inter-agent messaging. Exposes: `agent_send`, `agent_receive`, `agent_list`.

## Claude Code Integration
Add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "ultrathink": {
      "command": "python",
      "args": ["/path/to/ultrathink_orchestration_server.py"]
    }
  }
}
```
