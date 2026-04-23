# Sync Analysis: orama-system ↔ Perplexity-Tools

**Date:** 2026-04-11 | **Version:** ultrathink v0.9.9.7 · PT v0.9.9.7

> **v1.0 RC transport clarification:** HTTP Bridge (`POST /ultrathink` via `api_server.py`)
> is the **active primary transport** for v1.0 RC. MCP-Optional transport (stdio JSON-RPC)
> is planned for v1.1. Any references below to "MCP as primary" or "HTTP as backup" reflect
> older analysis snapshots and should be read as pre-v0.9.9.0 context.
---

## TL;DR — Status Summary

| Dimension | Status | Notes |
|---|---|---|
| **Version** | ✅ IN SYNC | Both at v0.9.9.7 |
| **Architecture contract** | ✅ IN SYNC | 4-layer hierarchy documented + upheld |
| **Bridge doc** | ✅ IN SYNC | PERPLEXITY_BRIDGE.md aligned to v0.9.9.7; HAL cross-link complete 
| **API endpoint spec** | ✅ IN SYNC | HTTP Bridge (`POST /ultrathink`) is v1.0 RC primary transport; MCP-Optional planned for v1.1 |
| **Idempotency contract** | ✅ RESOLVED | PT owns all state via `.state/agents.json`; ultrathink stateless (no Redis). Redis deferred to PT v1.1+ |
| **Shared `.env` contract** | ✅ IN SYNC | Vars in both `.env.example` files match BRIDGE doc |
| **SKILL.md cross-ref** | ✅ IN SYNC | PT SKILL.md references ultrathink routing methodology |
| **ECC Tools integration** | ✅ IN SYNC | Both agree on ECC as Stage-4 sub-agent selector |
| **autoresearch integration** | ✅ IN SYNC | Both reference uditgoenka/autoresearch equally |
| **Cross-repo README links** | ✅ IN SYNC | PT README links to orama-system; ultrathink README lists PT |
| **CI/CD** | ✅ IN SYNC | Both repos have `.github/workflows/ci.yml` with pytest + lint |
| **Tests** | ✅ RESOLVED | PT now has 6 test files (56+ tests); ultrathink has 86+ tests |
| **routing.yml** | ✅ IN SYNC | PT `config/routing.yml` has `deep_reasoning` + `code_analysis` ultrathink routes |
| **HAL doc cross-ref** | ✅ IN SYNC | PERPLEXITY_BRIDGE.md HAL section complete; 
| **PT hardware cross-link (OPT 1)** | ✅ RESOLVED | ultrathink `bin/skills/SKILL.md` references PT `hardware/SKILL.md`; `portal_server.py` and `network_autoconfig.py` are documented as active LAN helpers |
| **PT `pyproject.toml` (OPT 2)** | ✅ RESOLVED | PT now pip-installable as `perplexity-tools`; `[tool.pytest.ini_options]` + dev extras included |
| **Integration test suite (OPT 3)** | ✅ RESOLVED | `tests/test_ultrathink_integration.py` — 12 tests verifying routing.yml ↔ ultrathink | **Integration test suite (OPT 3)** | ✅ RESOLVED | `tests/test_ultrathink_integration.py` — 12 tests verifying routing.yml ↔ ultrathink contract |

## What IS Working (Synergized Well)

### 1. Architecture Hierarchy — Correct and Consistent

Both repos agree on the 4-layer stack:

```
Perplexity-Tools    ← top-level orchestrator, model selection, fallback chain
orama-system   ← reasoning engine, 5-stage methodology, CIDF
ECC Tools           ← Stage-4 parallel sub-agent auto-selection (up to 5x)
autoresearch        ← research automation, idempotent sync
```

Priority rule is identical in both READMEs. No conflict.

### 2. Version Parity — Both at v0.9.8.0

Aligned same day (2026-03-28). Releases match.

### 3. Cross-Reference Links — Complete

- PT README → links orama-system (GitHub URL + role description)
- ultrathink README → lists PT in "Compatible with" + architecture table
- PERPLEXITY_BRIDGE.md → full integration doc with code examples

### 4. SKILL.md Routing Contract — Agreed

Both agree:
- PT SKILL.md = top-level model selection runs **first**
- ultrathink bin/skills/SKILL.md = reasoning methodology, called **by** PT when deep reasoning needed
- ECC Tools = sub-agent selection for Stage-4 parallel executors

