# Sync Analysis: ultrathink-system ↔ Perplexity-Tools

**Date:** 2026-03-28 | **Version:** Both at v0.9.6.0
---

## TL;DR — Status Summary

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Version** | ✅ IN SYNC | Both at v0.9.6.0 |
| **Architecture contract** | ✅ IN SYNC | 4-layer hierarchy documented + upheld |
| **Bridge doc** | ✅ IN SYNC | PERPLEXITY_BRIDGE.md aligned to v0.9.6.0 |
| **API endpoint spec** | ✅ IN SYNC | `api_server.py` created; POST /ultrathink + GET /health implemented || **Routing logic in PT** | ⚠️ PARTIAL | PT README shows routing; no actual `routing.yml` reference to ultrathink |
| **Idempotency contract** | ✅ RESOLVED | PT owns all state via `.state/agents.json`; ultrathink is stateless (no Redis). Redis deferred to PT v1.1+ |
| **Shared `.env` contract** | ⚠️ PARTIAL | Vars defined in BRIDGE doc; not in `.env` files of either repo |
| **SKILL.md cross-ref** | ✅ IN SYNC | PT SKILL.md references ultrathink routing methodology |
| **ECC Tools integration** | ✅ IN SYNC | Both agree on ECC as Stage-4 sub-agent selector |
| **autoresearch integration** | ✅ IN SYNC | Both reference karpathy/autoresearch equally |
| **Cross-repo README links** | ✅ IN SYNC | PT README links to ultrathink-system; ultrathink README lists PT |
| **CI/CD** | ⚠️ ASYMMETRIC | ultrathink has CI; PT has no `.github/workflows` visible |
| **Tests** | ⚠️ ASYMMETRIC | ultrathink has 86+ tests + pytest; PT has requirements but no test dir visible |

---

## What IS Working (Synergized Well)

### 1. Architecture Hierarchy — Correct and Consistent
Both repos agree on the 4-layer stack:
```
Perplexity-Tools  ← top-level orchestrator, model selection, fallback chain
ultrathink-system ← reasoning engine, 5-stage methodology, CIDF
ECC Tools         ← Stage-4 parallel sub-agent auto-selection (up to 5x)
autoresearch      ← research automation, idempotent sync
```
Priority rule is identical in both READMEs. No conflict.

### 2. Version Parity — Both at v0.9.6.0
Aligned same day (2026-03-26). Releases match.

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
PT receives task
  → deep reasoning? → call ultrathink:8001
    → timeout? → local Qwen3:30b on Dell
  → realtime/finance? → Perplexity Grok 4.1
  → simple Q&A? → local Qwen3:8b
```

---

## Gaps Found — What Needs Work

### GAP 1: `api_server.py` Missing from ultrathink-system
**Severity:** HIGH — blocks real integration

The PERPLEXITY_BRIDGE.md documents a `POST /ultrathink` endpoint:
```
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001
```
But `api_server.py` does **not exist** in the ultrathink-system repo.
The bridge doc references it as if live; it is currently aspirational.

**Fix needed:**
- Create `ultrathink-system/api_server.py` (FastAPI)
- Wire to ultrathink 5-stage reasoning pipeline
- Expose `POST /ultrathink` + `GET /health`

### GAP 2: PT `routing.yml` Does Not Reference ultrathink
**Severity:** MEDIUM

PT's `config/routing.yml` controls `task_type → role → model` chain.
It currently selects from local/cloud models, but has **no explicit ultrathink routing rule**.
The BRIDGE doc shows routing logic in Python code (not in YAML).

**Fix needed in `config/routing.yml`:**
```yaml
routes:
  deep_reasoning:
    requires: [ultrathink_available]
    endpoint: "${ULTRATHINK_ENDPOINT}"
    fallback: local_qwen30b
  code_analysis:
    requires: [ultrathink_available]
    endpoint: "${ULTRATHINK_ENDPOINT}"
    model: qwen3-coder:14b
    fallback: local_qwen30b
