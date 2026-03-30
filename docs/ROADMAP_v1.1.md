# Roadmap: v1.1+ — Deferred Items

**Status:** TODO — not scheduled for v1.0 RC
**Last updated:** 2026-03-30

This document lists architecture enhancements explicitly deferred from MVP to v1.1 and above.

---

## 1. MCP-Optional Transport (v1.1)

**Current state (v1.0 RC):** PT calls ultrathink via HTTP bridge (`POST /ultrathink` on api_server.py port 8001). The HTTP bridge is the active v1.0 RC transport.

**v1.1 target:** MCP over stdio becomes an optional transport alongside HTTP. Both coexist; callers opt in to MCP when the environment supports it. HTTP bridge remains fully supported.

### Implementation Order — Read Before Starting

> **Start here (Tier 2) before PT builds Tier 1.**
> Tier 1 (MCP client infrastructure in PT) is tracked in
> [Perplexity-Tools/docs/ROADMAP_v1.1.md](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/ROADMAP_v1.1.md).
>
> **The HTTP bridge stays fully functional at every intermediate state.**
> No feature breaks if this work is incomplete or abandoned mid-flight:
> - Before Tier 2: PT's MCP client (if built) sees a stub response and falls back to HTTP automatically.
> - After Tier 2, before Tier 1: Ollama pipeline runs in MCP server; HTTP bridge unchanged, still primary.
> - After both tiers: PT tries MCP first, falls back to HTTP on any subprocess failure. HTTP is never removed.

### Required work:

#### Tier 2 — MCP server pipeline (real Ollama backend, ultrathink-system side)

- [ ] Extract Ollama pipeline into `multi_agent/shared/ollama_client.py`
  - Move `_build_prompt()`, `_call_ollama()`, `_call_with_fallback()`, `_select_model()` out of `api_server.py`
  - Both `api_server.py` and `ultrathink_orchestration_server.py` import from this shared module
  - No behavior change to `api_server.py` — just moves code, all tests still pass
- [ ] Implement `_solve()` in `ultrathink_orchestration_server.py` to call Ollama synchronously
  - Return full result inline (`{"result": str, "task_id": str, "model_used": str, ...}`)
  - Skip polling design — synchronous return matches HTTP contract, simplifies client
  - Map `optimize_for` → `reasoning_depth` via `bridge_contract.py`
  - Use `ollama_client.generate()` with primary/fallback endpoint logic
- [ ] Implement `_delegate()` with real message bus publish (or document as intentional stub)
- [ ] Wire `_status()` to real `StateManager` backends
- [ ] Wire `_lessons()` to real lessons store
- [ ] Create `tests/test_mcp_server.py`
  - Mock Ollama: `_solve()` returns full result inline
  - `_status()` with known task_id
  - `_lessons()` with domain filter
- [ ] Add tests for MCP success and MCP-failure-to-HTTP-fallback (coordinated with PT Tier 1 tests)

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
