# Salvage Contribution Plan — Divergent Build → Canonical `oramasys/perpetua-core` Plugins

**Date:** 2026-05-14
**Status:** Design approved — docs only (no code yet, manual review gate before Phase 2)
**Source artifacts:** `docs/wiki/10-wrong-repo-build-what-not-to-do.md` (divergent build), `docs/v2/15-phase1-as-built.md` (canonical pattern)

---

## Context

A divergent v2 kernel was built at `OpenClaw/perpetua-core` (pushed to `diazMelgarejo/perpetua-core`, commit `9cb153a`, 2026-05-14) while the canonical build had already shipped 13 days earlier at `oramasys/perpetua-core` (commit `2f717f5`, 2026-05-01). The divergent build is SUPERSEDED, but it contains correct, production-grade logic for ~5 features the canonical build does NOT yet have.

This spec identifies what's salvageable and structures the salvage as **plugins/mods that orbit the 65-line canonical engine** — strictly following the existing `graph/plugins/` pattern (one file, one primitive, no cross-plugin imports, only `perpetua_core.state` + stdlib/aiosqlite deps).

**Hard constraints:**
- All salvage code goes to `oramasys/*` repos ONLY. Nothing to `diazMelgarejo/perpetua-core`.
- The 65-line `engine.py` stays 65 lines for its core loop. The `name` attribute is the only engine addition allowed in this spec.
- `set_entry()` and `compile()` are deferred to Phase 2 engine work — documented here, not implemented yet.

---

## Canonical plugin contract (recap)

Each existing plugin in `oramasys/perpetua-core/perpetua_core/graph/plugins/`:
- One `.py` file, one primitive class or function
- Imports only `perpetua_core.state`, stdlib, and (optionally) `aiosqlite`
- Does NOT import `perpetua_core.graph.engine`
- Returns objects/closures that the engine can use as `NodeFn` or `EdgeFn`

Existing plugins: `checkpointer.py`, `interrupts.py`, `streaming.py`, `structured_output.py`, `subgraphs.py`, `tool.py`.

---

## Salvage target inventory

| # | Salvage candidate | Target file (kernel) | Target file (app layer) | Source | Value |
|---|-------------------|----------------------|-------------------------|--------|-------|
| 1 | `ToolNode` — subprocess CLI wrapper | `perpetua_core/graph/plugins/tool_node.py` | `orama/graph/tool_node_ext.py` | divergent `nodes.py` | ⭐ Highest — canonical has zero subprocess support |
| 2 | `Edge` + `ConditionalEdge` typed objects | `perpetua_core/graph/plugins/routing.py` | — | divergent `edges.py` | 🔶 Ergonomic + logging |
| 3 | `GraphValidator` — structural validation | `perpetua_core/graph/plugins/validator.py` | — | divergent `compile()` | 🔶 Safety + OQ12 |
| 4 | `InterruptGuard` — pre-declared HITL pause points | `perpetua_core/graph/plugins/interrupt_guard.py` | — | divergent `interrupt_before` | 🔸 Complements existing `interrupts.py` |
| 5 | `MiniGraph.name` attribute | `perpetua_core/graph/engine.py` (1-line addition) | — | divergent engine | 🔸 Observability |
| 6 | `set_entry()` + `compile()` on engine | `perpetua_core/graph/engine.py` (Phase 2) | — | divergent engine | 📋 Deferred to Phase 2 engine task |

---

## Plugin 1 — `tool_node.py` (kernel) + `tool_node_ext.py` (app)

### Kernel: `perpetua_core/graph/plugins/tool_node.py`

