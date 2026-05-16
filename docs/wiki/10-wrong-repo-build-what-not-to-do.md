# ⚠️ WHAT NOT TO DO — Wrong Repo Build (2026-05-14) — ARCHIVED TO WIKI

> **ARTIFACT STATUS: THIS FILE DOCUMENTS A MONUMENTAL MISTAKE.**
> It has been moved from `docs/v2/15-phase1-as-built.md` → `docs/wiki/10-wrong-repo-build-what-not-to-do.md`
> and is preserved here as a cautionary reference only.
>
> **DO NOT use any of the build facts, deltas, or OQ references below as canonical.**
> The canonical v2 build is at `oramasys/perpetua-core` (commit `2f717f5`, 2026-05-01).
>
> Full post-mortem: `docs/LESSONS.md` §"2026-05-14: Monumental Error — Wrong Repo Build"
> Repo registry (which org owns what): `../CLAUDE-instru.md` §1 / memory `project_repo_registry.md`

---

## What went wrong — Complete Agent-Readable Post-Mortem

### The incident (2026-05-14)

An AI agent (Claude Sonnet 4.5) was asked to enrich `docs/v2/` with post-Phase-1
reconciliation notes. Instead, it performed the following sequence of mistakes:

1. **Built a second v2 kernel from scratch** in `OpenClaw/perpetua-core` — a local
   directory inside the wrong parent project (`OpenClaw`, not `Documents/oramasys`).
2. **Pushed to the wrong GitHub remote:** `diazMelgarejo/perpetua-core` — a v1-legacy
   namespace. The agreed org for all v2 code is `oramasys/*`.
3. **Wrote `docs/v2/15-phase1-as-built.md`** treating the wrong build as if it were
   the real Phase 1 implementation, including detailed spec-vs-reality deltas.
4. **Modified 4 other `docs/v2/` files** to reference this wrong build as authoritative,
   corrupting the canonical documentation that had been correct since 2026-05-01.

The canonical v2 build had been shipped **13 days earlier** (2026-05-01) at
`oramasys/perpetua-core` (commit `2f717f5`), with 32 tests, 65-line engine +
`graph/plugins/`, Pydantic `BaseModel` state, and Python 3.11+.

The agent never checked whether the build it was "recording" already existed.
It never ran `git remote -v` before pushing. It skipped all `AskUserQuestion` gates
that the plan document required before touching `docs/v2/`.

### Why this is uniquely dangerous for AI agents

AI agents working across multiple local clones of related repos face a specific
failure mode that humans rarely encounter: the **phantom build problem**.

The agent had full access to:
- `OpenClaw/perpetua-core` (wrong clone, non-canonical)
- `Documents/oramasys/perpetua-core` (correct canonical repo)
- `OpenClaw/orama-system/docs/v2/` (canonical docs pointing to the canonical build)

Because it started from a plausible-looking directory, ran tests that passed, and
saw a `git push` succeed, it concluded the task was done. It never cross-checked
the remote URL against the agreed canonical home. The docs it wrote were internally
consistent — they just described the wrong artifact.

This is the AI equivalent of a surgeon operating on the wrong patient. The work
was technically competent. The target was wrong.

### The spec violations in the wrong build

| Spec decision | Canonical (`oramasys/perpetua-core`) | Wrong (`diazMelgarejo/perpetua-core`) |
|---------------|--------------------------------------|---------------------------------------|
| D8 revision: 65-line + plugins | ✅ 65-line + `graph/plugins/` dir | ❌ ~130-line integrated, no plugins/ |
| D7: Pydantic v2 `BaseModel` | ✅ `class PerpetuaState(BaseModel)` | ❌ `pydantic.dataclasses.dataclass` |
| `scratchpad: dict[str, Any]` | ✅ typed dict field | ❌ `scratchpad: str = ""` |
| D2: `oramasys` org | ✅ `oramasys/perpetua-core` | ❌ `diazMelgarejo/perpetua-core` |
| Python 3.11+ | ✅ `requires-python = ">=3.11"` | ❌ Python 3.9.6 |
| `@tool` decorator | ✅ `graph/plugins/tool.py` shipped | ❌ absent |
| Async `GossipBus` | ✅ `aiosqlite` | ❌ `sqlite3` (sync) |
| Test count | ✅ 32 tests | ❌ 13 smoke tests |

### Root causes (4 independent failures, all required)

**Failure 1 — No remote verification before push.**
`git remote -v` was not run before `git push`. The remote URL was assumed from
context. Rule: always verify remote URL before any push to a new repo.

**Failure 2 — No canonical existence check.**
The agent assumed Phase 1 had not been built. The correct check is:
`ls ~/Documents/oramasys/perpetua-core/` — if it exists, stop and read it.
Rule: before building anything in a v2 module, check `oramasys/` first.

**Failure 3 — Skipped planning gates.**
The plan required `AskUserQuestion` approval before modifying `docs/v2/`. These
gates exist precisely for actions that are hard to reverse. Skipping them is how
a recoverable mistake becomes a documented one.

**Failure 4 — No cross-reference against repo registry.**
The agreed repo-to-org mapping is documented in `CLAUDE-instru.md §1` and the
`project_repo_registry.md` memory entry. The agent did not consult either before
pushing. Rule: when pushing to any repo, match against the registry first.

### Recovery steps taken (commit `07581d6`)

1. `docs/v2/15-phase1-as-built.md` → moved to `docs/wiki/10-wrong-repo-build-what-not-to-do.md` (this file) as a cautionary artifact
2. `docs/v2/00-context-and-decisions.md`, `04-build-order.md`, `06-open-questions.md`, `README.md` → reverted to commit `935ce54` (the last known-good state)
3. LESSONS.md entry written (2026-05-14) with the full comparison table and "never again" rules
4. Warning header added to this file (2026-05-16) for future agent discoverability

### What future agents MUST do before any v2 work

```bash
# 1. Verify you are in the right repo
git remote -v   # must show github.com/oramasys/*, not diazMelgarejo/*

# 2. Confirm canonical build exists before building
ls ~/Documents/oramasys/perpetua-core/  # if present, use it — do not rebuild

# 3. Check the repo registry
# CLAUDE-instru.md §1 / memory: project_repo_registry.md
# v1-legacy = diazMelgarejo/*  |  v2-canonical = oramasys/*  |  NEVER MIX

# 4. Do not skip AskUserQuestion gates in any plan that modifies docs/v2/
```

### Cross-references

| Resource | What it contains |
|----------|-----------------|
| `docs/LESSONS.md` §"2026-05-14: Monumental Error" | Full post-mortem with spec comparison table and "never again" rules |
| `../CLAUDE-instru.md §1` | Canonical repo-to-org registry (source of truth for which org owns what) |
| Memory `project_repo_registry.md` | Agent-readable repo registry: v1-legacy vs v2-canonical org split |
| `orama-system/SKILL.md` | Behavioral rules: §"Repo identity" covers git remote verification |
| `Perpetua-Tools/SKILL.md` | §"Three-repo Architecture" — PT is L2, orama is L3, AlphaClaw is L1 |
| `orama-system/docs/v2/00-context-and-decisions.md` | Canonical decisions (D1–D9) that the wrong build violated |
| `orama-system/docs/v2/01-kernel-spec.md` | Kernel spec the canonical build correctly implements |

---

## ~~Phase 1 As-Built Notes (WRONG BUILD — for reference only)~~

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
