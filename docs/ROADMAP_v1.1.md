# Roadmap: v1.1+ — Deferred Items

**Status:** TODO — not scheduled for v1.0 RC
**Last updated:** 2026-03-30

This document lists architecture enhancements explicitly deferred from MVP to v1.1 and above.

---

## 1. MCP-Optional Transport (v1.1)

**Current state (v1.0 RC):** PT calls ultrathink via HTTP bridge (`POST /ultrathink` on api_server.py port 8001). The HTTP bridge is the active v1.0 RC transport.

**v1.1 target:** MCP over stdio becomes an optional transport alongside HTTP. Both coexist; callers opt in to MCP when the environment supports it. HTTP bridge remains fully supported.

### Required work:
- [ ] Flesh out MCP server stubs in `multi_agent/mcp_servers/ultrathink_orchestration_server.py`
  - `_solve()` must call Ollama and run actual 5-stage reasoning (currently returns stub)
  - `_delegate()` must publish to message bus (currently returns stub)
  - `_status()` and `_lessons()` need real state/lessons backends
- [ ] Build MCP client in PT (`orchestrator/ultrathink_mcp_client.py`)
  - Spawn `ultrathink_orchestration_server.py` as subprocess
  - JSON-RPC framing over stdin/stdout
  - Lifecycle management (start, health check, restart on crash)
- [ ] Update `orchestrator/fastapi_app.py` bridge logic:
  - Try MCP client first
  - On MCP failure, fall back to HTTP bridge
  - Surface transport method in response (`"transport": "mcp"` or `"transport": "http"`)
- [ ] Switch `httpx.post` (sync) to `httpx.AsyncClient` in bridge to avoid blocking event loop
- [ ] Add tests for both MCP success and MCP-failure-to-HTTP-fallback paths

### Protocol boundary:
| Dimension | MCP Server (v1.1) | HTTP Server (current) |
|-----------|-------------------|-----------------------|
| Input | `task` + `optimize_for` | `task_description` + `reasoning_depth` |
| Translation | Native | `bridge_contract.py` maps between the two |
| Transport | stdio JSON-RPC | HTTP POST |

The `bridge_contract.py` module already handles the mapping — both transports can coexist.

---

## 2. Redis-Backed Coordination (PT-only)

**Current state (MVP):** PT uses file-based state (`.state/agents.json`). ultrathink is stateless.

**v1.1 target:** Redis enables distributed coordination when running multiple PT instances.

### Required work:
- [ ] Redis as optional backend in PT for `.state/agents.json` (agent registry)
- [ ] Redis pub/sub for inter-PT-instance communication
- [ ] Distributed locking for agent spawn deduplication
- [ ] Budget tracking via Redis atomic counters (currently file-based)

### Rules:
- Redis lives in PT ONLY — ultrathink never depends on it
- Redis is optional — file-based state continues to work for single-instance/LAN
- Redis only activates when `REDIS_ENABLED=true` in PT `.env`

---

## 3. Multi-Instance PT Beyond LAN

**Current state (MVP):** Single PT instance per LAN. Mac controller + Windows GPU runner.

**v1.1 target:** Multiple PT instances across different networks, coordinated via Redis.

### Required work:
- [ ] Service discovery beyond mDNS/LAN scan
- [ ] Auth between PT instances
- [ ] Conflict resolution for overlapping agent spawns across instances
- [ ] Centralized budget enforcement across instances

---

## References
- Architecture decision: ultrathink stateless, PT owns state (locked v0.9.7.0)
- Canonical MVP wording in PT SKILL.md "State Ownership & Redis Strategy" section
- Bridge contract: `multi_agent/shared/bridge_contract.py`
- MCP server (stubs): `multi_agent/mcp_servers/ultrathink_orchestration_server.py`
- HTTP server (live): `api_server.py`