```python
"""ToolNode plugin — wrap a subprocess CLI tool as a MiniGraph node."""
from __future__ import annotations
import asyncio
from typing import Any
from perpetua_core.state import PerpetuaState


class ToolNode:
    """Wraps a subprocess CLI tool (Codex, Gemini, shell scripts) as a node.

    Usage:
        gemini_node = ToolNode(name="gemini", cmd=["gemini", "--yolo", "-p"])
        graph.add_node("gemini", gemini_node)
    """

    def __init__(
        self,
        name: str,
        cmd: list[str],
        *,
        prompt_from: str = "scratchpad",
        timeout: float = 300.0,
        stdin_devnull: bool = True,
    ) -> None:
        self.name = name
        self.cmd = cmd
        self.prompt_from = prompt_from
        self.timeout = timeout
        self.stdin_devnull = stdin_devnull

    async def __call__(self, state: PerpetuaState) -> dict[str, Any]:
        prompt_value = getattr(state, self.prompt_from, None)
        # scratchpad is dict[str, Any] in canonical — extract prompt key if needed
        if isinstance(prompt_value, dict):
            prompt = str(prompt_value.get("prompt", ""))
        else:
            prompt = str(prompt_value or "")
        full_cmd = self.cmd + ([prompt] if prompt else [])

        stdin = asyncio.subprocess.DEVNULL if self.stdin_devnull else None
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=stdin,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            proc.terminate()
            return {
                "status": "error",
                "error": f"ToolNode '{self.name}' timed out after {self.timeout}s",
            }

        if proc.returncode != 0:
            return {
                "status": "error",
                "error": (
                    f"ToolNode '{self.name}' exited {proc.returncode}: "
                    f"{stderr.decode(errors='replace')[:500]}"
                ),
            }

        output = stdout.decode(errors="replace").strip()
        # Write output back to scratchpad as {"output": ...}
        return {
            "scratchpad": {"output": output, "tool": self.name},
            "status": "running",
        }
```

**Key adaptation from divergent build:**
- `scratchpad` is `dict[str, Any]` in canonical (not `str`) — return delta wraps output appropriately
- Python 3.11+ type annotations (`list[str]`, `dict[str, Any]`)
- Uses `PerpetuaState` from canonical (`BaseModel`, not dataclass)
- No engine import — pure subprocess wrapper

**Tests required:**
- Subprocess success → state delta has `scratchpad.output`
- Subprocess non-zero exit → state delta has `status="error"`, `error` message includes stderr
- Subprocess timeout → state delta has `status="error"`, timeout message
- `prompt_from` reads custom state field
- Empty prompt → cmd runs without appended prompt arg

---

### App layer: `oramasys/orama/graph/tool_node_ext.py`

Two factory functions for the oramasys methodology layer:

```python
"""ToolNode extensions for oramasys — wire v1 planning types and v2 state into ToolNode."""
from __future__ import annotations
from perpetua_core.graph.plugins.tool_node import ToolNode
from perpetua_core.state import PerpetuaState

# v1 planning types — imported from oramasys (NOT from perpetua-core)
# WorkerSpec is defined in oramasys-side planning module
# (it's app-level, not kernel)


def worker_spec_to_tool_node(spec) -> ToolNode:
    """Build a ToolNode from a v1 WorkerSpec (model_id, hardware_tier, prompt_template).

    Translates the v1 → v2 bridge: orama methodology emits WorkerSpec,
    this factory wires it to a v2 ToolNode in the graph.
    """
    # Map WorkerSpec.model_id → cmd
    cmd = _resolve_cmd_for_model(spec.model_id, spec.hardware_tier)
    return ToolNode(
        name=spec.role,
        cmd=cmd,
        prompt_from="scratchpad",
        timeout=spec.timeout or 300.0,
    )


def tool_node_from_state(state: PerpetuaState) -> ToolNode:
    """Build a ToolNode purely from PerpetuaState routing fields.

    Pure-v2 path: uses state.model_hint + state.target_tier to pick the CLI.
    No v1 dependency. Used when oramasys graphs construct nodes dynamically.
    """
    cmd = _resolve_cmd_for_model(state.model_hint, state.target_tier)
    return ToolNode(
        name=state.model_hint or "default",
        cmd=cmd,
        prompt_from="scratchpad",
    )


def _resolve_cmd_for_model(model_id: str | None, tier: str) -> list[str]:
    """Routing table: (model_id, tier) → CLI cmd list.
    
    Real implementation reads from agate's model_hardware_policy.
    Stub here for planning purposes.
    """
    # Phase 3 will wire this to agate's policy resolver
    raise NotImplementedError("Phase 3: wire to agate hardware policy")
```

