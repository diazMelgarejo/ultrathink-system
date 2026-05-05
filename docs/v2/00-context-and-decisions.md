# 00 — Context and Decisions

This document captures **why v2 exists**, what each of the four source AI-conversations contributed, and the full rationale behind decisions D1–D10.

---

## Why v2 exists

The current `orama-system` (v0.9.9.8, approaching v1.0 RC) has matured into a working multi-agent system with a 5-stage methodology, 7 specialized agents, FastAPI HTTP bridge, MCP server stubs, and a LAN topology spanning Mac (LM Studio at `192.168.x.110:1234`) and Windows (LM Studio at `192.168.x.108:1234`) hosts. It works — but the architecture grew organically. State is scattered across `.env`, `openclaw.json`, hardcoded defaults; framework choices were never deliberate; and key safety primitives (hardware affinity gates, pre-spawn checks) are bolted on rather than baked in.

v2 is the chance to **rebuild from primitives** with hardware affinity, microkernel modularity, and local-first orchestration as first-class design constraints — informed by everything v1 taught us, while shedding the accidental complexity.

---

## The four source conversations (in sequence)

The user solicited input from four AI systems in order. Each built on the prior:

### 1. `1-Perplexity-Lang-Lang.md` — The strategic baseline (114 KB)

**What it proposes:**
- A two-stage roadmap: **v2.0** = MVP using **MAESTRO 7-layer threat modeling**; **v2.5** = **SWARM** (System-Wide Assessment of Risk in Multi-agent systems) misalignment guardrails.
- **Hardware affinity as a hard pre-spawn gate** — disqualifies LangGraph (Sept 2025 plan abandoned for this reason), CrewAI, AutoGen, and LangChain.
- A custom **70-line `MiniGraph` engine** with the LangGraph mental model but zero LangChain deps.
- **Pydantic AI Slim** for type-safe schemas (later corrected — Pydantic AI is a framework, not a schema lib; D7).
- SQLite + LangGraph-compatible checkpointers for durable session/routing persistence.
- **`model_hardware_policy.yml`** declaring PREFER/ALLOW/NEVER constraints — proposed as eventually publishable open standard (`agate`).
- "Scenario D" recommended first move: **expose Perpetua-Tools + orama-system as REST endpoints** so any framework can call them as local hardware routers.

**User profile**: advanced researcher/builder, citing Karpathy, SWARM framework, Anthropic agentic-misalignment research; long-term AGI-era planning horizon.

### 2. `2-GPT-5.5-Thinking.md` — The scope discipline (5 KB)

**What it adds:**
- **Ruthless v2.0 scope**: primitives + orchestration ONLY. No RAG, no vector DB, no memory, no swarm. (Adopted as kernel definition; non-kernel modules ship at own pace per D4.)
- **Two-repo split**: `perpetua-core` (state, llm, policy, gossip, tool, streaming) + `oramasys` (graph, api). One-way import boundary: `oramasys → perpetua-core`, never reverse.
- **FastAPI as a "glass window"** — handlers ≤ 10 lines: `req.to_state()` → `graph.ainvoke()` → `Response.from_state()`.
- **Phase 1–4 build order**: primitives → graph engine → HTTP surface → parity tests.
- **Rename** "orama-system" → `oramasys` to avoid public Orama Search collision (adopted; D2).
- Provides `perpetua_v2_clean_slate_scaffold.zip` starter file structure.

**Risks GPT flags:** scope creep (RAG, checkpointing, telemetry); accidental framework clone; weak package boundary.

### 3. `3-Gemini-3.1-PRO.md` — The starter code (6 KB)

**What it provides:**
- `perpetua/core/state.py` — `PerpetuaState` dataclass.
- `perpetua/core/llm.py` — `LLMClient` async wrapper around `openai.AsyncOpenAI`; defaults to local Ollama at `http://localhost:11434/v1`; env vars `LLM_BASE_URL`, `LLM_API_KEY`.
- `perpetua/config/model_hardware_policy.yml` — affinity routing config: OS constraints, VRAM limits, model quantization, fallback rules.
- Bash scaffolding script for the two-repo layout.
- File ends mid-section: "follow Perplexity example and adapt."

**Caveats:** Routing metadata + fallbacks "should be handled prior" via PolicyResolver (not shown). Error propagation explicit (`raise RuntimeError` to graph layer).

### 4. `4-Grok.md` — The synthesis (5 KB)

**Verdict:** "Clean, ready-to-use scaffolding, combining the best from both plans" — positive, actionable.

**Adds:**
- `nodes_visited`, `metadata["messages"]`, `retry_count` fields to `PerpetuaState`.
- Hardware tier enum: `mac` / `windows` / `shared`.
- Task-type taxonomy: coding / reasoning / research / ops.
- Optimization hints: speed / quality / reasoning.
- Mentions "recycle the husk" of today's `api_server.py` (scope unclear → D9: lift proven pieces).

**No critiques** of prior proposals — Grok positions as synthesizer.

---

## Locked decisions (with full rationale)

### D1 — Clean-slate rewrite alongside v1

