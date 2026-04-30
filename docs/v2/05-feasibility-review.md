# 05 — Feasibility Review

> Expanded with `/autoplan` CEO × Eng × DX lens applied to each suggestion from the 4 source files.
> Methodology: 6 decision principles (completeness, boil-lakes, pragmatic, DRY, explicit-over-clever, bias-toward-action).

---

## Dual-Voice Verdict Summary (pre-build)

| Voice | Verdict | Top risk |
|-------|---------|----------|
| **CEO / Strategic** | ✅ Sound premise. Hardware affinity is a genuine gap no framework solves. | Scope creep: MiniGraph could balloon to LangGraph parity if not guarded |
| **Eng / Architecture** | ✅ Two-repo split + one-way import is the right structure. Tier 3 kernel is justified. | Streaming + HITL together add ~60 lines of async complexity to the kernel |
| **DX / Developer** | ✅ FastAPI glass-window + @tool decorator make the surface ergonomic. | TTHW (time-to-hello-world) is still ≥30 min without a proper `quickstart.py` |

Cross-phase theme: **all three voices independently flag that the `model_hardware_policy.yml` schema needs a machine-readable JSON Schema companion** to be useful to external consumers (agate's job).

---

## Feasibility Matrix — Perplexity suggestions

| # | Suggestion | Target | Feasibility | Risk | Decision | Principle |
|---|-----------|--------|-------------|------|----------|-----------|
| P1 | MAESTRO 7-layer threat modeling | v2.5 | ✅ High | Medium — 7 layers means 7 subgraphs; scope balloons if rushed | Approved for v2.5; kernel hooks (HITL, GossipBus) land in v2.0 | P6 (bias-to-action: don't block on safety theater) |
| P2 | SWARM misalignment guardrails | v2.5 | ✅ High | Medium — needs real multi-agent traffic to tune thresholds | Approved for v2.5; no v2.0 impact | P6 |
| P3 | `MiniGraph` engine (70-line target) | v2.0 kernel | ✅ High | Low — GPT scaffold already has 40-line engine; Tier 3 adds ~180 lines | Approved. Tier 3 chosen explicitly (D8). Document line budget. | P3 (pragmatic) |
| P4 | `model_hardware_policy.yml` as open standard | agate (v2.1+) | ✅ High | Low — YAML spec + JSON Schema; no runtime complexity | Approved for `agate` repo. v2.0 ships internal copy; agate publishes spec. | P5 (explicit over clever) |
| P5 | Scenario D: expose as REST Plugin API for other frameworks | v2.1 | ✅ High | Low — existing FastAPI surface, just needs versioning + OpenAPI | Approved for v2.1 (D5). Internal-only in v2.0. | P6 |
| P6 | Pydantic AI Slim for type safety | ❌ Rejected (D7) | N/A | High — Pydantic AI is a framework, not a schema lib; conflicts with MiniGraph | Pydantic v2 in kernel instead. Pydantic AI logged as v2.1+ framework research. | P4 (DRY — we already have Pydantic v2) |
| P7 | SQLite + LangGraph checkpointers | v2.0 kernel | ✅ High | Low — `aiosqlite` is 1 dep, lightweight | Approved. Custom `SqliteCheckpointer` (not LangGraph's) — same interface. | P5 |
| P8 | Hardware affinity as hard pre-spawn gate | v2.0 kernel | ✅ High — this is THE non-negotiable | Low | Approved. Already in `HardwarePolicyResolver` (D4 kernel). | P1 |
| P9 | Gossip pub/sub event log | v2.0 kernel | ✅ High | Low — reuses same SQLite db as checkpointer | Approved. `GossipBus` in kernel. | P1 |
| P10 | Publish `model_hardware_policy.yml` as `agate` (naming) | agate | ✅ High | Low — just a name + spec repo | Approved. `oramasys/agate` is the 3rd new repo (user confirmed). | P5 |
| P11 | Subprocess tool node (Claude Code / Codex as ToolNode) | v2.0 kernel | ✅ High | Low — async subprocess, 20 lines | Approved. `ToolNode` contract in `graph/nodes.py`. | P1 |

---

## Feasibility Matrix — GPT suggestions

| # | Suggestion | Target | Feasibility | Risk | Decision | Principle |
|---|-----------|--------|-------------|------|----------|-----------|
| G1 | Two-repo split: `perpetua-core` + `oramasys` | v2.0 | ✅ High | Low — well-established pattern (cf. FastAPI + Starlette) | Approved (D2). | P5 (explicit: clear boundary) |
| G2 | One-way import boundary CI lint | v2.0 | ✅ High | Low — one grep in CI | Approved. Add to `oramasys/.github/workflows/lint.yml`. | P1 |
| G3 | FastAPI handlers ≤ 10 lines | v2.0 | ✅ High | Low — disciplinary constraint, not technical | Approved (D4). Lint it: `len(source_lines) > 10 → CI fail`. | P5 |
| G4 | Phase 1→4 build order | v2.0 | ✅ High | Low — well-reasoned progression | Approved (D9). Documented in `04-build-order.md`. | P3 |
| G5 | Rename to `oramasys` (avoid Orama Search collision) | v2.0 | ✅ High | Low | Approved (D2). GitHub org = `oramasys`. | P5 |
| G6 | No RAG / no memory in v2.0 MVP | v2.0 | ✅ High | Low | Approved (D4 anti-scope). | P3 (YAGNI) |
| G7 | FastAPI as "glass window" pattern | v2.0 | ✅ High | Low | Approved. `req.to_state() → graph.ainvoke() → Response.from_state()` | P5 |
| G8 | Version pinning across repos | v2.0 | ✅ High | Medium — can drift if not enforced | Approved. `perpetua-core` publishes semver; `oramasys/pyproject.toml` pins exact version. | P1 |

---

## Feasibility Matrix — Gemini code samples

| # | Suggestion | Target | Feasibility | Risk | Decision | Principle |
|---|-----------|--------|-------------|------|----------|-----------|
| E1 | `PerpetuaState` as frozen dataclass | v2.0 | ⚠️ Medium | Medium — Gemini used stdlib dataclasses; we chose Pydantic v2 (D7). Pydantic v2 gives validation + JSON schema. **Not a conflict, an upgrade.** | Use Pydantic v2 `BaseModel` instead of stdlib `@dataclass`. Gemini's field names preserved. | P1 (Pydantic v2 = more complete) |
| E2 | `LLMClient` async `AsyncOpenAI` wrapper | v2.0 | ✅ High | Low — GPT scaffold uses `httpx` directly (lighter dep). Slight divergence. | Use `httpx.AsyncClient` (GPT scaffold) over `openai.AsyncOpenAI`. Avoids `openai` SDK dep in kernel — stays truly dependency-minimal. | P4 (DRY — already in venv) + P3 |
| E3 | `model_hardware_policy.yml` YAML schema | v2.0 + agate | ✅ High | Low | Adopt GPT scaffold's schema shape (models → provider/hardware_tier/context/roles; routing dict). Cleaner than Gemini's draft. | P5 |
| E4 | Bash scaffolding script | v2.0 | ✅ High | Low | GPT scaffold (`perpetua_v2_clean_slate_scaffold.zip`) is already available — replaces Gemini's partial script. | P6 (bias-to-action: use what exists) |
| E5 | Error propagation via `raise RuntimeError` to graph layer | v2.0 | ✅ High | Low | Adopt pattern. `HardwareAffinityError(RuntimeError)` already established in v1. | P5 |

---

## Feasibility Matrix — Grok additions

| # | Suggestion | Target | Feasibility | Risk | Decision | Principle |
|---|-----------|--------|-------------|------|----------|-----------|
| R1 | Add `nodes_visited`, `metadata`, `retry_count` to state | v2.0 | ✅ High | Low | Approved (D8). All 3 fields in `PerpetuaState`. | P1 |
| R2 | Hardware tier enum: mac / windows / shared | v2.0 | ✅ High | Low — GPT scaffold uses `provider` + `hardware_tier` separately, which is richer | Approved. Keep both: `provider` (routing) and `hardware_tier` (affinity check). | P5 |
| R3 | Task-type taxonomy: coding / reasoning / research / ops | v2.0 | ✅ High | Low | Approved. In `PerpetuaState.task_type` + `model_hardware_policy.yml` routing keys. | P1 |
| R4 | Optimization hints: speed / quality / reasoning | v2.0 | ✅ High | Low — `optimize_for` field in GPT scaffold already covers this | Approved. Use `optimize_for` (GPT scaffold name) rather than `opt_hint` to match scaffold. | P4 (DRY) |
| R5 | "Recycle the husk" of api_server.py | v2.0 | ✅ High | Low | Approved (D9). FastAPI skeleton lifted from v1's `api_server.py`. | P6 |
| R6 | Task taxonomy in routing keys (coding:default, etc.) | v2.0 | ✅ High | Low — already in GPT scaffold's `model_hardware_policy.yml` | Approved. | P4 |

---

## CEO Strategic Assessment (autoplan Phase 1 voice)

### Premise validation

| Premise | Status | Evidence |
|---------|--------|----------|
| "No framework enforces hardware affinity as a pre-spawn gate" | ✅ CONFIRMED | LangGraph Sept 2025 attempt abandoned for this reason; CrewAI/AutoGen both assume cloud |
| "A 70-line MiniGraph is sufficient for the kernel" | ⚠️ REVISED | Tier 3 kernel is ~220 lines (D8) — still small but GPT's 70-line target was too conservative for the feature set chosen |
| "Pydantic AI Slim is a leaner schema lib" | ❌ FALSE | Corrected: Pydantic AI is a framework, not a schema lib. Resolved in D7. |
| "GPT's scaffold is the right starting point" | ✅ CONFIRMED | `perpetua_v2_clean_slate_scaffold.zip` present at `OpenClaw/` — usable immediately |
| "MIT license matches the ecosystem" | ✅ CONFIRMED | LangChain/LangGraph both MIT. |

### Dream state delta

```
TODAY (v1.0 RC)           → v2.0 KERNEL              → 12-MONTH IDEAL (v2.5+)
─────────────────            ──────────────────          ─────────────────────────
• Organic architecture       • perpetua-core +           • MAESTRO enforcement active
• HardwareAffinityError        oramasys clean-slate      • SWARM risk monitor live
  in 2 places               • MiniGraph Tier 3           • agate spec published as
• Volatile .json state       • GossipBus audit log         open standard
• No resumability            • SQLite checkpointer        • Other frameworks (LangGraph,
• No HITL                   • HITL interrupts               CrewAI) use perpetua-core
• v1.1/v1.2 roadmap         • @tool decorator              as hardware router via REST
  in limbo                  • Streaming                  • Community RFC on GGUF
                            • agate spec v0.1               hardware metadata
```

### NOT in scope for v2.0

- MAESTRO enforcement subgraphs
- SWARM risk monitor
- Redis distributed coordination
- Multi-agent 7-agent network (in non-kernel module)
- RAG / vector DB
- Self-improve evaluator
- Public Plugin API (v2.1)
- agate community RFC (v2.1+)

---

## Eng Assessment (autoplan Phase 3 voice)

### Architecture dependency graph

```
oramasys/orama/api/server.py
    ↓ imports
oramasys/orama/graph/runner.py
    ↓ imports
oramasys/orama/graph/engine.py  ← perpetua_core.graph.engine (MiniGraph)
    ↓ imports
perpetua_core/state.py           ← PerpetuaState (Pydantic v2)
perpetua_core/llm.py             ← LLMClient (httpx)
perpetua_core/policy.py          ← HardwarePolicyResolver + HardwareAffinityError
perpetua_core/gossip.py          ← GossipBus (aiosqlite)
perpetua_core/graph/checkpointer.py ← SqliteCheckpointer (aiosqlite, same db)
perpetua_core/graph/interrupts.py   ← Interrupt exception
perpetua_core/graph/tool.py         ← @tool decorator (Pydantic v2)
perpetua_core/graph/streaming.py    ← AsyncGenerator

ONE-WAY BOUNDARY: oramasys → perpetua_core (enforced by CI lint)
```

### Edge cases that need test coverage (TDD-first per policy)

| Edge case | Test type | Priority |
|-----------|-----------|----------|
| `HardwareAffinityError` on NEVER tier | Unit (policy.py) | CRITICAL |
| Graph interrupted mid-run → checkpoint saved → aresume succeeds | Integration | HIGH |
| `@tool` decorator on function with no return annotation → clear error | Unit | HIGH |
| `LLMClient` timeout → `httpx.TimeoutException` propagated cleanly | Unit (mock) | HIGH |
| `GossipBus.emit()` on locked SQLite (concurrent writes) | Unit | MEDIUM |
| `PerpetuaState.merge()` with unknown field → Pydantic v2 strict mode | Unit | MEDIUM |
| `oramasys` imports `perpetua_core` but reverse never true → CI lint | Integration | HIGH |
| Mac LM Studio at `.110:1234` + Windows-only model hint → 400 HARDWARE_MISMATCH | E2E | HIGH |
| `streaming.astream()` yields events in node order | Unit | MEDIUM |

---

## DX Assessment (autoplan Phase 3.5 voice)

### Developer journey map

| Stage | Current v1.0 | Target v2.0 | Gap |
|-------|-------------|-------------|-----|
| Install | `pip install` from local | `pip install perpetua-core oramasys` | pyproject.toml must have correct entry points |
| Config | Env vars + openclaw.json | `model_hardware_policy.yml` (one file) | Schema validation at startup (not silent failure) |
| First run | POST /ultrathink (FastAPI) | `python quickstart.py` | Need a `quickstart.py` with 3-node example |
| Error | Silent model failure | `HardwareAffinityError` with clear message | Error message: model + tier + reason + fix suggestion |
| Debug | Check logs manually | `GossipBus` queryable audit | Add `oramasys debug session <session_id>` CLI command |

**TTHW (time-to-hello-world) target: ≤ 10 minutes** from `git clone` to first successful graph run.

### Critical DX gaps to address in v2.0

1. **`quickstart.py`** — a 30-line example that runs a 3-node graph, shows routing, HITL pause, and resumes. Ship with `perpetua-core`.
2. **Startup schema validation** — `model_hardware_policy.yml` must be validated at server start; bad config = clear error message with fix hint.
3. **`HardwareAffinityError` message quality** — format: "Model `{model}` is `NEVER` on `{tier}`. Available tiers: {allowed}. Set `model_hint` to a {allowed[0]}-compatible model."
4. **JSON Schema companion for agate** — developers integrating perpetua-core need a schema to validate their policy files. `agate/schema/model_hardware_policy.schema.json`.

---

## Autoplan final verdicts

**Auto-decided (applying 6 principles):** All 27 suggestions above are classified.
**Taste decisions:** E2 (httpx vs openai SDK — both viable; httpx chosen for lighter deps).
**User challenges:** None — no suggestions conflict with stated user direction.
**Key insight (Eureka):** The `agate` repo is not just documentation — it IS the hardware affinity standard that makes perpetua-core interoperable. Its JSON Schema becomes the contract that lets any Python, Rust, or Go agent system participate in the same hardware routing ecosystem. This is a bigger deal than "Scenario B" framing suggested.