**Boundary check:** `oramasys/orama/graph/tool_node_ext.py` imports `perpetua_core.graph.plugins.tool_node` (downward import). It does NOT modify perpetua-core. WorkerSpec lives in oramasys-side planning code (not in kernel). ✅

---

## Plugin 2 — `routing.py` (typed edges)

`oramasys/perpetua-core/perpetua_core/graph/plugins/routing.py`:

```python
"""Routing plugin — typed Edge and ConditionalEdge wrappers for MiniGraph."""
from __future__ import annotations
from typing import Any, Callable
from perpetua_core.state import PerpetuaState


class Edge:
    """Static edge: always routes from source to target."""
    def __init__(self, source: str, target: str) -> None:
        self.source = source
        self.target = target

    def __call__(self, state: PerpetuaState) -> str:
        return self.target

    def __repr__(self) -> str:
        return f"Edge({self.source!r} → {self.target!r})"


class ConditionalEdge:
    """Conditional edge: router function picks the next node.

    Args:
        source:  Source node name (documentation only).
        router:  Callable (state) → label_or_node_name.
        mapping: Optional label→node mapping. If provided, router returns labels
                 and the mapping resolves them to actual node names.
    """
    def __init__(
        self,
        source: str,
        router: Callable[[PerpetuaState], str],
        mapping: dict[str, str] | None = None,
    ) -> None:
        self.source = source
        self._router = router
        self._mapping = mapping or {}

    def __call__(self, state: PerpetuaState) -> str:
        label = self._router(state)
        return self._mapping.get(label, label)

    def __repr__(self) -> str:
        return f"ConditionalEdge({self.source!r} → <router>)"
```

**Why this works with canonical engine:** The engine accepts `str | EdgeFn` where `EdgeFn = Callable[[PerpetuaState], str]`. Both `Edge` and `ConditionalEdge` are callable and return a `str`. Zero engine changes.

**Tests required:**
- `Edge` always returns target regardless of state
- `ConditionalEdge` with no mapping → router output is the next node name
- `ConditionalEdge` with mapping → router output is a label, resolved via mapping
- `__repr__` strings render correctly (used in debug logs)

---

## Plugin 3 — `validator.py` (graph structural validation + OQ12 max_steps companion)

`oramasys/perpetua-core/perpetua_core/graph/plugins/validator.py`:

```python
"""Graph validator plugin — structural validation + max_steps spec.

Use this BEFORE constructing a MiniGraph to catch structural errors at build
time, not at runtime.
"""
from __future__ import annotations
from typing import Any, Callable
from perpetua_core.state import PerpetuaState

NodeFn = Callable[[PerpetuaState], object]
EdgeFn = Callable[[PerpetuaState], str]


def validate_graph(
    nodes: dict[str, NodeFn],
    edges: dict[str, str | EdgeFn],
    entry: str,
    *,
    max_steps: int | None = None,
) -> None:
    """Raise ValueError if the graph definition has structural errors.

    Checks:
    - entry node exists in nodes
    - every edge source exists in nodes
    - every static edge target exists in nodes OR equals END sentinel
    - max_steps (if provided) is a positive integer
    """
    from perpetua_core.graph.engine import END

    if not isinstance(entry, str) or not entry:
        raise ValueError("entry must be a non-empty string")
    if entry not in nodes:
        raise ValueError(f"entry node '{entry}' not in nodes")

    for src, dst in edges.items():
        if src not in nodes:
            raise ValueError(f"edge source '{src}' not in nodes")
        if isinstance(dst, str) and dst != END and dst not in nodes:
            raise ValueError(f"static edge target '{dst}' not in nodes")
        # callable edges (EdgeFn) are not statically checkable — skip

    if max_steps is not None:
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError(f"max_steps must be a positive int, got {max_steps!r}")
```

