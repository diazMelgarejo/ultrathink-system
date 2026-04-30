# 01 — Kernel Spec (perpetua-core, v2.0 blocking)

> The only **blocking** spec for v2.0. Everything else (modules) ships at its own pace.
> **Revised D8 (2026-04-30)**: MiniGraph kernel = ~70 lines (essential services only).
> Tier-3 features (checkpointer, interrupts, subgraphs, tool, streaming, structured output)
> ship as **graph plugins** under `perpetua_core/graph/plugins/`, loaded on demand.
> Cold kernel has zero optional dependencies.

---

## Repo layout (`perpetua-core/`)

```
perpetua-core/
├── pyproject.toml            # MIT license, deps: pydantic>=2, openai, pyyaml, aiosqlite
├── LICENSE                   # MIT
├── README.md
├── perpetua_core/
│   ├── __init__.py
│   ├── state.py              # PerpetuaState (Pydantic v2)
│   ├── message.py            # Message + role enums
│   ├── llm.py                # LLMClient (async OpenAI-compat)
│   ├── policy.py             # HardwarePolicyResolver + HardwareAffinityError
│   ├── gossip.py             # GossipBus (SQLite event log)
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── engine.py         # MiniGraph core
│   │   ├── nodes.py          # Node base + ToolNode
│   │   ├── edges.py          # Edge + conditional edge router
│   │   ├── checkpointer.py   # SQLite checkpointer (resumability)
│   │   ├── interrupts.py     # HITL pause/resume
│   │   ├── subgraphs.py      # Subgraph composition
│   │   ├── streaming.py      # AsyncGenerator over node + state events
│   │   └── tool.py           # @tool decorator (Pydantic v2 schema autogen)
│   └── config/
│       └── model_hardware_policy.example.yml
└── tests/
    ├── test_state.py
    ├── test_policy.py
    ├── test_minigraph.py           # kernel in isolation — no plugins
    ├── test_plugins_checkpointer.py
    ├── test_plugins_interrupts.py
    ├── test_plugins_tool.py
    └── test_plugins_structured_output.py
```

**Kernel target: ~70 lines** (`graph/engine.py` only — START/END, node registry, edge routing, `ainvoke`).
**Plugin target: ~30–50 lines each** — loaded via `MiniGraph.use(plugin)`, never in engine imports.
Cold `MiniGraph()` with no plugins: pure Python, zero optional deps.

---

## 1. `PerpetuaState` (Pydantic v2)

```python
# perpetua_core/state.py
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

HardwareTier = Literal["mac", "windows", "shared"]
TaskType     = Literal["coding", "reasoning", "research", "ops"]
OptHint      = Literal["speed", "quality", "reasoning"]

class PerpetuaState(BaseModel):
    session_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    scratchpad: dict[str, Any]    = Field(default_factory=dict)
    status: Literal["idle", "running", "interrupted", "error", "done"] = "idle"
    error: str | None = None

    # Grok additions
    nodes_visited: list[str]    = Field(default_factory=list)
    metadata: dict[str, Any]    = Field(default_factory=dict)
    retry_count: int            = 0

    # routing hints
    target_tier: HardwareTier   = "shared"
    task_type: TaskType         = "reasoning"
    opt_hint: OptHint           = "quality"
    model_hint: str | None      = None

    def merge(self, delta: dict[str, Any]) -> "PerpetuaState":
        """Apply a node's output delta. Engine calls this per step."""
        return self.model_copy(update=delta)
```

Field rationale:
- `messages`/`scratchpad` — distinct: messages = chat-shaped LLM I/O; scratchpad = node-internal working memory
- `nodes_visited` — auditable graph traversal (Grok)
- `metadata` — extensible without schema bumps (Grok)
- `retry_count` — first-class; reducers increment on retry (Grok)
- routing hints — kept on state so middle-of-graph routing decisions can read them

---

## 2. `LLMClient`

