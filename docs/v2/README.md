# oramasys v2 — Master Spec Index

**Date opened:** 2026-04-30
**Status:** Tentative — spec tree under brainstorming review
**Source of truth (raw):** `OpenClaw/v2/{1-Perplexity-Lang-Lang.md, 2-GPT-5.5-Thinking.md, 3-Gemini-3.1-PRO.md, 4-Grok.md}`

---

## Vision

A **secure, hardware-aware, local-first multi-agent LLM orchestration system** built clean-slate from primitives, with a small ruthless kernel and modules that orbit at their own pace.

Non-negotiable: **hardware affinity is a hard pre-spawn gate**. No framework that cannot enforce "refuse to dispatch if hardware unavailable" qualifies. This disqualifies LangGraph, CrewAI, AutoGen, and LangChain as direct adoptions — but their best ideas are borrowed into a slimmer custom engine.

Local-first + airgapped capable. Dependency-minimal. MIT-licensed (matches LangChain/LangGraph existing ecosystem).

---

## Locked decisions (D1–D10)

| # | Area | Decision |
|---|------|----------|
| **D1** | Relationship to v1 | Clean-slate rewrite alongside today's `orama-system` + `Perpetua-Tools`; v1 stays at v1.x and gets superseded only once v2 stable |
| **D2** | v2 repo names | `perpetua-core` + `oramasys` (lowercase, one-word; avoids public Orama Search collision) |
| **D3** | Sequencing | v1.0 RC ships first (close 2026-04-28 revamp); v2 starts after; v1.1/v1.2 roadmap re-evaluated post-v2.0 |
| **D4** | Architecture model | Microkernel — small ruthless kernel + plug-in modules at own pace |
| **D5** | Plugin API | Internal in v2.0, public versioned API in v2.1 |
| **D6** | Spec layout | Master + per-module sub-specs under `orama-system/docs/v2/` |
| **D7** | Schema lib | Pydantic v2 in kernel (already in stack); Pydantic AI logged as v2.1+ research item, *as a framework comparison*, not schema swap |
| **D8** | Kernel tier | **Revised 2026-04-30: 70-line kernel + `graph/plugins/`** — engine.py stays ~70 lines; checkpointer/interrupts/subgraphs/tool/streaming/structured_output ship as on-demand plugins (see `01-kernel-spec.md`) |
| **D9** | Build approach | GPT Phase 1–4 order (primitives → graph → HTTP → parity tests); lift proven pieces from v1 |
| **D10** | License | MIT (matches LangChain + LangGraph) |

Full rationale and the Perplexity/GPT/Gemini/Grok evidence behind each decision is in [`00-context-and-decisions.md`](./00-context-and-decisions.md).

---

## Sequencing

```
NOW (May 2026)        →   next           →   ?              →   ?
─────────────────         ──────────         ──────────         ──────────
v1.0 RC closed ✅         v2.0 parity        v2.1 public        v2.5 safety
v2.0 kernel done ✅       tests (Phase 4)    Plugin API         (MAESTRO + SWARM
(perpetua-core +          wire LLMClient     promotion          overlays + non-kernel
oramasys + agate,         to dispatch_node,  (semver,           self-improve
36 tests green)           non-kernel mods    OpenAPI)           evaluator)
                          orbit at own pace
```

Calendar-free. Each phase gates on completion criteria, not dates.

---

## Architecture model — microkernel

```
                 ┌─────────────────────────────────────┐
                 │      oramasys (orchestration)       │
                 │   • graph DSL composition           │
                 │   • FastAPI glass-window surface    │
                 │   • app-level node implementations  │
                 └────────────────┬────────────────────┘
                                  │  (one-way import only)
                                  ▼
                 ┌─────────────────────────────────────┐
                 │      perpetua-core (kernel)         │
                 │   • PerpetuaState                   │
                 │   • LLMClient (OpenAI-compat)       │
                 │   • HardwarePolicyResolver          │
                 │   • MiniGraph engine (70-line)      │
                 │   • GossipBus (SQLite event log)    │
                 └─────────────────────────────────────┘
                              ▲           ▲
                              │           │
                ┌─────────────┴──┐    ┌──┴──────────────┐
                │ non-kernel mod │    │ non-kernel mod  │
                │ (multi-agent)  │    │ (MCP-Optional)  │
                └────────────────┘    └─────────────────┘
                             ... ship at own pace ...
```

