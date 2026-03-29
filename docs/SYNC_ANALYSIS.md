# Sync Analysis: ultrathink-system ↔ Perplexity-Tools

**Date:** 2026-03-28 | **Version:** ultrathink v0.9.8.0 · PT v0.9.8.0
---

## TL;DR — Status Summary

| Dimension | Status | Notes |
|---|---|---|
| **Version** | ✅ IN SYNC | Both at v0.9.8.0 |
| **Architecture contract** | ✅ IN SYNC | 4-layer hierarchy documented + upheld |
| **Bridge doc** | ✅ IN SYNC | PERPLEXITY_BRIDGE.md aligned to v0.9.8.0; HAL cross-link complete 
| **API endpoint spec** | ✅ IN SYNC | `api_server.py` v0.9.8.0; POST /ultrathink + GET /health + rate limiting |
| **Idempotency contract** | ✅ RESOLVED | PT owns all state via `.state/agents.json`; ultrathink stateless (no Redis). Redis deferred to PT v1.1+ |
| **Shared `.env` contract** | ✅ IN SYNC | Vars in both `.env.example` files match BRIDGE doc |
| **SKILL.md cross-ref** | ✅ IN SYNC | PT SKILL.md references ultrathink routing methodology |
| **ECC Tools integration** | ✅ IN SYNC | Both agree on ECC as Stage-4 sub-agent selector |
| **autoresearch integration** | ✅ IN SYNC | Both reference karpathy/autoresearch equally |
| **Cross-repo README links** | ✅ IN SYNC | PT README links to ultrathink-system; ultrathink README lists PT |
| **CI/CD** | ✅ IN SYNC | Both repos have `.github/workflows/ci.yml` with pytest + lint |
| **Tests** | ✅ RESOLVED | PT now has 6 test files (56+ tests); ultrathink has 86+ tests |
| **routing.yml** | ✅ IN SYNC | PT `config/routing.yml` has `deep_reasoning` + `code_analysis` ultrathink routes |
| **HAL doc cross-ref** | ✅ IN SYNC | PERPLEXITY_BRIDGE.md HAL section complete; 
| **PT hardware cross-link (OPT 1)** | ✅ RESOLVED | ultrathink `single_agent/SKILL.md` references PT `hardware/SKILL.md`; `orchestrator/__init__.py` has `__version__` |
| **PT `pyproject.toml` (OPT 2)** | ✅ RESOLVED | PT now pip-installable as `perplexity-tools`; `[tool.pytest.ini_options]` + dev extras included |
| **Integration test suite (OPT 3)** | ✅ RESOLVED | `tests/test_ultrathink_integration.py` — 12 tests verifying routing.yml ↔ ultrathink | **Integration test suite (OPT 3)** | ✅ RESOLVED | `tests/test_ultrathink_integration.py` — 12 tests verifying routing.yml ↔ ultrathink contract |

## What IS Working (Synergized Well)

### 1. Architecture Hierarchy — Correct and Consistent

Both repos agree on the 4-layer stack:

```
Perplexity-Tools    ← top-level orchestrator, model selection, fallback chain
ultrathink-system   ← reasoning engine, 5-stage methodology, CIDF
ECC Tools           ← Stage-4 parallel sub-agent auto-selection (up to 5x)
autoresearch        ← research automation, idempotent sync
```

Priority rule is identical in both READMEs. No conflict.

### 2. Version Parity — Both at v0.9.8.0

Aligned same day (2026-03-28). Releases match.

### 3. Cross-Reference Links — Complete

- PT README → links ultrathink-system (GitHub URL + role description)
- ultrathink README → lists PT in "Compatible with" + architecture table
- PERPLEXITY_BRIDGE.md → full integration doc with code examples

### 4. SKILL.md Routing Contract — Agreed

Both agree:
- PT SKILL.md = top-level model selection runs **first**
- ultrathink single_agent/SKILL.md = reasoning methodology, called **by** PT when deep reasoning needed
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

**ultrathink-system** `tests/` — 86+ tests, full CI coverage.

### 7. CI/CD — Both Repos Active

- PT `.github/workflows/ci.yml`: pytest + flake8 lint + routing.yml validation, Python 3.11/3.12 matrix
- ultrathink `.github/workflows/ci.yml` + `release.yml`: pytest + build + lint