The four files describe a v2 distinct enough that retrofitting today's `orama-system` would muddy both. We build new repos from scratch; v1 keeps shipping at v1.x; v2 supersedes only once stable.

### D2 — `perpetua-core` + `oramasys`

GPT recommends, Grok agrees. **`orama-system` → `oramasys`** avoids collision with the public Orama Search project on PyPI/npm. Lowercase, one-word, brand-fresh.

### D3 — v1.0 RC ships first, then v2

The in-flight `2026-04-28-perpetua-orama-master-revamp.md` (5 correctness fixes for v1.0 RC: CI blocker, model-ID hallucination, `HardwareAffinityError` re-export, HARDWARE_MISMATCH 400 tests, doc sync) closes first. Then v2 begins. The published v1.1 / v1.2 roadmaps get re-evaluated — features may roll into v2 instead of being delivered in v1.x.

### D4 — Microkernel architecture

Small ruthless kernel; everything else is plug-in modules/skills shipping at their own pace.

**Kernel (v2.0, blocking):**
- `PerpetuaState` (Pydantic v2 model)
- `LLMClient` (async, OpenAI-compatible)
- `HardwarePolicyResolver` + `model_hardware_policy.yml`
- `MiniGraph` engine (Tier 3 — see D8)
- `GossipBus` (SQLite event log)
- FastAPI "glass window" surface

**Non-kernel modules (ship at own pace):**
- 7-agent network (carry-over from v1)
- v1.1 features: MCP-Optional transport, Redis coordination
- v1.2 self-improve: evaluator, proposal, mutation engines (→ considered for v2.5)
- RAG / vector DB / memory beyond gossip
- Lessons + SKILL.md tooling
- MAESTRO + SWARM safety overlays (→ v2.5)

### D5 — Plugin API: internal v2.0, public v2.1

v2.0 FastAPI is consumed by `oramasys` only. v2.1 promotes it to a versioned public Plugin API (OpenAPI spec, semver) — Perplexity's "Scenario D" — letting external frameworks (LangGraph, CrewAI, AutoGen) call `perpetua-core` as their local hardware router.

### D6 — Master + per-module sub-specs

Single master doc + dedicated per-module files. Modules can evolve independently without master-doc bloat.

### D7 — Pydantic v2 in kernel

User-validated correction: **Pydantic AI is an agent framework, not a leaner Pydantic v2.** Adopting it in the kernel would partially undo D4 (we'd be importing someone else's `Agent`/`Tool`/`RunContext` runtime instead of MiniGraph). Pydantic v2 is already in stack via FastAPI; mature, fast (Rust core), zero new deps. Pydantic AI is logged in `06-open-questions.md` for v2.1+ evaluation **as a framework competitor**.

### D8 — Tier 3 kernel (~220 lines)

User chose Tier 3 over Tier 1 (~80 lines) and Tier 2 (~150 lines). Borrowed features:
- Conditional edges + state reducers (LangGraph)
- SQLite checkpointer for resumability (LangGraph; reuses GossipBus's SQLite)
- HITL interrupts / pause points (LangGraph; pairs with checkpointer; required by MAESTRO)
- Subgraphs for module composition (LangGraph; critical for microkernel modularity)
- ToolNode contract for subprocess CLIs (Claude Code / Codex / shell)
- Streaming (token + state, `AsyncGenerator`)
- `@tool` decorator with auto-schema from type hints (Pydantic AI Slim ergonomics, built on plain Pydantic v2)
- Structured output validation (force LLM responses into Pydantic v2 shapes; retry on parse failure)

Tradeoff: kernel grows ~3x beyond Perplexity's original 70-line target, but ships substantial UX out of the box. Documented as explicit departure from "ruthless" cut.

### D9 — GPT Phase 1–4 order; lift proven pieces

Sequence: primitives → graph engine → HTTP surface → parity tests. Lift battle-tested code from v1: FastAPI surface skeleton from `api_server.py`, `HardwareAffinityError` exception class (already canonicalized in 2026-04-28 revamp), `model_hardware_policy.yml` schema, LM Studio routing config from `routing.json`.

### D10 — MIT License

Both `langchain-ai/langchain` and `langchain-ai/langgraph` ship MIT. Matching them: maximum permissive, ecosystem alignment, friction-free adoption. `perpetua-core` PyPI release becomes possible once stable; hardware policy spec can become open standard in v2.1+.

---

## Confirmed not-decisions (parked, not punted)

- **Pydantic AI** as kernel schema lib — rejected per D7 (category error). Kept in `06-open-questions.md` as v2.1+ framework-comparison item.
- **Adopting LangGraph wholesale** — rejected per D4/D8 (cannot enforce hardware affinity pre-spawn). LangGraph mental model + best ideas borrowed instead.
- **Open-standard publishing of `model_hardware_policy.yml`** (Perplexity's "Scenario B") — held off until spec stabilizes; revisit at v2.1+.
- **Smolagents fork** (Perplexity's "Scenario C") — declined; only relevant if pursuing a named OSS project identity, which we are now via `perpetua-core` directly.
