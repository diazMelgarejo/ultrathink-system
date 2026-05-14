# 15 — v2 Alpha As-Built Notes (2026-05-01)

> Records what the canonical `oramasys/*` repos shipped in their v2.0-alpha.1 build.
> All three repos were pushed to GitHub on 2026-05-01 and remain 0 ahead/0 behind remote.
> Status: **reference doc** — no code changes implied here.

---

## What shipped (2026-05-01)

### `oramasys/perpetua-core` — kernel

**Commit:** `2f717f5` "feat: perpetua-core v2.0 alpha — 70-line kernel + plugin system (32/32 tests)"
**Tests:** 32 passing (Python 3.11+)
**Remote:** `github.com/oramasys/perpetua-core`

| Module | File | Notes |
|--------|------|-------|
| State | `perpetua_core/state.py` | `BaseModel`, `scratchpad: dict[str,Any]`, `HardwareTier`/`TaskType`/`OptHint` literals, `merge()` via `model_copy()` |
| LLM client | `perpetua_core/llm.py` | Async OpenAI-compatible; `LLM_BASE_URL` env var |
| Hardware policy | `perpetua_core/policy.py` | `HardwarePolicyResolver`, `HardwareAffinityError` |
| Gossip bus | `perpetua_core/gossip.py` | `aiosqlite` (async, 47 lines) |
| Graph engine | `perpetua_core/graph/engine.py` | **65 lines**, START/END sentinels, duck-typed HITL via `Interrupt` exception |
| Plugin: checkpointer | `perpetua_core/graph/plugins/checkpointer.py` | SQLite state snapshots |
| Plugin: interrupts | `perpetua_core/graph/plugins/interrupts.py` | `Interrupt` + `aresume()` |
| Plugin: streaming | `perpetua_core/graph/plugins/streaming.py` | `AsyncGenerator` token + state streaming |
| Plugin: structured_output | `perpetua_core/graph/plugins/structured_output.py` | Force LLM → Pydantic v2 shapes |
| Plugin: subgraphs | `perpetua_core/graph/plugins/subgraphs.py` | Nested `MiniGraph` as node |
| Plugin: tool | `perpetua_core/graph/plugins/tool.py` | `@tool` decorator, auto-schema from type hints |

**Key design confirmations vs. spec:**
- `PerpetuaState` is `BaseModel` (not dataclass) ✅ matches `01-kernel-spec.md`
- `scratchpad: dict[str, Any]` ✅ matches `01-kernel-spec.md`
- `optimize_for: OptHint = "quality"` is ON `PerpetuaState` (matches Grok synthesis, D8)
- `target_tier`, `task_type`, `model_hint` fields present (Grok additions, not in original spec)
- Engine is 65 lines — matches D8 revision ("~70-line kernel + plugins")
- All 6 Tier-3 features ship as plugins (not inline in engine)
- `aiosqlite` used throughout — no sync SQLite

**Open gaps (Phase 2 work):**
- `MiniGraph.max_steps` safety guard not implemented (OQ12 — still open)
- No `perpetua_core/message.py` typed Message wrapper — messages are plain `dict` (OQ17 — still open)

---

### `oramasys/oramasys` — methodology + FastAPI layer

**Commit:** `d123420` "feat: oramasys v2.0 alpha — FastAPI glass-window + hardware-routed graph (4/4 tests)"
**Tests:** 4 passing
**Remote:** `github.com/oramasys/oramasys`

| Module | File | Notes |
|--------|------|-------|
| Graph | `orama/graph/perpetua_graph.py` | 3-node: route → dispatch → respond; hardware affinity gate in `route_node` |
| API server | `orama/api/server.py` | FastAPI `/run` + `/health`, handlers ≤ 10 lines ✅ |
| API contracts | `orama/api/contracts.py` | `RunRequest` → `PerpetuaState`, `RunResponse` from state |

**Open gaps (Phase 3 work):**
- `dispatch_node` is a placeholder (echo-only) — not wired to `LLMClient` (OQ15 partial, Phase 3)
- No `TaskPlan` / `OramaToPTBridge` migration from v1 yet (OQ15 — still open)

---

### `oramasys/agate` — hardware policy specification

**Commits:** `755e1de` / `f1d5a57`
**Remote:** `github.com/oramasys/agate`

| Module | File | Notes |
|--------|------|-------|
| JSON Schema | `schemas/model_hardware_policy.schema.json` | Hardware policy schema v1 |
| Examples | `examples/` | Example policy YAMLs |
| GGUF RFC | `docs/gguf-hardware-affinity-rfc.md` | Community RFC for `system_requirements` in GGUF |

**Open gaps (future work):**
- Bridge adapter (OramaToPTBridge → agate) not yet implemented (OQ15)
- IDE API surface not yet in agate (future scope from D5 / agate vision)

---

## OQs resolved by this build

| OQ | Resolution | Date |
|----|------------|------|
| OQ4 — GitHub org `oramasys` | **Resolved:** org exists at `github.com/oramasys`; all 3 v2 repos live there | 2026-05-01 |
| OQ7 — Python version | **Resolved:** canonical uses Python 3.11+; `requires-python = ">=3.11"` in all 3 pyproject.toml files | 2026-05-01 |
| OQ8 — `optimize_for` field name | **Resolved:** `optimize_for: OptHint = "quality"` is on `PerpetuaState` directly (matches Grok synthesis and policy routing key structure) | 2026-05-01 |
| OQ11 — GossipBus async | **Resolved:** `aiosqlite` used from day one; no sync sqlite3 in the codebase | 2026-05-01 |
| (was OQ13) — PerpetuaState dataclass vs BaseModel | **Resolved:** `BaseModel` with `ConfigDict` in canonical | 2026-05-01 |
| (was OQ14) — `perpetua-core` org transfer | **Resolved:** canonical was always under `oramasys` org | 2026-05-01 |
| (was OQ16) — engine.py size and integration | **Resolved:** 65-line pure engine + `graph/plugins/` — D8 revision is implemented | 2026-05-01 |

---

## Note on `diazMelgarejo/perpetua-core` (divergent build)

A divergent build (`9cb153a`, 2026-05-14) was accidentally created at the wrong local path
and pushed to `diazMelgarejo/perpetua-core`. It is SUPERSEDED by this canonical build.
See `docs/wiki/10-wrong-repo-build-what-not-to-do.md` for the full post-mortem.

No further work goes to `diazMelgarejo/perpetua-core`.