## Resolved Gaps (History)

### GAP 1: `api_server.py` — ✅ RESOLVED (v0.9.5.0)

`api_server.py` created in ultrathink-system. Implements `POST /ultrathink` and `GET /health`. Now at v0.9.8.0 with rate limiting (slowapi), Pydantic V2 field_validator, input bounds, and null-byte sanitization.

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

**Implemented:** ultrathink `single_agent/SKILL.md` updated (commit `ac292db`) with hardware-aware routing section referencing PT `hardware/SKILL.md`. `orchestrator/__init__.py` also updated with `__version__` for package metadata consistency.

ultrathink-system's `single_agent/SKILL.md` should reference PT's hardware profiles so that when running inside PT orchestration, ultrathink knows to respect PT's hardware-aware routing.

**Suggested addition to ultrathink SKILL.md:**
```
When running inside Perplexity-Tools orchestration:
- Respect PT's model selection for top-level agents (see hardware/SKILL.md)
- Only override model choice when reasoning_depth = ultra
- Accept model_hint in request payload; use DEFAULT_MODEL as fallback
```

### OPT 2: `pyproject.toml` in PT

**Status:** ✅ RESOLVED (rolling — pre-v1.0 RC)

**Implemented:** `pyproject.toml` added to Perplexity-Tools root (commit `5082db6`). Includes `[project]` metadata, `[project.optional-dependencies]` for dev/test, and `[tool.pytest.ini_options]` config. PT is now pip-installable as `perplexity-tools`.

ultrathink-system is pip-installable. PT only has `requirements.txt`. Making PT installable enables consistent versioning and dependency pinning across the stack.

### OPT 3: Unified Integration Test

**Status:** ✅ RESOLVED (rolling — pre-v1.0 RC)

**Implemented:** `tests/test_ultrathink_integration.py` added to Perplexity-Tools (commit `c84a5f6`). 12 tests in `TestRoutingYmlUltrathinkContract` verifying `deep_reasoning` + `code_analysis` routes declare `ULTRATHINK_ENDPOINT`, `fallback=local_qwen30b`, and `requires=[ultrathink_available]`.

A single integration test that fires a task at PT and verifies it correctly routes to ultrathink:

```python
def test_deep_reasoning_routes_to_ultrathink():
    # POST to PT with privacy_critical=True
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
- ✅ `api_server.py` created in ultrathink-system
  - Implements `POST /ultrathink` and `GET /health`
  - Wire to 5-stage reasoning pipeline complete
  - Runs on port 8001 as specified
  - v0.9.8.0: rate limiting, Pydantic V2 validators, security hardening

**P1 — RESOLVED:**
- ✅ ultrathink-system `.env.example` updated with required API/model vars
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
- ultrathink-system API contract unchanged
- 4-layer architecture priority rule preserved
- ultrathink remains stateless; PT owns dedup via `.state/agents.json`

**Coordination Items (updated):**
- [x] PERPLEXITY_BRIDGE.md updated with Hardware Abstraction Layer section
- [x] ultrathink-system SKILL.md should reference hardware profiles from PT for optimal model selection
- [ ] Consider adding hardware profile awareness to ultrathink's model selection if it needs to make autonomous model choices

**Tests & CI (P2 items RESOLVED):**
- ✅ PT now has `tests/` with 6 test files (56+ tests)
- ✅ PT now has `.github/workflows/ci.yml`
- ✅ ultrathink-system maintains 86+ tests + CI

### Recommended Next Actions

1. ✅ **Cross-link SKILL.md files** — DONE: ultrathink SKILL.md now references PT `hardware/SKILL.md` for hardware-aware model selection
2. ✅ **Add integration test** — DONE: `tests/test_hardware_routing.py` (commit `82cb179`) verifies PT correctly routes deep reasoning tasks to ultrathink with hardware-appropriate models (mac-studio → MLX backend; win-rtx3080 → Ollama backend).
3. **Consider**: Should ultrathink-system be aware of hardware profiles, or should it remain fully hardware-agnostic?

---

**Generated:** 2026-03-28 | **Analyst:** Comet (Perplexity)