### 5. Fallback Chain — Documented and Consistent

```
PT receives task → deep reasoning? → call ultrathink:8001
  → timeout? → local Qwen3:30b on Dell
  → realtime/finance? → Perplexity Grok 4.1
  → simple Q&A? → local Qwen3:8b
```

### 6. Tests — Both Repos Now Covered

**Perplexity-Tools** `tests/` (6 files, 56+ tests):
- `test_routing.py` — routing.yml contract, ultrathink routes, autoresearch routes
- `test_resilience.py` — connectivity resilience + fallback behaviour
- `test_lan_discovery.py` — LAN device discovery
- `test_agent_tracker.py` — 18 tests: AgentTracker lifecycle (register, update, find, conflicts, destroy)
- `test_cost_guard.py` — 16 tests: CostGuard budget, spend, alert, auto-reset, snapshot
- `test_autoresearch_bridge.py` — 22 tests: SwarmState parsing, GPU lock, preflight (all SSH mocked)

**orama-system** `tests/` — 86+ tests, full CI coverage.

### 7. CI/CD — Both Repos Active

- PT `.github/workflows/ci.yml`: pytest + flake8 lint + routing.yml validation, Python 3.11/3.12 matrix
- ultrathink `.github/workflows/ci.yml` + `release.yml`: pytest + build + lint

## Resolved Gaps (History)

### GAP 1: `api_server.py` — HISTORICAL BACKUP PATH

Earlier sync snapshots treated `api_server.py` as the primary bridge and
documented `POST /ultrathink` plus `GET /health`. In the current checkout,
that server exists as an implemented backup method with request/response tests,
but it is still not the primary bridge contract.

### GAP 2: PT `routing.yml` — ✅ RESOLVED (v0.9.5.0)

`config/routing.yml` now has `deep_reasoning` and `code_analysis` routes with ultrathink endpoint + fallback to `local_qwen30b`.

### GAP 3: `.env` Contract — ✅ RESOLVED (v0.9.5.0)

Both `.env.example` files contain all vars specified in PERPLEXITY_BRIDGE.md.

### GAP 4: Idempotency — ✅ RESOLVED (v0.9.7.0)

Architecture decision locked: ultrathink remains **stateless** with no Redis requirement. PT is the sole orchestration layer and owns agent instantiation, tracking, queueing, budget enforcement, and file-based runtime state. Redis-backed coordination deferred to PT v1.1+ for multi-instance distributed deployments.

### GAP 5: PT Has No Tests — ✅ RESOLVED (v0.9.8.0)

6 test files now in `Perplexity-Tools/tests/` covering all critical orchestrator modules.

### GAP 6: PT Has No CI/CD — ✅ RESOLVED (v0.9.6.0)

`.github/workflows/ci.yml` created in PT with pytest + flake8 + YAML validation.

## Open Items (P2 / Future)

### OPT 1: ultrathink SKILL.md → PT Hardware Profile Cross-Link

**Status:** ✅ RESOLVED (rolling — pre-v1.0 RC)

**Implemented:** ultrathink `bin/skills/SKILL.md` updated (commit `ac292db`) with hardware-aware routing section referencing PT `hardware/SKILL.md`. `orchestrator/__init__.py` also updated with `__version__` for package metadata consistency.

orama-system's `bin/skills/SKILL.md` should reference PT's hardware profiles so that when running inside PT orchestration, ultrathink knows to respect PT's hardware-aware routing.

**Suggested addition to ultrathink SKILL.md:**
```
When running inside Perplexity-Tools orchestration:
- Respect PT's model selection for top-level agents (see hardware/SKILL.md)
- Only override model choice when the backup HTTP path uses `reasoning_depth = ultra`
- Accept model_hint in request payload; use DEFAULT_MODEL as fallback
```

### OPT 2: `pyproject.toml` in PT

**Status:** ✅ RESOLVED (rolling — pre-v1.0 RC)

**Implemented:** `pyproject.toml` added to Perplexity-Tools root (commit `5082db6`). Includes `[project]` metadata, `[project.optional-dependencies]` for dev/test, and `[tool.pytest.ini_options]` config. PT is now pip-installable as `perplexity-tools`.

orama-system is pip-installable. PT only has `requirements.txt`. Making PT installable enables consistent versioning and dependency pinning across the stack.

### OPT 3: Unified Integration Test