```python
# perpetua_core/llm.py
import os
from openai import AsyncOpenAI

DEFAULT_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
DEFAULT_API_KEY  = os.getenv("LLM_API_KEY", "ollama")

class LLMClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_key: str = DEFAULT_API_KEY):
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat(self, *, model: str, messages: list[dict], **kwargs):
        return await self._client.chat.completions.create(model=model, messages=messages, **kwargs)
```

**LAN endpoints** (from user memory, verified `routing.json` distributed=true):
- Mac LM Studio: `http://192.168.x.110:1234/v1`
- Windows LM Studio: `http://192.168.x.108:1234/v1`
- Local fallback: `http://localhost:11434/v1` (Ollama)

LAN routing belongs to the policy + graph layer, not the LLMClient itself. The client is a dumb dispatcher.

---

## 3. `HardwarePolicyResolver`

```python
# perpetua_core/policy.py
from typing import Literal
import yaml
from pathlib import Path

class HardwareAffinityError(RuntimeError):
    """Pre-spawn hardware affinity gate failure. Re-exported from v1."""

Verdict = Literal["ALLOW", "PREFER", "NEVER"]

class HardwarePolicyResolver:
    def __init__(self, policy_path: Path):
        self._policy = yaml.safe_load(policy_path.read_text())

    def check_affinity(self, *, model: str, target_tier: str) -> Verdict:
        rule = self._policy["models"].get(model)
        if rule is None:
            return "ALLOW"  # unknown models are unconstrained
        verdict = rule.get(target_tier, "ALLOW")
        if verdict == "NEVER":
            raise HardwareAffinityError(f"{model} forbidden on {target_tier}")
        return verdict
```

**`model_hardware_policy.example.yml`:**

```yaml
# perpetua-core/perpetua_core/config/model_hardware_policy.example.yml
version: 1
models:
  Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2:
    mac: NEVER
    windows: PREFER       # 24GB VRAM RTX 3080 — fits
    shared: ALLOW
  qwen3-coder:14b:
    # known-bad ID from v1 hallucination — explicitly NEVER on all tiers
    mac: NEVER
    windows: NEVER
    shared: NEVER
  llama-3.2-3B:
    mac: PREFER
    windows: ALLOW
    shared: ALLOW
```

Carries forward the `HardwareAffinityError` re-export pattern canonicalized in `2026-04-28-perpetua-orama-master-revamp.md` Task 4.

---

## 4. `MiniGraph` engine — 70-line kernel + plugin system

State machine: nodes (callables that return state deltas), edges (router fns), start/end. API-compatible with the LangGraph mental model so a future migration to real LangGraph remains cheap. **Tier-3 features ship as plugins**, never embedded in `engine.py`.

### 4a. Core engine (`graph/engine.py`)

```python
# perpetua_core/graph/engine.py
from typing import Awaitable, Callable
from ..state import PerpetuaState

NodeFn = Callable[[PerpetuaState], Awaitable[dict]]
EdgeFn = Callable[[PerpetuaState], str]  # returns next node name

class MiniGraph:
    def __init__(self):
        self._nodes: dict[str, NodeFn] = {}
        self._edges: dict[str, EdgeFn | str] = {}
        self.start: str | None = None
        self.end: str = "__end__"

    def add_node(self, name: str, fn: NodeFn) -> "MiniGraph":
        self._nodes[name] = fn
        return self

    def add_edge(self, src: str, dst: str | EdgeFn) -> "MiniGraph":
        self._edges[src] = dst
        return self

    def set_start(self, name: str) -> "MiniGraph":
        self.start = name
        return self

    async def ainvoke(self, state: PerpetuaState) -> PerpetuaState:
        node = self.start
        while node and node != self.end:
            state = state.merge({"nodes_visited": [*state.nodes_visited, node]})
            delta = await self._nodes[node](state)
            state = state.merge(delta)
            edge  = self._edges.get(node, self.end)
            node  = edge(state) if callable(edge) else edge
        return state.merge({"status": "done"})
```

