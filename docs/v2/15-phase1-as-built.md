# 15 — Phase 1 As-Built Notes (2026-05-14)

> Records the delta between the v2.0 kernel spec and what actually shipped.
> Purpose: track deferred reconciliation items without losing them.
> Status: **planning doc** — no code changes implied here.

---

## What shipped (2026-05-14)

**Repository:** `github.com/diazMelgarejo/perpetua-core` (not yet under `oramasys` org — see OQ14)
**Commit:** `9cb153a` "feat: perpetua-core v2 kernel Phase 1"
**Tests:** 13 smoke tests, all passing (Python 3.9.6)

| Module | File | Status |
|--------|------|--------|
| State | `perpetua_core/state.py` | ✅ shipped |
| LLM client | `perpetua_core/llm.py` | ✅ shipped |
| Hardware policy | `perpetua_core/policy.py` | ✅ shipped |
| Gossip bus | `perpetua_core/gossip.py` | ✅ shipped |
| Graph engine | `perpetua_core/graph/engine.py` | ✅ shipped |
| Graph nodes | `perpetua_core/graph/nodes.py` | ✅ shipped |
| Graph edges | `perpetua_core/graph/edges.py` | ✅ shipped |

Also shipped in orama-system (v1 layer, not v2 kernel):
- `bin/agents/dispatcher.py` — OramaToPTBridge with verifier gate
- `bin/agents/orchestrator/task_schema.py` — planning types (WorkerSpec, StageSpec, TaskPlan, PlanResult)
- `bin/agents/orchestrator/dispatch_loop.py` — run_plan() stage executor
- `tests/test_bridge.py` — 11 tests for verifier gate + parallel fan-out

---

## Spec vs. reality deltas

### Δ1 — Engine size: integrated ~130 lines, not ~70-line + plugins (D8)

**Spec (D8 revision in README.md):** `graph/engine.py` stays ~70 lines; Tier-3 features (checkpointer, interrupts, streaming, subgraphs, tool decorator) ship as separate `graph/plugins/` loaded via `MiniGraph.use(plugin)`.

**Actual:** Engine is ~130 lines with Tier-3 features (conditional edges, HITL interrupts, streaming via `astream()`, checkpointing via `GossipBus`) integrated directly. No `graph/plugins/` directory.

**Why it diverged:** The D8 revision (documented in README) happened in a separate session from the original D8 decision (documented in `00-context-and-decisions.md`). The `00-context` doc still describes the original Tier-3 (~220-line) intent. The README revision to "70-line + plugins" was not carried to `00-context`. When Phase 1 was built, the richer integrated design was followed.

**Deferred decision (OQ16):** Should engine.py be refactored to the ~70-line pure core + `plugins/` model, or should the integrated ~130-line design be canonicalized as the new D8? See `06-open-questions.md` OQ16.

---

### Δ2 — PerpetuaState: Pydantic dataclass, not BaseModel

**Spec (`01-kernel-spec.md`):**
```python
class PerpetuaState(BaseModel):
    session_id: str
    scratchpad: dict[str, Any] = Field(default_factory=dict)
    ...
```

**Actual (`perpetua_core/state.py`):**
```python
from pydantic.dataclasses import dataclass

@dataclass
class PerpetuaState:
    session_id: str
    scratchpad: str = ""
    ...
```

Two sub-deltas:
- `BaseModel` → `pydantic.dataclasses.dataclass` (affects `.model_dump()` vs `.to_dict()`)
- `scratchpad: dict[str, Any]` → `scratchpad: str` (simpler; nodes write text, not dicts)

**Why it diverged:** Dataclass gives copy-on-write semantics naturally via `replace()`. The `scratchpad` type change reflects how the ToolNode pattern actually works: nodes write text output, not structured dicts.

**Deferred decision (OQ13):** Canonicalize `PerpetuaState` as dataclass or BaseModel? Affects oramasys API layer (Phase 3) which needs to serialize/deserialize state across HTTP. See `06-open-questions.md` OQ13.

---

### Δ3 — `optimize_for` vs. `opt_hint` field name (OQ8 resolved)

**Spec (`01-kernel-spec.md`):** `opt_hint: OptHint = "quality"` on PerpetuaState.

**Actual:** Field is `optimize_for` on `TaskPlan` (in `task_schema.py`), not on `PerpetuaState`. PerpetuaState has no routing-hint fields — that's kept in `metadata`.

**Resolution:** `optimize_for` is canonical (matches GPT scaffold and policy routing key structure). It belongs on task/plan objects, not on kernel state. PerpetuaState's `metadata` dict is the extension point if routing hints need to flow through the graph.