**Status:** ✅ RESOLVED (rolling — pre-v1.0 RC)

**Implemented:** `tests/test_ultrathink_integration.py` added to Perplexity-Tools (commit `c84a5f6`). 12 tests in `TestRoutingYmlUltrathinkContract` verifying `deep_reasoning` + `code_analysis` routes declare `ULTRATHINK_ENDPOINT`, `fallback=local_qwen30b`, and `requires=[ultrathink_available]`.

A single integration test that fires a task at PT and verifies it correctly routes to ultrathink:

```python
def test_deep_reasoning_routes_to_ultrathink():
    # Historical backup flow: POST to PT with privacy_critical=True
    # Assert ultrathink endpoint was called
    # Assert result structure matches BRIDGE spec
```

## What NOT to Change

- **Do not merge the repos.** Independent configurability is a feature.
- **Do not make ultrathink stateful** with its own agent registry. PT owns that.
- **Do not add Perplexity API calls to ultrathink.** It stays local-only (privacy layer).
- **Do not change the priority rule.** PT SKILL.md → ECC → ultrathink ordering is correct.

## Update 2026-03-27: v0.9.5.0 Hardware Abstraction Layer [SYNC]

### Status: P0 & P1 Gaps RESOLVED ✅

All critical integration gaps from the initial analysis have been addressed.

**P0 — RESOLVED:**
- Historical backup path: older sync snapshots referenced `api_server.py`
  - `POST /ultrathink` and `GET /health` are implemented backup endpoints in this checkout
  - Wire to 5-stage reasoning pipeline complete
  - Runs on port 8001 as specified
  - v0.9.8.0: rate limiting, Pydantic V2 validators, security hardening

**P1 — RESOLVED:**
- ✅ orama-system `.env.example` updated with required API/model vars
- ✅ Perplexity-Tools `.env.example` updated with `ULTRATHINK_ENDPOINT`, `ULTRATHINK_TIMEOUT`, `ULTRATHINK_ENABLED`
- ✅ PT `config/routing.yml` now has `deep_reasoning` and `code_analysis` routes with ultrathink endpoint + fallback

### New in PT v0.9.5.0: Hardware Abstraction Layer

Perplexity-Tools has added hardware-aware orchestration:

#### Added Files:

- `hardware/SKILL.md` — Hardware profiles for `mac-studio` (Apple Silicon) and `win-rtx3080` (Dell RTX 3080)
  - Role-based model assignment matrix
  - VRAM/RAM safety rules
  - Fallback degradation chains
- `hardware/Modelfile.win-rtx3080` — Ollama Modelfile for Qwen3.5-35B-A3B with Flash Attention + KV cache compression
- `hardware/Modelfile.mac-studio` — Ollama Modelfile for Qwen3.5-9B manager agent with unified memory tuning
- `agent_launcher.py` — Hardware detection script with graceful degradation (Distributed → Mac-only → LM Studio → Cloud)
  - Outputs routing state to `.state/agents.json`
  - 3-second timeout to avoid blocking
- `setup_wizard.py` — Idempotent installation wizard
  - Scans for existing AI software (Ollama, LM Studio, MLX)
  - Tiered setup guidance (Priority 1: easiest, Priority 2: advanced)

#### Model Updates:

- Qwen3.5-35B-A3B MoE (Windows): `frob/qwen3.5:35b-a3b-instruct-ud-q4_K_M`
- Qwen3.5-9B (Mac manager): `qwen3.5:9b-instruct`
- MLX path preferred on Apple Silicon for maximum performance

### Sync Impactdocs(sync): mark Recommended Next Action #2 DONE in SYNC_ANALYSIS.md

**No Breaking Changes:**
- orama-system API contract unchanged
- 4-layer architecture priority rule preserved
- ultrathink remains stateless; PT owns dedup via `.state/agents.json`

**Coordination Items (updated):**
- [x] PERPLEXITY_BRIDGE.md updated with Hardware Abstraction Layer section
- [x] orama-system SKILL.md should reference hardware profiles from PT for optimal model selection
- [x] Consider adding hardware profile awareness to ultrathink's model selection if it needs to make autonomous model choices

**Tests & CI (P2 items RESOLVED):**
- ✅ PT now has `tests/` with 6 test files (56+ tests)
- ✅ PT now has `.github/workflows/ci.yml`
- ✅ orama-system maintains 86+ tests + CI