**Why this matters:**
- Closes OQ12 (max_steps guard) at the spec level. Runtime enforcement is a Phase 2 engine change.
- Catches "node X referenced by edge but not defined" bugs before first `ainvoke()` call.
- Standalone function — doesn't need access to MiniGraph internals.

**Tests required:**
- Valid graph → no exception
- Missing entry node → ValueError
- Edge source not in nodes → ValueError
- Static edge target not in nodes (and not END) → ValueError
- Callable edge target → skipped (no error)
- max_steps invalid → ValueError

---

## Plugin 4 — `interrupt_guard.py` (pre-declared HITL pause points)

`oramasys/perpetua-core/perpetua_core/graph/plugins/interrupt_guard.py`:

```python
"""InterruptGuard plugin — pre-declare HITL pause points at graph build time.

Complements the existing duck-typed `Interrupt` exception in interrupts.py:
- Runtime interrupts: node raises `Interrupt(...)` at any time
- Pre-declared interrupts: this plugin wraps nodes to raise Interrupt BEFORE
  executing them (caller decides at graph construction)
"""
from __future__ import annotations
from typing import Any, Callable
from perpetua_core.graph.plugins.interrupts import Interrupt
from perpetua_core.state import PerpetuaState

NodeFn = Callable[[PerpetuaState], object]


def wrap_with_interrupt(node_name: str, original_fn: NodeFn) -> NodeFn:
    """Return a wrapped node that raises Interrupt before invoking the original."""
    async def wrapped(state: PerpetuaState) -> object:
        raise Interrupt(
            prompt=f"Pausing before '{node_name}' — resume when human-authorized",
            payload={"node": node_name},
        )
    wrapped.__name__ = f"interrupt_before_{node_name}"
    return wrapped


class InterruptGuard:
    """Apply pre-declared interrupt-before nodes to a node dict.

    Usage:
        nodes = {"verifier": verifier_fn, "crystallizer": crystallizer_fn}
        guard = InterruptGuard(interrupt_before=["crystallizer"])
        nodes = guard.apply(nodes)
        # Now graph.add_node("crystallizer", nodes["crystallizer"]) wraps with Interrupt
    """
    def __init__(self, interrupt_before: list[str]) -> None:
        self._interrupt_before = interrupt_before

    def apply(self, nodes: dict[str, NodeFn]) -> dict[str, NodeFn]:
        out = dict(nodes)
        for name in self._interrupt_before:
            if name not in out:
                raise ValueError(f"interrupt_before references unknown node '{name}'")
            out[name] = wrap_with_interrupt(name, out[name])
        return out
```

**Tests required:**
- Wrapping a node → calling it raises `Interrupt` with matching prompt
- `apply()` only wraps named nodes; others untouched
- Unknown node name → ValueError
- Wrapped function works in canonical engine: graph stops with `status="interrupted"`

---

## Engine Addition #5 — `MiniGraph.name` attribute (trivial)

```python
# perpetua_core/graph/engine.py — MiniGraph.__init__

def __init__(self, *, name: str = "graph", interrupt_handler: str | None = None):
    self.name = name  # NEW: observability for logs and debug
    self._nodes: dict[str, NodeFn] = {}
    self._edges: dict[str, str | EdgeFn] = {}
    self._interrupt_handler = interrupt_handler
```

