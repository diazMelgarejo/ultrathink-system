# Perplexity-Tools Bridge for The ὅραμα System

## Version 0.9.9.8

## Current Contract (v1.0 RC)

**Active transport:** HTTP Bridge (`POST /ultrathink` on port 8001 via `api_server.py`).
MCP-Optional transport is planned for v1.1 — see [MCP-Optional Transport (v1.1)](#mcp-optional-transport-v11) below.

- `Perplexity-Tools` remains the top-level orchestrator and selects ultrathink
  behavior through `task_type` routing (`deep_reasoning`, `code_analysis`).
- `orama-system` serves the HTTP bridge via `api_server.py` (FastAPI, port 8001).
- The MCP server (`bin/mcp_servers/ultrathink_orchestration_server.py`)
  exposes the tool surface below but its `_solve()` is a stub — it does not yet
  call Ollama. All production traffic flows through the HTTP bridge.
- MCP tool surface (v1.1+ target):
  - `ultrathink_solve`
  - `ultrathink_delegate`
  - `ultrathink_status`
  - `ultrathink_lessons`

## HTTP Bridge Flow (v1.0 RC)

`Perplexity-Tools` reaches the local ultrathink reasoning layer by choosing
local-only route types such as `deep_reasoning` and `code_analysis`.

- `reasoning_depth` is not a field on `Perplexity-Tools` `OrchestrateRequest`.
- `privacy_critical` is not a live `Perplexity-Tools` request field in this
  checkout.
- Privacy isolation is currently structural: the ultrathink routes require
  `ultrathink_available` and do not include cloud or online model roles.

The practical current mapping is:

| Perplexity-Tools decision | Current bridge effect |
|---|---|
| `task_type=deep_reasoning` | Use the local ultrathink reasoning path |
| `task_type=code_analysis` | Use the local ultrathink code-analysis path |
| ultrathink unavailable | Fall back to the configured local model chain |

## Hardware Note

Perplexity-Tools owns hardware-aware routing before tasks reach ultrathink.

- `mac-studio` and `win-rtx3080` profiles stay on the PT side.
- Current PT defaults are `Mac=http://192.168.254.103:1234` and `Win=http://192.168.254.100:1234` for LM Studio.
- PT prefers `glm-5.1:cloud` for the thin Mac orchestrator lane when the live probe succeeds, then falls back to Mac LM Studio.
- PT prefers `Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2` for Windows heavy coding and autoresearch, with `qwen3-coder:14b` and `qwen3.5:35b-a3b-q4_K_M` retained as fallbacks.
- ultrathink remains the hardware-agnostic local reasoning layer.
- The implemented HTTP backup bridge accepts `model_hint`, but PT still owns
  the hardware-routing decision that produces that hint.

## Current MCP Runtime

Run the current in-repo bridge with:

```bash
cd orama-system
python bin/mcp_servers/ultrathink_orchestration_server.py
```

The MCP server publishes the tool schemas defined in `TOOL_SCHEMAS` and is the
current source of truth for bridge behavior in this repository.

## HTTP Bridge Status (v1.0 RC — Primary Transport)

The HTTP `/ultrathink` path via `api_server.py` is the **primary v1.0 RC transport**.

- Fully implemented: FastAPI + uvicorn, port 8001, rate-limited, Pydantic V2 validated.
- All production PT→ultrathink calls go through this path.
- Semantically aligned with MCP through shared `bridge_contract.py` mapping helpers.
- Will remain supported when MCP-Optional transport lands in v1.1 (HTTP is not deprecated).

The exact contract mapping is:

| MCP `optimize_for` | HTTP `reasoning_depth` |
|---|---|
| `reliability` | `ultra` |
| `creativity` | `deep` |
| `speed` | `standard` |

The backup HTTP bridge also accepts `model_hint` for compatibility, but PT
hardware routing remains owned by `Perplexity-Tools`.

If neither `reasoning_depth` nor `optimize_for` is supplied, the backup server
keeps the legacy HTTP default of `reasoning_depth=standard` for compatibility
with existing direct HTTP callers.

## MCP-Optional Transport (v1.1)

MCP-Optional adds stdio JSON-RPC transport alongside HTTP. Both coexist; callers
opt in to MCP when the environment supports it. HTTP bridge remains fully supported.

### Transport naming convention

| Release | Transport | Status |
|---------|-----------|--------|
| v1.0 RC | HTTP Bridge (`POST /ultrathink`) | **Active — ships now** |
| v1.1 | MCP-Optional (stdio JSON-RPC) | Planned — opt-in alongside HTTP |
| Future | MCP-Primary (if HTTP ever retired) | Not scheduled |

### Why MCP `_solve()` currently falls back to HTTP

The MCP server's `_solve()` creates a `TaskState` and returns a stub:
```json
{"task_id": "...", "status": "started", "message": "Poll ultrathink_status for updates."}
```
It does not call Ollama or run the 5-stage pipeline. Until Tier 2 is implemented,
any MCP client will fall back to HTTP automatically.

### Implementation sequencing (Tier 2 before Tier 1)

**Step 1 — Tier 2 (orama-system, do this first):**
Extract Ollama pipeline into `bin/shared/ollama_client.py`, then implement
`_solve()` to call Ollama synchronously and return the full result inline —
matching the HTTP synchronous contract, no polling loop needed.

**Step 2 — Tier 1 (Perplexity-Tools, do this after Tier 2 is merged):**
Build `orchestrator/ultrathink_mcp_client.py` (subprocess lifecycle + JSON-RPC
framing), add `call_ultrathink_mcp_or_bridge()` to `ultrathink_bridge.py` with
HTTP fallback, expose `"transport": "mcp"` or `"transport": "http"` in the
response envelope.

**Why this order:** Tier 1 infrastructure without Tier 2 means every call falls
back to HTTP anyway — the client would be untestable end-to-end. Building the
real server backend first makes Tier 1 immediately verifiable.

**The HTTP bridge stays fully functional at every intermediate state.**
Nothing breaks if work is paused or abandoned between tiers:
- Before Tier 2: MCP client (if built early) detects stub response (`status: started`, no `result`) and falls back to HTTP automatically.
- After Tier 2, before Tier 1: MCP server returns real results; HTTP bridge unchanged, still the active primary transport.
- After both tiers: PT tries MCP first, falls back to HTTP on any subprocess failure. HTTP is never deprecated.

### Checklist links
- Tier 1 TODO: [Perplexity-Tools/docs/ROADMAP_v1.1.md](../../perplexity-api/Perplexity-Tools/docs/ROADMAP_v1.1.md)
- Tier 2 TODO: [orama-system/docs/ROADMAP_v1.1.md](ROADMAP_v1.1.md)

---

## Historical HTTP Design Context

Earlier drafts described an HTTP escape hatch where `Perplexity-Tools` would
call `/ultrathink` and pass `reasoning_depth`. That design now exists as an
implemented backup method rather than a future-only note.

- `reasoning_depth` belongs to the backup HTTP design, not the live PT request
  model.
- `privacy_critical` explained why sensitive tasks should stay local, but it is
  still not a live PT request field in this checkout.
- PT continues to express primary routing intent through `task_type`, while the
  backup HTTP server normalizes optional `optimize_for` into `reasoning_depth`.

## Version Compatibility

This bridge documentation assumes:

- orama-system >= v0.9.9.7
- Perplexity-Tools >= v0.9.0.0
- Python >= 3.8

## Related Documentation

- Perplexity-Tools: `SKILL.md`, `README.md`
- orama-system: `README.md`, `docs/api-reference.md`
- MCP runtime: `bin/mcp_servers/README.md`