### 4b. Conditional edges + state reducers — built into engine

`add_edge(src, fn)` where `fn(state) -> str` is the conditional router. State merge happens in `state.merge()` — single delta-application path; reducers can be added by subclassing `PerpetuaState` and overriding `merge()`.

### 4c. SQLite checkpointer (`graph/checkpointer.py`)

```python
# perpetua_core/graph/checkpointer.py
import aiosqlite, json
from ..state import PerpetuaState

class SqliteCheckpointer:
    def __init__(self, db_path: str):
        self._db_path = db_path

    async def save(self, state: PerpetuaState, *, node: str):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO checkpoints (session_id, node, state_json) VALUES (?, ?, ?)",
                (state.session_id, node, state.model_dump_json()),
            )
            await db.commit()

    async def load_latest(self, session_id: str) -> PerpetuaState | None:
        async with aiosqlite.connect(self._db_path) as db:
            row = await (await db.execute(
                "SELECT state_json FROM checkpoints WHERE session_id=? ORDER BY id DESC LIMIT 1",
                (session_id,),
            )).fetchone()
            return PerpetuaState.model_validate_json(row[0]) if row else None
```

Engine plumbing (in `engine.py`) accepts `checkpointer=...`; if set, persists after each node.

### 4d. HITL interrupts (`graph/interrupts.py`)

```python
# perpetua_core/graph/interrupts.py
class Interrupt(Exception):
    """Raised by a node to pause graph execution and surface a HITL prompt."""
    def __init__(self, prompt: str, payload: dict | None = None):
        self.prompt  = prompt
        self.payload = payload or {}
```

Engine catches `Interrupt`, sets `state.status = "interrupted"`, persists via checkpointer, returns. Caller resumes by calling `graph.aresume(session_id, user_response=...)` which loads checkpoint and re-enters at the interrupting node.

MAESTRO 7-layer enforcement (v2.5) will use this primitive heavily for human-checkpoint gates.

### 4e. Subgraphs (`graph/subgraphs.py`)

A subgraph is just a `MiniGraph` exposed as a single node:

```python
# perpetua_core/graph/subgraphs.py
from .engine import MiniGraph
from ..state import PerpetuaState

def as_node(subgraph: MiniGraph):
    async def node(state: PerpetuaState) -> dict:
        result = await subgraph.ainvoke(state)
        return result.model_dump()
    return node
```

Critical for microkernel modularity — each non-kernel module ships as a subgraph that the kernel can compose.

### 4f. ToolNode contract (`graph/nodes.py`)

```python
# perpetua_core/graph/nodes.py
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from ..state import PerpetuaState

class ToolNode:
    """Subprocess CLI as a graph node. Used for Claude Code, Codex CLI, shell tools."""
    def __init__(self, cmd: list[str]):
        self._cmd = cmd

    async def __call__(self, state: PerpetuaState) -> dict:
        proc = await create_subprocess_exec(*self._cmd, stdout=PIPE, stderr=PIPE)
        out, err = await proc.communicate()
        return {
            "scratchpad": {**state.scratchpad, "tool_stdout": out.decode(), "tool_stderr": err.decode()},
            "metadata":   {**state.metadata,   "tool_exit": proc.returncode},
        }
```

API-compatible with LangGraph's ToolNode contract — same call shape so external frameworks (post-D5 Plugin API) can hand us tools they constructed for LangGraph.

### 4g. Streaming (`graph/streaming.py`)

```python
# perpetua_core/graph/streaming.py
from typing import AsyncGenerator
from ..state import PerpetuaState

# Yields ("node", node_name, delta) and ("token", token_str) events.
StreamEvent = tuple[str, str, dict] | tuple[str, str]

async def astream(graph, state: PerpetuaState) -> AsyncGenerator[StreamEvent, None]:
    """Wraps ainvoke; yields per-node deltas. Token-level streaming
    is enabled at the LLMClient layer (OpenAI streaming API)."""
    ...  # implementation in Phase 2
```