```

### GAP 3: `.env` Contract Not Persisted in Repos
**Severity:** MEDIUM

The BRIDGE doc specifies these env vars — but neither `.env.example` file contains them:

**ultrathink-system `.env.example` is missing:**
```
API_PORT=8001
API_HOST=0.0.0.0
DEFAULT_MODEL=qwen3:30b-a3b-instruct-q4_K_M
FAST_MODEL=qwen3:8b-instruct
CODE_MODEL=qwen3-coder:14b
OLLAMA_MAC_ENDPOINT=http://192.168.1.100:11434
OLLAMA_WINDOWS_ENDPOINT=http://192.168.1.101:11434
```

**Perplexity-Tools `.env.example` is missing:**
```
ULTRATHINK_ENDPOINT=http://localhost:8001/ultrathink
ULTRATHINK_TIMEOUT=120
ULTRATHINK_ENABLED=true
```

### GAP 4: Idempotency — Redis vs `.state/agents.json`
**Severity:** LOW-MEDIUM

PT uses file-persisted `.state/agents.json` for top-level agent dedup.
The BRIDGE doc specifies Redis for ultrathink task caching.
Redis is **not installed/configured** in ultrathink-system.

**Options:**
1. Use file-based cache in ultrathink too (consistent with PT pattern)
2. Add optional Redis dependency with file fallback
3. Delegate dedup entirely to PT (ultrathink stays stateless)

**Recommended:** Option 3 — ultrathink stays stateless; PT checks `.state/agents.json` before calling ultrathink.

**Resolution (v0.9.7.0):** Architecture decision locked — ultrathink remains stateless with no Redis requirement. PT is the sole orchestration layer and owns agent instantiation, tracking, queueing, budget enforcement, and file-based runtime state. Redis-backed coordination is a future PT-only enhancement planned for multi-instance distributed deployments in v1.1+.

### GAP 5: PT Has No Tests
**Severity:** MEDIUM

ultrathink-system has 86+ tests, CI, pytest suite.
Perplexity-Tools has `requirements.txt` but no `tests/` directory.
This means the orchestrator — the most critical layer — has zero regression coverage.

**Fix needed:**
```
Perplexity-Tools/
  tests/
    test_agent_tracker.py
    test_model_registry.py
    test_connectivity.py
    test_cost_guard.py
    test_routing.py
```

### GAP 6: PT Has No CI/CD
**Severity:** MEDIUM

ultrathink-system has `.github/workflows/ci.yml` + `release.yml`.
Perplexity-Tools has no workflows visible. No automated lint, test, or release.

---

## Synergy Optimization Opportunities

### OPT 1: Shared CHANGELOG Pattern
ultrathink-system has a `CHANGELOG.md`. PT does not.
Both should track cross-repo changes together so integration regressions are traceable.

### OPT 2: Health-Check Startup Script
Create a single `check-stack.sh` in either repo:
```bash
#!/bin/bash
# Check full stack health
curl -sf http://localhost:8000/health && echo "PT: OK" || echo "PT: DOWN"
curl -sf http://localhost:8001/health && echo "UltraThink: OK" || echo "UltraThink: DOWN"
ollama list && echo "Ollama: OK" || echo "Ollama: DOWN"
```

### OPT 3: Unified Task Router Test
A single integration test that fires a task at PT and verifies it correctly routes to ultrathink:
```python
def test_deep_reasoning_routes_to_ultrathink():
    # POST to PT with privacy_critical=True
    # Assert ultrathink endpoint was called
    # Assert result structure matches BRIDGE spec
```

### OPT 4: `.agents/skills` Cross-Linking
ultrathink-system has `.agents/skills/ultrathink-system/`.
PT has `.agents/skills/Perplexity-Tools/`.
Neither skill bundle mentions the other explicitly in its trigger conditions.

Add to ultrathink's skill SKILL.md:
```
When running inside Perplexity-Tools orchestration:
  - Respect PT's model selection for top-level agents
  - Only override when reasoning_depth = ultra