### Recommended Next Actions

1. ✅ **Cross-link SKILL.md files** — DONE: ultrathink SKILL.md now references PT `hardware/SKILL.md` for hardware-aware model selection
2. ✅ **Add integration test** — DONE: `tests/test_hardware_routing.py` (commit `82cb179`) verifies PT correctly routes deep reasoning tasks to ultrathink with hardware-appropriate models (mac-studio → MLX backend; win-rtx3080 → Ollama backend).
3. :white_check_mark: **Hardware-agnostic core + model_hint passthrough** — IMPLEMENTED BACKUP NOTE: the HTTP `api_server.py` bridge accepts `model_hint`, but PT's `hardware/SKILL.md` remains the active hardware-routing source of truth.

### Architecture Decision Record: ADR-001 (v0.9.9.0)

**Decision:** orama-system remains fully hardware-agnostic at its core.

**Context:** PT v0.9.5.0 added a Hardware Abstraction Layer (`hardware/SKILL.md`, `agent_launcher.py`) that detects mac-studio (MLX) vs win-rtx3080 (Ollama/CUDA) and assigns optimal models per hardware profile. The question arose: should ultrathink replicate this hardware detection internally?

**Decision drivers:**
- ultrathink's purpose is reasoning methodology, not hardware orchestration
- PT already owns the hardware layer; duplication would violate the 4-layer hierarchy
- ultrathink must remain stateless and portable (privacy-critical local-only design)
- Adding hardware detection to ultrathink would tighten coupling and break portability

**Resolution:** Hardware-agnostic core with optional `model_hint` passthrough:
- `UltraThinkRequest.model_hint: Optional[str]` — PT may inject a hardware-appropriate model name
- `_select_model()` honors `model_hint` when present; falls back to task-type heuristic otherwise
- ultrathink logs `hint=<model>` so operators can verify PT is routing correctly
- `metadata.model_hint_used: bool` in response so PT can audit hint acceptance

**Consequences:**
- mac-studio PT instance: sends `model_hint=qwen3:8b-instruct` (MLX-optimised)
- win-rtx3080 PT instance: sends `model_hint=qwen3:30b-a3b-instruct-q4_K_M` (Ollama GGUF)
- ultrathink standalone (no PT): falls back to internal heuristic (unchanged behavior)
- No breaking change — `model_hint` is optional; existing callers unaffected

**Status:** Implemented backup note — do not treat `api_server.py v0.9.9.0` as the active primary contract in this checkout.

## Update 2026-03-30: v0.9.9.0 v1.0 RC Refinements [SYNC]

### Transport Naming Corrected
- **HTTP Bridge (`POST /ultrathink`)** is now documented as the v1.0 RC primary transport.
- **MCP-Optional transport** (stdio JSON-RPC) renamed from "MCP-first" — planned for v1.1.
  `ultrathink_orchestration_server.py` MCP `_solve()` remains a stub; no production Ollama call yet.
- Both repos updated: `api_server.py` docstring, `PERPLEXITY_BRIDGE.md`, both `ROADMAP_v1.1.md` files.

### Redis Import Hardened
- `orchestrator.py` soft import: `try: import redis.asyncio as _redis_mod / except ImportError: _redis_mod = None`
- `requirements.txt` redis moved to optional comment.
- Test `test_orchestrator_starts_without_redis_package` added.

### ECC Sync Gate Added
- `ECC_SYNC_ENABLED` env var in `orchestrator/ecc_tools_sync.py` (default: true).
- `tests/conftest.py` sets `ECC_SYNC_ENABLED=false` at session scope so tests never hit the network.

### MCP-Optional v1.1 TODO Checklists Added
- Tier 1 (PT): `orchestrator/ultrathink_mcp_client.py`, `call_ultrathink_mcp_or_bridge()`, tests — in `PT/docs/ROADMAP_v1.1.md`.
- Tier 2 (ultrathink): `bin/shared/ollama_client.py`, `_solve()` real pipeline, tests — in `ultrathink/docs/ROADMAP_v1.1.md`.
- Recommended sequencing: Tier 2 (server pipeline) before Tier 1 (client infrastructure).

### Test Count
- PT: 108 tests passing (up from 93 before v0.9.9.0 refinements).
- orama-system: unchanged, CI green.

---

**Generated:** 2026-03-30 | **Analyst:** Claude Sonnet 4.6