### 4h. `@tool` decorator (`graph/tool.py`)

```python
# perpetua_core/graph/tool.py
import inspect
from pydantic import create_model

def tool(fn):
    """Decorate a typed function; auto-derives a Pydantic v2 input schema."""
    sig = inspect.signature(fn)
    fields = {
        name: (param.annotation, ... if param.default is inspect.Parameter.empty else param.default)
        for name, param in sig.parameters.items()
    }
    InputModel = create_model(f"{fn.__name__}Input", **fields)
    fn._input_schema = InputModel
    fn._tool_name    = fn.__name__
    return fn
```

Mirrors Pydantic AI Slim's `@tool` ergonomics but emits plain Pydantic v2 — no `pydantic-ai` runtime dep.

### 4i. Structured output validation

Implemented at `LLMClient.chat_structured(model, messages, output_schema: type[BaseModel])` — calls LLM, validates against schema, retries with the schema appended to the prompt on parse failure (max retries from env). Increments `state.retry_count`.

---

## 5. `GossipBus` (SQLite event log)

```python
# perpetua_core/gossip.py
import aiosqlite, json, time
from typing import Literal

EventType = Literal["load", "route", "affinity_check", "dispatch", "error"]

class GossipBus:
    def __init__(self, db_path: str):
        self._db_path = db_path

    async def emit(self, event_type: EventType, payload: dict):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO gossip (ts, event_type, payload_json) VALUES (?, ?, ?)",
                (time.time(), event_type, json.dumps(payload)),
            )
            await db.commit()

    async def subscribe(self, *, since: float = 0.0):
        # async-iterator of events newer than `since` — long-poll pattern
        ...
```

Replaces volatile `.json` blobs from v1 with a durable, queryable audit trail. Shares the same SQLite database file as the checkpointer (`perpetua_core.db` by default).

---

## 6. FastAPI glass-window (lives in `oramasys`, depicted here for completeness)

```python
# oramasys/api/server.py — handlers ≤ 10 lines
from fastapi import FastAPI
from oramasys.graphs import perpetua_graph
from oramasys.api.contracts import RunRequest, RunResponse

app = FastAPI(title="oramasys")

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest) -> RunResponse:
    state  = req.to_state()
    result = await perpetua_graph.ainvoke(state)
    return RunResponse.from_state(result)
```

Lifted/skeletonized from today's `orama-system/api_server.py` per D9. Internal-only contract for v2.0 (D5).

---

## Verification (kernel acceptance criteria)

1. `python -c "import perpetua_core; perpetua_core.MiniGraph()"` succeeds — no circular imports, no missing deps.
2. `pytest tests/test_state.py` — Pydantic v2 round-trip + `merge()` delta application.
3. `pytest tests/test_policy.py` — `check_affinity()` raises `HardwareAffinityError` for NEVER tiers.
4. `pytest tests/test_minigraph.py` — 3-node graph (start → middle → end) runs end-to-end with state delta merging and `nodes_visited` populated.
5. `pytest tests/test_checkpointer.py` — save then load reproduces identical state.
6. `pytest tests/test_interrupts.py` — node raises `Interrupt`, graph status becomes `"interrupted"`, checkpoint saved, `aresume` continues correctly.
7. `pytest tests/test_tool_decorator.py` — `@tool`-decorated function exposes correct `_input_schema` Pydantic model.
8. `pytest tests/test_structured_output.py` — `chat_structured()` retries on parse failure and increments `retry_count`.
9. **Import boundary lint**: `grep -r "from oramasys" perpetua-core/` returns nothing. (CI gate.)
10. Live integration: graph node calls Mac LM Studio (`192.168.x.110:1234`) and Windows LM Studio (`192.168.x.108:1234`) per `model_hardware_policy.yml` routing; `agent_log` table in SQLite shows correct dispatch sequence.