**Tests required:**
- `MiniGraph(name="ultrathink").name == "ultrathink"`
- Default name is `"graph"` (backward compatible — existing tests don't pass `name=`)

---

## Phase 2 Engine Items #6 — `set_entry()` + `compile()` (deferred)

**Not implemented in this salvage spec.** Documented here for Phase 2 traceability.

### `MiniGraph.set_entry(node_name: str)` 
Replaces `graph.add_edge(START, "first_node")`. Hides the START sentinel behind an explicit API method. Backward compatible if both paths supported.

### `MiniGraph.compile()` lazy-invoked from `ainvoke()`
Runs `validate_graph()` on the engine's internal state before first execution. Catches structural errors immediately rather than mid-pipeline.

**Phase 2 task:** Add both methods, update `ainvoke()` to call `compile()` lazily on first run, port the validator plugin's checks into the engine method, write tests.

**Why deferred:** Requires touching the 65-line engine itself + test coverage. Validator plugin gives 90% of the value as an opt-in external check today.

---

## What changes where (summary)

| Repo | File | Action |
|------|------|--------|
| `oramasys/perpetua-core` | `perpetua_core/graph/plugins/tool_node.py` | CREATE |
| `oramasys/perpetua-core` | `perpetua_core/graph/plugins/routing.py` | CREATE |
| `oramasys/perpetua-core` | `perpetua_core/graph/plugins/validator.py` | CREATE |
| `oramasys/perpetua-core` | `perpetua_core/graph/plugins/interrupt_guard.py` | CREATE |
| `oramasys/perpetua-core` | `perpetua_core/graph/engine.py` | EDIT: add `name` attribute (1 line) |
| `oramasys/perpetua-core` | `tests/test_plugins_tool_node.py` | CREATE (5 tests) |
| `oramasys/perpetua-core` | `tests/test_plugins_routing.py` | CREATE (4 tests) |
| `oramasys/perpetua-core` | `tests/test_plugins_validator.py` | CREATE (6 tests) |
| `oramasys/perpetua-core` | `tests/test_plugins_interrupt_guard.py` | CREATE (4 tests) |
| `oramasys/oramasys` | `orama/graph/tool_node_ext.py` | CREATE |
| `oramasys/oramasys` | `tests/test_tool_node_ext.py` | CREATE (3 tests) |

**Test count delta:** 32 → ~51 in perpetua-core (+19), 4 → ~7 in oramasys (+3).

**NOT changing:** the 65-line `engine.py` core loop (one line added for `name`, no logic changes), any of the existing 6 plugins, `state.py`, `policy.py`, `gossip.py`, `llm.py`.

---

## Acceptance gates

- All new plugin tests green (TDD: write tests first, then implementation)
- Existing 32 tests in perpetua-core still green (no regression)
- Existing 4 tests in oramasys still green
- `oramasys/perpetua-core` engine.py diff is exactly 1 line (name attr)
- One-way import boundary lint passes: no `perpetua_core` file imports `orama` or `oramasys`

---

## Deferred items (NOT in this spec — Phase 2 or later)

- `MiniGraph.set_entry()` + `MiniGraph.compile()` — engine API improvements (Phase 2 engine task)
- `OramaToPTBridge` migration from v1 → oramasys (OQ15 — Phase 3)
- `message.py` typed Message wrapper (OQ17 — Phase 3)
- Sentinel Node for SWARM misalignment monitoring (Phase 2)
- Capability-based routing in agate (OQ10 — v2.2)
- `dispatch_node` wired to `LLMClient` (Phase 3)

---

## Phase 2 engine additions — `set_entry()` + `compile()` — IMPLEMENTATION DEFERRED

> **SPEC ADDITIONS ONLY.** No code is written here. Actual implementation goes to a dedicated Phase 2 brainstorm session, opened after the manual review gate below clears. This pattern matches the "Deferred items" table above and the `04-build-order.md` Phase 2 "Still needed" list.

### Rationale

The four Phase 1 plugins above deliver most of their value without any engine changes. Two engine-level methods unlock a cleaner and safer graph construction API for all of them — and for every oramasys graph that ships in Phase 3 and beyond.

**Why `set_entry()` matters for the plugins above:**
- Currently, the caller wires the entry node by calling `graph.add_edge(START, "first_node")`. The START sentinel is an implementation detail that leaks into every graph construction site. `set_entry()` hides it behind an explicit method and makes the intent readable.
- `InterruptGuard.apply()` wraps nodes before they are added to the engine. Today the caller must manually ensure the wrapped node for the entry position is also the START-edge target. `set_entry()` decouples node registration from entry assignment, making the pattern less brittle.
- `ToolNode` graphs constructed in `tool_node_ext.py` currently require the caller to know which node name was passed to `add_edge(START, ...)`. An explicit `set_entry()` call recorded on the engine removes that implicit coupling.

**Why `compile()` matters for the plugins above:**
- `validator.py` ships as an opt-in, standalone check. A caller who forgets to call `validate_graph()` before `ainvoke()` gets no safety net. `compile()` on the engine makes validation automatic and impossible to skip.
- `routing.py` edges that reference undefined node names are currently detectable only at runtime (when the engine tries to route to a missing key). `compile()` runs `validate_graph()` at graph-freeze time, surfacing the error at construction instead of mid-pipeline.
- `interrupt_guard.py` validates that named nodes exist when `apply()` is called. `compile()` adds a second, engine-level check that the interrupt-wrapped nodes are correctly wired into the graph structure (edges reach them, entry does not bypass them).

---

### `MiniGraph.set_entry(node_name: str)` — Phase 2 engine task

**Target file:** `perpetua_core/graph/engine.py` (Phase 2 addition)

**Signature:**
```python
def set_entry(self, node_name: str) -> None
```

**Semantics:**
- Records `node_name` as the designated entry point for the graph.
- Internally equivalent to `self.add_edge(START, node_name)` — writes the START-keyed edge into `self._edges`.
- Calling `set_entry()` a second time overwrites the previous entry; raises `ValueError` if `node_name` is not yet in `self._nodes` (fail-fast at construction time).
- `add_edge(START, ...)` continues to work in Phase 1 and Phase 2 — both paths are supported. `set_entry()` is additive, not a replacement.

**What it replaces:**

In Phase 1, entry is set implicitly via:
```python
graph.add_edge(START, "route")   # current pattern — still valid in Phase 2
```

In Phase 2, the following is also valid:
```python
graph.set_entry("route")         # Phase 2 explicit API
```

The existing 32 tests in perpetua-core use `add_edge(START, ...)` and remain untouched. Neither path changes in Phase 1.

**Position in MiniGraph:** added as a method alongside `add_node` and `add_edge`, not inside the `ainvoke` loop. Engine line count grows by approximately 5 lines (method definition + docstring + validation guard).

---

### `MiniGraph.compile()` — Phase 2 engine task

**Target file:** `perpetua_core/graph/engine.py` (Phase 2 addition)

**Signature:**
```python
def compile(self) -> MiniGraph
```

**Semantics:**
- Freezes the graph: after `compile()` is called, `add_node`, `add_edge`, and `set_entry` raise `RuntimeError("graph is already compiled")`.
- Runs `validate_graph(self._nodes, self._edges, entry=self._entry, ...)` internally, raising `ValueError` on any structural error (missing entry node, dangling edge source, static edge target not in nodes and not END).
- Returns `self` to allow chaining: `graph = MiniGraph().add_node(...).add_edge(...).compile()`.
- Sets a `_compiled: bool` flag on the instance.

**Interaction with `ainvoke()`:** `ainvoke()` is updated to call `compile()` lazily on first invocation if `_compiled` is False. This means graphs that never explicitly call `compile()` still get validated before the first node executes. Explicit `compile()` calls at construction time are the preferred pattern (eager validation, fail-fast).

**Interaction with `validator.py` plugin:**
- `compile()` imports and calls `validate_graph()` from `perpetua_core.graph.plugins.validator` — the Phase 1 plugin. The validation logic is not duplicated into the engine; the engine delegates to the plugin.
- This preserves the plugin boundary: the engine grows by approximately 10 lines (compile method + lazy-compile guard in ainvoke); the validation logic stays in `validator.py`.
- Callers who prefer the standalone `validate_graph()` external check continue to use it as before — there is no regression.

**Interaction with `interrupt_guard.py` plugin:**
- `InterruptGuard.apply()` must be called before `compile()`. The guard wraps nodes in-place; `compile()` freezes the node dict. If a caller calls `compile()` then tries to call `guard.apply()`, the subsequent `add_node` inside apply raises `RuntimeError`. This ordering requirement must be documented clearly in the Phase 2 implementation.
- Recommended construction order in Phase 2:
  1. Register nodes via `add_node`
  2. Apply `InterruptGuard` (if used)
  3. Register edges via `add_edge`
  4. Call `set_entry()` (or use `add_edge(START, ...)`)
  5. Call `compile()` — or let `ainvoke()` trigger it lazily

---

### Effect on existing Phase 1 deliverables

| Item | Phase 1 behavior | Phase 2 with additions |
|------|-----------------|------------------------|
| `engine.py` | 65 lines, Phase 1 core loop unchanged | Grows by ~15 lines — `set_entry`, `compile`, lazy guard in `ainvoke` |
| Existing 32 perpetua-core tests | All pass | All still pass — both new methods are additive |
| Existing 4 oramasys tests | All pass | All still pass |
| `validator.py` plugin | Opt-in external check | Also called internally by `compile()`; standalone use still supported |
| `interrupt_guard.py` plugin | Call before `add_node` or after | Must be called before `compile()`; ordering documented |
| `tool_node.py` + `routing.py` | No engine dependency | Unaffected |
| `MiniGraph.name` attribute | Shipped Phase 1 (1-line addition) | Unchanged |

---

### Backward compatibility with canonical `oramasys/perpetua-core@2f717f5`

The canonical shipped build (commit `2f717f5`, 2026-05-01) has zero references to `set_entry()` or `compile()`. Adding these methods in Phase 2 is a strictly additive change:

- No existing method signatures change.
- No existing behavior changes unless `compile()` is explicitly called or `ainvoke()` triggers the lazy-compile path — which only runs `validate_graph()`, a pure read over existing internal state.
- The `_compiled` flag defaults to `False`; existing callsites that never call `compile()` see no difference until `ainvoke()` is invoked, at which point the lazy guard runs silently and sets the flag.
- A graph that passes all 32 existing tests today continues to pass them after Phase 2 ships.
- The D8 constraint ("engine size bounded") is respected: the engine grows from 65 lines to approximately 80 lines — within the D8 Tier 3 intent, not a structural violation.

---

### Phase 2 implementation checklist (for the Phase 2 brainstorm session — NOT this spec)

- [ ] Add `set_entry(node_name: str) -> None` to `MiniGraph`
- [ ] Add `compile() -> MiniGraph` to `MiniGraph`
- [ ] Update `ainvoke()` with lazy-compile guard (`if not self._compiled: self.compile()`)
- [ ] Add `_compiled: bool = False` instance variable
- [ ] Document ordering requirement: `InterruptGuard.apply()` before `compile()`
- [ ] Write tests: `set_entry` records entry, duplicate call overwrites, unknown node raises `ValueError`
- [ ] Write tests: `compile()` returns self, freezes graph, raises `RuntimeError` on post-compile mutation
- [ ] Write tests: `ainvoke()` lazy-compile path triggers `validate_graph()` before first node executes
- [ ] Confirm all 32 existing perpetua-core tests still pass after changes
- [ ] Confirm engine.py line count growth is bounded (target: 65 + ~15 = ~80 lines)

---

## Manual review gate (before any code work)

This spec is docs-only. Before any of the above is implemented:

1. Run `cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core && python -m pytest tests/ -v` → expect 32 passing
2. Run `cd /Users/lawrencecyremelgarejo/Documents/oramasys/oramasys && python -m pytest tests/ -v` → expect 4 passing
3. Read all 6 plugins to confirm patterns
4. Verify all 3 repos are 0 ahead/0 behind remote
5. Open a NEW brainstorm session to plan Phase 2 implementation in detail using subagent-driven-development

Only after manual review passes do we touch code.
