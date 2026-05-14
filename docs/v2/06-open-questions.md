# 06 — Open Questions

Items deliberately deferred. Each has a target checkpoint for resolution.

---

## Active open questions

| # | Question | Context | Resolve by |
|---|----------|---------|------------|
| OQ1 | **Pydantic AI as framework** — at v2.1+, evaluate whether `pydantic-ai` (`Agent`, `Tool`, `RunContext`) should supplement or replace `MiniGraph` for the application layer (not kernel). | Pydantic AI is a framework built on Pydantic v2. It's a LangGraph competitor. MiniGraph is our custom engine. The question is whether v2.1's app layer uses one, both, or neither. | v2.1 checkpoint |
| OQ2 | **GGUF hardware spec extension** — a community RFC to add `system_requirements` to the GGUF metadata layer has been pending since Oct 2024 with no timeline. Do we wait for it, or does `agate` serve as the bridge (mapping GGUF model IDs to hardware policy)? | The GGUF format is the de facto standard for local model metadata. Adding hardware requirements to GGUF would let any GGUF loader natively enforce hardware affinity without a separate policy file. | agate v0.1 release |
| OQ3 | **`agate` naming** — Perplexity proposed "agate" as the name for the published hardware policy spec (memorable vs. `model-hardware-policy-spec`). The repo is confirmed as `oramasys/agate`. Should the Python package also be `agate` on PyPI? Check availability. | Name availability determines distribution strategy. | agate repo setup |
| OQ5 | **Agent identity attestation (MAESTRO Layer 3)** — v2.5 MAESTRO Layer 3 requires agents to attest their identity per dispatch. Options: (a) cryptographic signing per agent process (secure, complex); (b) per-session UUID cached in state (simple, spoofable); (c) `metadata["agent_id"]` in PerpetuaState (already there, honor-system). | Cryptographic attestation may be overkill for a LAN-local system. Honor-system agent IDs may be sufficient until the system is exposed externally. | v2.5 safety planning |
| OQ6 | **Perpetua-Tools repository** — the 2026-04-28 revamp plan (Tasks 0 and 1) requires changes to `Perpetua-Tools` repo (CI blocker fix + Perplexity-Tools → Perpetua-Tools typo). PT is not available locally. Location: `github.com/diazMelgarejo/Perpetua-Tools`. | Need to `gh repo clone diazMelgarejo/Perpetua-Tools` to continue Tasks 0 and 1. | v1.0 RC (immediate) |
| OQ9 | **`quickstart.py` scope** — DX assessment flags TTHW ≤ 10 min as a target. `quickstart.py` should demonstrate: (a) 3-node graph, (b) hardware routing, (c) HITL pause + resume. Does it live in `perpetua-core/` or `oramasys/`? | Quickstart should live in `oramasys/` (it uses both repos). Ideally runnable with `uvicorn oramasys.orama.api.server:app --reload` + a separate `curl` or Python client. | v2.0 Phase 3 |

---

## Resolved (logged for posterity)

| # | Question | Resolution | Date |
|---|----------|------------|------|
| D1 | Clean-slate vs. evolve-in-place | Clean-slate rewrite | 2026-04-30 |
| D2 | Repo names | `perpetua-core` + `oramasys` | 2026-04-30 |
| D3 | v2 sequencing | v1.0 RC first | 2026-04-30 |
| D4 | Architecture model | Microkernel | 2026-04-30 |
| D5 | Plugin API | Internal v2.0, public v2.1 | 2026-04-30 |
| D6 | Spec layout | Master + per-module | 2026-04-30 |
| D7 | Schema lib | Pydantic v2 (Pydantic AI = framework, not schema lib) | 2026-04-30 |
| D8 | Kernel tier | **Revised 2026-04-30**: ~70-line pure kernel + `graph/plugins/`. Canonical implementation: `oramasys/perpetua-core` commit `2f717f5`, 65-line engine + 6 plugins, 32 tests | 2026-04-30 / impl 2026-05-01 |
| D9 | Build approach | GPT Phase 1-4, lift proven pieces | 2026-04-30 |
| D10 | License | MIT | 2026-04-30 |
| D11 | 3rd new repo | `oramasys/agate` (Hardware Policy Specification) | 2026-05-01 |
| D12 | GitHub org | Real GitHub org `oramasys` (user to create at github.com/organizations/new) | 2026-05-01 |
| D13 | TDD policy | Enshrined in `docs/v2/README.md` and `04-build-order.md`. tdd.md is the source of truth. | 2026-05-01 |
| OQ10 | **Capability-Based Routing** — Should the `model_hardware_policy.yml` move from model-ID mapping to hardware capability rules (e.g. `VRAM >= 12GB`)? | Current static mapping requires manual YAML updates for every new model version. Rule-based routing would be more adaptive. | v2.2 planning |
| OQ11 | GossipBus async | **Resolved:** `aiosqlite` used from day one in `oramasys/perpetua-core` — no sync SQLite; background writer concern resolved by async-native design | 2026-05-01 |
| OQ4 | GitHub org `oramasys` creation | Org created; all 3 v2 repos live at `github.com/oramasys/*` | 2026-05-01 |
| OQ7 | Python version for new repos | Python 3.11+ from day one; `requires-python = ">=3.11"` in all 3 `pyproject.toml` files | 2026-05-01 |
| OQ8 | `optimize_for` field name | `optimize_for: OptHint = "quality"` IS on `PerpetuaState` in canonical (matches Grok synthesis + policy routing key structure) | 2026-05-01 |
| (OQ13) | PerpetuaState dataclass vs BaseModel | `BaseModel` with `ConfigDict` in canonical; `scratchpad: dict[str,Any]` | 2026-05-01 |
| (OQ14) | `perpetua-core` org transfer | Canonical was always under `oramasys` org; no transfer needed | 2026-05-01 |
| (OQ16) | Engine integration vs. plugins | 65-line pure engine + `graph/plugins/` is canonical; D8 revision implemented | 2026-05-01 |
| OQ12 | **Kernel recursion limit** — Should `MiniGraph.ainvoke` enforce a `max_steps` safety guard? | Prevents infinite loops in malformed graphs. Aligns with MAESTRO Layer 2 safety. | Phase 2 implementation |