```

### OPT 5: `pyproject.toml` in PT
ultrathink-system is pip-installable (`pyproject.toml` + wheel).
PT only has `requirements.txt`. Making PT installable enables:
- `pip install perplexity-tools` in CI
- Consistent versioning
- Dependency pinning across the stack

---

## Recommended Action Priority

| Priority | Action | Repo | Effort |
|----------|--------|------|--------|
| P0 | Create `api_server.py` (POST /ultrathink) | ultrathink-system | High |
| P1 | Add ultrathink env vars to `.env.example` | ultrathink-system | Low |
| P1 | Add ultrathink vars to PT `.env.example` | Perplexity-Tools | Low |
| P1 | Add ultrathink route to PT `config/routing.yml` | Perplexity-Tools | Medium |
| P2 | Create `tests/` in Perplexity-Tools | Perplexity-Tools | High |
| P2 | Add `.github/workflows/` to Perplexity-Tools | Perplexity-Tools | Medium |
| P2 | ~~Simplify Redis → stateless ultrathink + PT dedup~~ | ✅ DONE | Resolved in v0.9.7.0 — ultrathink stateless, PT owns all state |
| P3 | Add `CHANGELOG.md` to Perplexity-Tools | Perplexity-Tools | Low |
| P3 | Add `check-stack.sh` health script | Either | Low |
| P3 | Add `pyproject.toml` to Perplexity-Tools | Perplexity-Tools | Medium |
| P3 | Cross-link `.agents/skills` SKILL.md references | Both | Low |

---

## What NOT to Change

- **Do not merge the repos.** Independent configurability is a feature.
- **Do not make ultrathink stateful** with its own agent registry. PT owns that.
- **Do not add Perplexity API calls to ultrathink.** It stays local-only (privacy layer).
- **Do not change the priority rule.** PT SKILL.md → ECC → ultrathink ordering is correct.


---

## Update 2026-03-27: v0.9.5.0 Hardware Abstraction Layer [SYNC]

### Status: P0 & P1 Gaps RESOLVED ✅

All critical integration gaps from the previous analysis have been addressed:

**P0 — RESOLVED:**
- ✅ `api_server.py` created in ultrathink-system (commit 3a98311, 18h ago)
  - Implements `POST /ultrathink` and `GET /health`
  - Wire to 5-stage reasoning pipeline complete
  - Runs on port 8001 as specified

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

### Sync Impact

**No Breaking Changes:**
- ultrathink-system API contract unchanged
- 4-layer architecture priority rule preserved
- ultrathink remains stateless; PT owns dedup via `.state/agents.json`

**Coordination Needed (P2/Future):**
- [ ] ultrathink-system SKILL.md should reference hardware profiles from PT for optimal model selection
- [ ] PERPLEXITY_BRIDGE.md should be updated to include hardware abstraction layer examples
- [ ] Consider adding hardware profile awareness to ultrathink's model selection if it needs to make autonomous model choices

**Tests & CI (P2 items remain):**
- PT still has no `tests/` directory (GAP 5)
- PT still has no `.github/workflows/` (GAP 6)
- ultrathink-system maintains 86+ tests + CI

### Recommended Next Actions

1. **Update PERPLEXITY_BRIDGE.md** to reference `hardware/SKILL.md` and new model selection patterns
2. **Cross-link SKILL.md files** so ultrathink knows to respect PT's hardware-aware routing
3. **Add integration test** that verifies PT correctly routes deep reasoning tasks to ultrathink with hardware-appropriate models
4. **Consider**: Should ultrathink-system be aware of hardware profiles, or should it remain fully hardware-agnostic?

---

**Generated:** 2026-03-27 | **Analyst:** Comet (Perplexity)

---

*Generated: 2026-03-26 | Analyst: Comet (Perplexity)*
