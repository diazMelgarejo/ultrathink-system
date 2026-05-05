# Module: MCP-Optional Transport

> Status: stub — ex-v1.1 roadmap item

## What it does

Expose `oramasys` as a real MCP server with actual Ollama/LM Studio calls (not the stub `_solve()` that v1.0 RC ships). Makes `perpetua-core` callable from any MCP-aware host (Claude Code, OpenClaw, etc.) in addition to the existing HTTP surface.

## Current state in v1.0 RC

`orama-system/bin/mcp_servers/ultrathink_orchestration_server.py` — exposes MCP tool schema but `_solve()` returns a stub. No real Ollama call.

## v2.0+ implementation plan

1. Implement `_solve()` to call `oramasys`'s FastAPI surface (HTTP → MCP adapter)
2. OR: expose `MiniGraph.ainvoke()` directly from the MCP server (tighter coupling but lower latency)
3. Prefer option 1: MCP server calls the HTTP surface → clean separation

## Dependencies

- `oramasys/orama/api/server.py` (must be running)
- `perpetua_core` (via oramasys)
- MCP SDK (`mcp` Python package)