**One-way import boundary**: `oramasys` imports `perpetua_core`. Never reverse. CI lints enforce this.

---

## Repo topology

| Repo | Purpose | Imports |
|------|---------|---------|
| `perpetua-core/` | Data + state + LLM + hardware policy + gossip + graph engine | (no internal upward deps) |
| `oramasys/` | Graph DSL composition + FastAPI surface + app nodes | imports `perpetua_core` only |

**Rule**: any time you find yourself wanting `perpetua-core` to import `oramasys`, you have a layering bug.

---

## What v2.0 is **NOT** (anti-scope)

Explicit list of things deferred to non-kernel modules or later versions. Don't sneak these into the kernel.

- ❌ RAG / vector DB / semantic memory (deferred — see `02-modules/rag-and-memory.md`)
- ❌ Multi-agent swarm parallelism (deferred — see `02-modules/multi-agent-network.md`)
- ❌ Self-improving evaluator / proposal / mutation engines (deferred to v2.5 consideration — see `02-modules/self-improve-evaluator.md`)
- ❌ MAESTRO 7-layer enforcement (kernel-aware, but enforcement layer is v2.5 — see `03-safety-v2.5.md`)
- ❌ SWARM misalignment guardrails (v2.5 — see `03-safety-v2.5.md`)
- ❌ Public versioned Plugin API (v2.1 — see `02-modules/plugin-api-public.md`)
- ❌ Lessons / SKILL.md authoring tooling (deferred — see `02-modules/lessons-and-skill-authoring.md`)
- ❌ Redis distributed coordination (deferred — see `02-modules/redis-coordination.md`)
- ❌ MCP-Optional transport (deferred — see `02-modules/mcp-optional-transport.md`)

---

## Module roadmap

| Module | Source | Target version | Blocking? | Status |
|--------|--------|----------------|-----------|--------|
| Kernel | this spec | v2.0 | **YES** | **DONE** v2.0-alpha.1 (36 tests ✅, 2026-05-02) |
| Multi-agent network | v1 carry-over | v2.0+ (parallel) | no | stub |
| MCP-Optional transport | ex-v1.1 roadmap | v2.0+ | no | stub |
| Redis coordination | ex-v1.1 roadmap | v2.0+ | no | stub |
| Self-improve evaluator | ex-v1.2 roadmap | considered v2.5 | no | stub |
| RAG / memory | new | v2.0+ | no | stub |
| Lessons + SKILL.md | v1 carry-over | v2.0+ | no | stub |
| Plugin API (public) | v2.1 promotion of internal | v2.1 | no | stub |
| MAESTRO + SWARM safety | new | v2.5 | no | stub |

---

## Spec tree

```
orama-system/docs/v2/
├── README.md                          ← you are here
├── 00-context-and-decisions.md
├── 01-kernel-spec.md                  ← the only v2.0 blocking spec
├── 02-modules/
│   ├── README.md
│   ├── multi-agent-network.md
│   ├── mcp-optional-transport.md
│   ├── redis-coordination.md
│   ├── self-improve-evaluator.md
│   ├── rag-and-memory.md
│   ├── lessons-and-skill-authoring.md
│   └── plugin-api-public.md
├── 03-safety-v2.5.md
├── 04-build-order.md
├── 05-feasibility-review.md
├── 06-open-questions.md
├── 07-agate-vision.md
├── 08-technical-architecture-review.md
├── 09-comparative-analysis-and-merging-plan.md
├── 10-v1-hacks-automation-orbit.md
└── 11-idempotency-and-guard-patterns.md
```

---

## Open questions (live)

Tracked in [`06-open-questions.md`](./06-open-questions.md). Highlights:

- Pydantic AI evaluation (as a framework competitor) at v2.1+ checkpoint
- LM Studio LAN endpoint canonicalization (Mac `.110:1234`, Windows `.108:1234` per user memory; `routing.json` already verified `distributed=true`)
- GGUF spec extension RFC (community-pending since Oct 2024) for `system_requirements` metadata
- Naming: hardware policy spec → publish as `agate` (Perplexity proposal) when stable