OQ8 is resolved. See `06-open-questions.md` Resolved table.

---

### Δ4 — Python 3.9, not 3.11+ (OQ7 partially resolved)

**Spec (OQ7):** New repos should target Python ≥ 3.11.

**Actual:** perpetua-core smoke tests run on Python 3.9.6 (same CI runtime as PT). `pyproject.toml` declares `requires-python = ">=3.9"`.

**Why:** The test runner on this machine is Python 3.9.6. Using 3.10+ union syntax (`str | None`) was already a bug in the PT contracts file (required `Optional[str]` fix). Targeting 3.9 keeps all three repos consistent for now.

**Deferred decision:** OQ7 is partially resolved: 3.9 is the floor until a CI upgrade. Target 3.11 is deferred to the `oramasys` repo which will have its own CI setup. `perpetua-core` will bump to 3.11 in Phase 2 when `ExceptionGroup` / `tomllib` are needed.

---

### Δ5 — `graph/plugins/` directory: not created

**Spec:** `perpetua_core/graph/plugins/` with `checkpointer.py`, `interrupts.py`, `subgraphs.py`, `streaming.py`, `tool.py`.

**Actual:** No `plugins/` directory. Checkpointing is in `engine.py` directly; interrupts via `interrupt_before` constructor arg; streaming via `astream()` on `MiniGraph`.

**Deferred:** Phase 2 task — extract plugin interface and refactor if Δ1 resolves to "70-line + plugins". If Δ1 resolves to "integrated is canonical", this delta is closed.

---

### Δ6 — `message.py` not created

**Spec:** `perpetua_core/message.py` (Message types + role enums).

**Actual:** Messages are plain `Dict[str, Any]` in the `messages` list, following OpenAI wire format directly. No typed `Message` wrapper.

**Deferred decision (OQ17):** Typed `Message` enum wrapper adds ergonomics but couples to a schema choice. OpenAI wire-format dicts are simpler and interoperable. Decide before oramasys Phase 3 needs to serialize messages to LLMClient.

---

### Δ7 — `@tool` decorator not implemented

**Spec (D8):** `@tool` decorator with auto-schema from Pydantic v2 type hints.

**Actual:** ToolNode pattern (subprocess wrapper) is implemented. The `@tool` decorator for Python function tools is not. `graph/nodes.py` has `ToolNode` for CLIs but no function-level decorator.

**Deferred (Phase 2):** `@tool` decorator needs `graph/tool.py` — was intentionally left for Phase 2 when real oramasys nodes need it.

---

## orama-system v1 additions (same day, not v2 kernel)

These live in the **v1 orama-system repo** (`bin/agents/`), not in `perpetua-core`:

| Addition | File | Purpose |
|----------|------|---------|
| OramaToPTBridge | `bin/agents/dispatcher.py` | Typed dispatch: orama stage planner → PT OrchestrationSupervisor |
| TaskPlan schema | `bin/agents/orchestrator/task_schema.py` | orama-side planning types (WorkerSpec, StageSpec, TaskPlan, PlanResult) |
| Dispatch loop | `bin/agents/orchestrator/dispatch_loop.py` | run_plan() drives TaskPlan through stage sequence with verifier gate |
| Bridge tests | `tests/test_bridge.py` | 11 tests: verifier gate + parallel fan-out |

**Why in v1, not v2:** These are the bridge between today's v1 PT supervisor and orama's stage planner. They are not kernel primitives. When `oramasys` is created (Phase 3), the planning types and dispatch loop will migrate there. The `OramaToPTBridge` itself becomes obsolete when v2 fully replaces v1 PT.

**Deferred decision (OQ15):** Migration timeline for `OramaToPTBridge` and `TaskPlan` → `oramasys`. See `06-open-questions.md` OQ15.

---

## What Phase 2 needs to address

Priority order:

| Item | Ref | Urgency |
|------|-----|---------|
| Canonicalize PerpetuaState type (dataclass vs BaseModel) | Δ2 / OQ13 | Before oramasys Phase 3 |
| `@tool` decorator (`graph/tool.py`) | Δ7 | Before real nodes need it |
| `MiniGraph.max_steps` safety guard | OQ12 | Before any production run |
| GossipBus background writer | OQ11 | Before high-frequency nodes |
| Resolve engine integration vs. plugins | Δ1 / OQ16 | Shapes all Phase 2 graph work |
| `message.py` Message type | Δ6 / OQ17 | Before oramasys LLMClient wiring |
| Python 3.9 → 3.11 bump | Δ4 / OQ7 | Before oramasys CI |
| Capability-based routing in policy | OQ10 | v2.2 planning |
