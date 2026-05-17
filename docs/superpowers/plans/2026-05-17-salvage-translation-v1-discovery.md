# Salvage Translation + v1 IP-Aware Backend Discovery — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (a) Add the four valuable plugins + engine improvements salvaged from `diazMelgarejo/perpetua-core@9cb153a` into canonical `oramasys/perpetua-core@2f717f5`, (b) ship IP-aware backend discovery + health validation in v1 `Perpetua-Tools` so we can target specific models on specific IPs (autodetect OR direct IP) today, and (c) wire that discovery into v2 `oramasys/oramasys.dispatch_node` so the same selector serves both generations.

**Architecture (LangGraph concept → canonical equivalent):**

| LangGraph concept | Canonical `oramasys` equivalent | Status |
|---|---|---|
| `State` (shared whiteboard) | `perpetua_core.state.PerpetuaState` (Pydantic v2 `BaseModel`) | ✅ shipped |
| `Node` (unit of work) | `async (state) -> dict` callable | ✅ shipped |
| `Edge` (static decision) | `MiniGraph.add_edge(src, "dst")` | ✅ shipped |
| `Conditional Edge` (branch) | `MiniGraph.add_edge(src, lambda state: "next")` | ✅ shipped (raw) — **plugin needed for label registry** (Task 7) |
| `Cycle / Loop` (back to prior node) | callable edge returning earlier node + **`max_steps` guard** | ❌ guard missing (Task 5) |
| `START` / `END` | sentinels in `perpetua_core.graph.engine` | ✅ shipped |
| `Checkpointer` | `perpetua_core.graph.plugins.checkpointer` (SQLite snapshots) | ✅ shipped |
| `Send()` fan-out (parallel) | `perpetua_core.graph.plugins.parallel` | ❌ missing (Task 11) |
| Tool-node (CLI subprocess) | `perpetua_core.graph.plugins.tool_node` | ❌ missing (Task 8) — distinct from existing `tool.py` `@tool` decorator |
| Input/output validator | `perpetua_core.graph.plugins.validator` | ❌ missing (Task 9) |
| Interrupt merge-vs-drop policy | `perpetua_core.graph.plugins.interrupt_guard` | ❌ missing (Task 10) |
| **Backend discovery + health probe (v1 → v2 layer)** | `perpetua_tools.discovery` (v1) → `perpetua_core.graph.plugins.backend_discovery` (v2) | ❌ both missing (Tasks 1–4, 13) |

**Tech Stack:** Python 3.11+ · Pydantic v2 · `aiosqlite` · `httpx` (async) · `pytest` · `pytest-asyncio` · `Hypothesis` · `respx` (HTTP mock).

**Companion docs:**
- Spec (port mechanics): `docs/superpowers/specs/2026-05-17-salvage-translation-design.md`
- Spec (asset selection): `docs/superpowers/specs/2026-05-14-salvage-plugins-design.md`
- TDD discipline: `docs/TDD.md` + `superpowers:test-driven-development`

---

## Generation labeling (per Canonical Repo Registry)

Every task in this plan is labeled to one of three generations, and the labels are non-negotiable:

| Label | Meaning | Target repos in this plan |
|---|---|---|
| **v1-legacy** | `diazMelgarejo/*` — current working code; tactical fixes apply here | `diazMelgarejo/Perpetua-Tools` (Track A only) |
| **v2-planning** | `oramasys/*` — forward-looking scaffold; **architectural canon** | `oramasys/perpetua-core`, `oramasys/oramasys` (Tracks B, C, D) |
| **cross-cutting** | Principles, contracts, HITL gates governing both generations | property tests (Track E), this plan doc, LESSONS.md |

**Strategic decomposition (resolves the "build-where" vs. "design-where" tension):**
- The discovery **shape** (`Backend`, `BackendRegistry`, `select_backend`) is a **v2-planning architectural decision**. Its canonical home is `oramasys/perpetua-core/perpetua_core/discovery/`.
- The discovery **first implementation** lands in **v1-legacy** (`diazMelgarejo/Perpetua-Tools/perpetua/discovery/`) per user priority ("improve v1 today").
- **Track D copies v1 → v2 verbatim** (`cp -r`, no drift). The v2 copy is canonical; v1 keeps its working copy until a future plan flips the import direction (v1 imports v2's discovery instead of duplicating).
- **All architectural decisions** (engine shape, plugin contracts, state schema, message wrapper) live in **v2-planning only**. v1-legacy gets forward-looking statements as reference, never structural rewrites.
- **`orama-system`** (this repo) is the cross-cutting coordination/navigation hub. Plans + specs + LESSONS live here; code does not. The repo is technically `diazMelgarejo/orama-system` (v1-legacy) but its `docs/` folder serves all three generations.

**Push policy (per generation):**
- v1-legacy (`Perpetua-Tools`): local branch, **do not push** until user reviews end-to-end on Mac+Win.
- v2-planning (`perpetua-core`, `oramasys`): local branches, **do not push** until full regression green AND user approves the dispatch wiring change.
- cross-cutting (`orama-system/docs/`): push the plan, spec, and LESSONS append immediately — those are navigation, not code.

**Hard rules:**
- ALL canonical changes go to `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/` on local branch `feat/salvage-plugins-rc1`. **Do NOT push** until full regression green.
- ALL v1 changes go to `/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools/` on local branch `feat/ip-aware-discovery`.
- v2 `oramasys/oramasys` dispatch wiring goes on local branch `feat/dispatch-discovery-bridge`.
- Every task: failing test first, watch it fail, then code. No exceptions.
- Commit per task. PROGRESS.md updated per task (claim → done).

**Hardware reality (verified 2026-05-17):**
- Mac: Ollama `localhost:11434` + LM Studio `localhost:1234` (if running)
- Windows rig: LM Studio at `192.168.254.103:1234` (RTX 3080)
- Optional cloud: OpenRouter via env var

---

## File map (with generation labels)

### `oramasys/perpetua-core` — **v2-planning** (`/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/`)

| Action | Path | Purpose |
|---|---|---|
| Modify | `perpetua_core/graph/engine.py` | Add `set_entry()`, `compile()`, `max_steps` guard |
| Create | `perpetua_core/graph/plugins/routing.py` | ConditionalEdge label registry |
| Create | `perpetua_core/graph/plugins/tool_node.py` | CLI subprocess node wrapper |
| Create | `perpetua_core/graph/plugins/validator.py` | Pre/post node validation |
| Create | `perpetua_core/graph/plugins/interrupt_guard.py` | Merge-vs-drop interrupt policy |
| Create | `perpetua_core/graph/plugins/parallel.py` | `Send()` fan-out for parallel dispatch |
| Create | `perpetua_core/message.py` | Typed `ChatMessage` wrapper (closes OQ17) |
| Create | `tests/graph/test_engine_max_steps.py` | Cycle guard |
| Create | `tests/graph/test_engine_compile.py` | `set_entry`/`compile` |
| Create | `tests/graph/plugins/test_routing.py` | Label registry |
| Create | `tests/graph/plugins/test_tool_node.py` | Subprocess wrapper |
| Create | `tests/graph/plugins/test_validator.py` | Validation gate |
| Create | `tests/graph/plugins/test_interrupt_guard.py` | Interrupt policy |
| Create | `tests/graph/plugins/test_parallel.py` | Fan-out + merge |
| Create | `tests/property/test_engine_invariants.py` | Hypothesis property tests |
| Create | `PROGRESS.md` | Multi-agent coordination ledger |

### `diazMelgarejo/Perpetua-Tools` — **v1-legacy** (`/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools/`)

| Action | Path | Purpose |
|---|---|---|
| Create | `perpetua/discovery/__init__.py` | Discovery package |
| Create | `perpetua/discovery/backend.py` | `Backend` dataclass — `(name, base_url, kind, models, health, last_seen)` |
| Create | `perpetua/discovery/probe.py` | Async `health_probe(base_url)` → `BackendHealth` |
| Create | `perpetua/discovery/registry.py` | `BackendRegistry` — autodetect + direct-IP register, validates health |
| Create | `perpetua/discovery/selector.py` | `select_backend(*, model_hint, task_type, target_tier)` |
| Modify | `orchestrator/agent_launcher.py` | Use `BackendRegistry.select()` instead of hardcoded URLs |
| Create | `tests/discovery/test_probe.py` | Health probe with `respx` |
| Create | `tests/discovery/test_registry.py` | Autodetect, direct-IP, eviction |
| Create | `tests/discovery/test_selector.py` | Routing rules |

### `oramasys/oramasys` — **v2-planning** (`/Users/lawrencecyremelgarejo/Documents/oramasys/oramasys/`)

| Action | Path | Purpose |
|---|---|---|
| Modify | `orama/graph/perpetua_graph.py` | Wire `dispatch_node` to `BackendRegistry` (via perpetua-core bridge plugin) |
| Create | `perpetua_core_bridge/discovery_adapter.py` *(in perpetua-core)* | Adapter so v2 plugin uses same shapes as v1 |
| Create | `tests/test_dispatch_with_discovery.py` | End-to-end: route → discover → dispatch |

---

## Task 0 — Branches + PROGRESS.md scaffolding (coordination ledger)

**Why:** Per spec §5, every salvage task is claimed in `PROGRESS.md` before work starts so concurrent Codex/Gemini agents don't collide on the same file.

**Files:**
- Create: `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/PROGRESS.md`

- [ ] **Step 1: Create local branches (do NOT push)**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core && git checkout -b feat/salvage-plugins-rc1
cd /Users/lawrencecyremelgarejo/Documents/Terminal\ xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools && git checkout -b feat/ip-aware-discovery
cd /Users/lawrencecyremelgarejo/Documents/oramasys/oramasys && git checkout -b feat/dispatch-discovery-bridge
```

- [ ] **Step 2: Write PROGRESS.md**

```markdown
# Salvage Translation Progress — RC-1

| # | Task | Owner | Status | Claimed | Done | Commit |
|---|------|-------|--------|---------|------|--------|
| 1 | discovery/backend.py | _unclaimed_ | TODO | | | |
| 2 | discovery/probe.py | _unclaimed_ | TODO | | | |
| 3 | discovery/registry.py | _unclaimed_ | TODO | | | |
| 4 | discovery/selector.py | _unclaimed_ | TODO | | | |
| 5 | engine: max_steps guard | _unclaimed_ | TODO | | | |
| 6 | engine: set_entry + compile | _unclaimed_ | TODO | | | |
| 7 | plugin: routing | _unclaimed_ | TODO | | | |
| 8 | plugin: tool_node | _unclaimed_ | TODO | | | |
| 9 | plugin: validator | _unclaimed_ | TODO | | | |
| 10 | plugin: interrupt_guard | _unclaimed_ | TODO | | | |
| 11 | plugin: parallel (Send) | _unclaimed_ | TODO | | | |
| 12 | message.py typed wrapper | _unclaimed_ | TODO | | | |
| 13 | bridge: discovery_adapter | _unclaimed_ | TODO | | | |
| 14 | wire agent_launcher.py | _unclaimed_ | TODO | | | |
| 15 | wire dispatch_node | _unclaimed_ | TODO | | | |
| 16 | property tests | _unclaimed_ | TODO | | | |

## Claim protocol

1. Edit this row: set Owner to your agent name + Status to CLAIMED.
2. Commit immediately: `chore(progress): claim task N (<agent>)`.
3. If another agent already claimed: pick another row.
4. On completion: Status DONE, fill Commit SHA, push the work commit.
```

- [ ] **Step 3: Commit ledger**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
git add PROGRESS.md
git commit -m "chore: PROGRESS.md ledger for salvage-plugins-rc1"
```

---

## TRACK A — v1-legacy IP-aware backend discovery (Perpetua-Tools)

**Generation:** **v1-legacy** (`diazMelgarejo/Perpetua-Tools`) — tactical fix.
**Architectural status:** shapes are **v2-planning canon**, first-implemented here per user priority. Track D copies them verbatim to v2.
**Lands first. Immediately useful. Zero drift from the shape that ships in v2.**

### Task 1 — `discovery/backend.py` (data shapes)

**Files:**
- Create: `perpetua/discovery/__init__.py`
- Create: `perpetua/discovery/backend.py`
- Create: `tests/discovery/__init__.py`
- Create: `tests/discovery/test_backend.py`

- [ ] **Step 1: Failing test**

`tests/discovery/test_backend.py`:
```python
from datetime import datetime, timezone
from perpetua.discovery.backend import Backend, BackendKind, BackendHealth


def test_backend_holds_identity_and_health():
    b = Backend(
        name="lmstudio-win",
        base_url="http://192.168.254.103:1234/v1",
        kind=BackendKind.LMSTUDIO,
        models=("qwen3-coder-30b",),
        health=BackendHealth.UNKNOWN,
        last_seen=None,
    )
    assert b.is_targetable_by_ip("192.168.254.103")
    assert not b.is_targetable_by_ip("10.0.0.5")
    assert b.with_health(BackendHealth.ONLINE, now=datetime.now(timezone.utc)).health is BackendHealth.ONLINE
```

- [ ] **Step 2: Watch it fail**

```bash
cd /Users/lawrencecyremelgarejo/Documents/Terminal\ xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools
pytest tests/discovery/test_backend.py -v
```
Expected: `ModuleNotFoundError: No module named 'perpetua.discovery'`.

- [ ] **Step 3: Implement**

`perpetua/discovery/__init__.py`:
```python
"""Backend discovery + health-aware selection (v1; ports to v2 plugin)."""
```

`perpetua/discovery/backend.py`:
```python
from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse


class BackendKind(str, Enum):
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    OPENROUTER = "openrouter"


class BackendHealth(str, Enum):
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class Backend:
    name: str
    base_url: str
    kind: BackendKind
    models: tuple[str, ...] = field(default_factory=tuple)
    health: BackendHealth = BackendHealth.UNKNOWN
    last_seen: datetime | None = None

    @property
    def host(self) -> str:
        return urlparse(self.base_url).hostname or ""

    def is_targetable_by_ip(self, ip: str) -> bool:
        return self.host == ip

    def with_health(self, health: BackendHealth, *, now: datetime) -> "Backend":
        return replace(self, health=health, last_seen=now)
```

- [ ] **Step 4: Test passes**

```bash
pytest tests/discovery/test_backend.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add perpetua/discovery/ tests/discovery/
git commit -m "feat(discovery): Backend dataclass + health/kind enums (Task 1)"
```

---

### Task 2 — `discovery/probe.py` (async health check)

**Files:**
- Create: `perpetua/discovery/probe.py`
- Create: `tests/discovery/test_probe.py`

Probe rule: an `OpenAI-compat` endpoint is **online** iff `GET {base_url}/models` returns 200 within 1.5s and the body parses as JSON with a `data` array (LM Studio + Ollama both expose this; OpenRouter as well). Otherwise **offline**. Network error within budget → **offline**.

- [ ] **Step 1: Failing test**

`tests/discovery/test_probe.py`:
```python
import pytest, respx, httpx
from perpetua.discovery.backend import BackendHealth
from perpetua.discovery.probe import health_probe


@pytest.mark.asyncio
@respx.mock
async def test_probe_returns_online_when_models_endpoint_serves_200():
    respx.get("http://192.168.254.103:1234/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3-coder-30b"}]})
    )
    result = await health_probe("http://192.168.254.103:1234/v1")
    assert result.health is BackendHealth.ONLINE
    assert "qwen3-coder-30b" in result.models


@pytest.mark.asyncio
@respx.mock
async def test_probe_returns_offline_when_endpoint_404s():
    respx.get("http://192.168.254.103:1234/v1/models").mock(return_value=httpx.Response(404))
    result = await health_probe("http://192.168.254.103:1234/v1")
    assert result.health is BackendHealth.OFFLINE


@pytest.mark.asyncio
@respx.mock
async def test_probe_returns_offline_on_connection_error():
    respx.get("http://10.0.0.99:1234/v1/models").mock(side_effect=httpx.ConnectError("nope"))
    result = await health_probe("http://10.0.0.99:1234/v1")
    assert result.health is BackendHealth.OFFLINE
```

- [ ] **Step 2: Watch it fail**

```bash
pytest tests/discovery/test_probe.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement**

`perpetua/discovery/probe.py`:
```python
from __future__ import annotations
from dataclasses import dataclass
import httpx
from .backend import BackendHealth

_TIMEOUT_S = 1.5


@dataclass(frozen=True, slots=True)
class ProbeResult:
    health: BackendHealth
    models: tuple[str, ...]


async def health_probe(base_url: str, *, timeout: float = _TIMEOUT_S) -> ProbeResult:
    url = base_url.rstrip("/") + "/models"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
        return ProbeResult(BackendHealth.OFFLINE, ())
    if r.status_code != 200:
        return ProbeResult(BackendHealth.OFFLINE, ())
    try:
        body = r.json()
        models = tuple(item["id"] for item in body.get("data", []) if "id" in item)
    except (ValueError, KeyError, TypeError):
        return ProbeResult(BackendHealth.DEGRADED, ())
    return ProbeResult(BackendHealth.ONLINE, models)
```

- [ ] **Step 4: Test passes**

```bash
pytest tests/discovery/test_probe.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add perpetua/discovery/probe.py tests/discovery/test_probe.py
git commit -m "feat(discovery): async health_probe with 1.5s budget (Task 2)"
```

---

### Task 3 — `discovery/registry.py` (autodetect + direct-IP register)

**Behavior:** `BackendRegistry.autodetect()` probes a fixed seed list (`localhost:11434`, `localhost:1234`, `192.168.254.103:1234`). `register_by_ip(ip, port, kind)` adds an explicit backend and probes it before admission — if offline, raises `BackendOfflineError` so the caller knows immediately. Registry is in-memory; persistence is out of scope here.

**Files:**
- Create: `perpetua/discovery/registry.py`
- Create: `perpetua/discovery/errors.py`
- Create: `tests/discovery/test_registry.py`

- [ ] **Step 1: Failing test**

`tests/discovery/test_registry.py`:
```python
import pytest, respx, httpx
from perpetua.discovery.backend import BackendKind, BackendHealth
from perpetua.discovery.registry import BackendRegistry
from perpetua.discovery.errors import BackendOfflineError


@pytest.mark.asyncio
@respx.mock
async def test_autodetect_keeps_only_responsive_seeds():
    respx.get("http://localhost:11434/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3.5:9b-nvfp4"}]}))
    respx.get("http://localhost:1234/v1/models").mock(return_value=httpx.Response(404))
    respx.get("http://192.168.254.103:1234/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3-coder-30b"}]}))

    reg = BackendRegistry()
    await reg.autodetect()
    online = [b.name for b in reg.online()]
    assert "ollama-local" in online
    assert "lmstudio-win" in online
    assert "lmstudio-mac" not in online


@pytest.mark.asyncio
@respx.mock
async def test_register_by_ip_admits_only_when_probe_succeeds():
    respx.get("http://192.168.254.103:1234/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3-coder-30b"}]}))
    reg = BackendRegistry()
    b = await reg.register_by_ip("192.168.254.103", 1234, BackendKind.LMSTUDIO, name="win-rig")
    assert b.health is BackendHealth.ONLINE
    assert reg.find("win-rig") is b


@pytest.mark.asyncio
@respx.mock
async def test_register_by_ip_raises_when_offline():
    respx.get("http://10.0.0.99:1234/v1/models").mock(side_effect=httpx.ConnectError("nope"))
    reg = BackendRegistry()
    with pytest.raises(BackendOfflineError):
        await reg.register_by_ip("10.0.0.99", 1234, BackendKind.LMSTUDIO)
```

- [ ] **Step 2: Watch it fail**

```bash
pytest tests/discovery/test_registry.py -v
```

- [ ] **Step 3: Implement**

`perpetua/discovery/errors.py`:
```python
class BackendOfflineError(RuntimeError):
    """Raised when register_by_ip probe fails — caller chose this backend explicitly."""
```

`perpetua/discovery/registry.py`:
```python
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from .backend import Backend, BackendKind, BackendHealth
from .errors import BackendOfflineError
from .probe import health_probe

# Seed list for autodetect. Pure data — extend without code changes elsewhere.
_SEEDS: tuple[tuple[str, str, BackendKind], ...] = (
    ("ollama-local", "http://localhost:11434/v1", BackendKind.OLLAMA),
    ("lmstudio-mac", "http://localhost:1234/v1", BackendKind.LMSTUDIO),
    ("lmstudio-win", "http://192.168.254.103:1234/v1", BackendKind.LMSTUDIO),
)


class BackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, Backend] = {}

    def all(self) -> list[Backend]:
        return list(self._backends.values())

    def online(self) -> list[Backend]:
        return [b for b in self._backends.values() if b.health is BackendHealth.ONLINE]

    def find(self, name: str) -> Backend | None:
        return self._backends.get(name)

    async def autodetect(self) -> list[Backend]:
        results = await asyncio.gather(
            *(self._probe_and_record(name, url, kind) for name, url, kind in _SEEDS),
            return_exceptions=False,
        )
        return [b for b in results if b is not None]

    async def register_by_ip(
        self, ip: str, port: int, kind: BackendKind, *, name: str | None = None
    ) -> Backend:
        url = f"http://{ip}:{port}/v1"
        name = name or f"{kind.value}-{ip}"
        backend = await self._probe_and_record(name, url, kind)
        if backend is None or backend.health is not BackendHealth.ONLINE:
            raise BackendOfflineError(f"{name} @ {url} did not respond")
        return backend

    async def _probe_and_record(self, name: str, url: str, kind: BackendKind) -> Backend | None:
        probe = await health_probe(url)
        now = datetime.now(timezone.utc)
        backend = Backend(
            name=name, base_url=url, kind=kind, models=probe.models,
            health=probe.health, last_seen=now,
        )
        if probe.health is BackendHealth.ONLINE:
            self._backends[name] = backend
        return backend
```

- [ ] **Step 4: Test passes**

```bash
pytest tests/discovery/test_registry.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add perpetua/discovery/errors.py perpetua/discovery/registry.py tests/discovery/test_registry.py
git commit -m "feat(discovery): BackendRegistry autodetect + register_by_ip with probe (Task 3)"
```

---

### Task 4 — `discovery/selector.py` (routing rules)

**Routing rules (tight, like the CSV concept map):**

| Input | Selection rule |
|---|---|
| `target_tier="mac"` | Prefer Ollama, then LM Studio Mac |
| `target_tier="windows"` | Require LM Studio Win |
| `target_tier="shared"` + `task_type="coding"` | Win-first (RTX 3080), fallback Mac |
| `target_tier="shared"` + `task_type="reasoning"` | Mac-first (qwen3.5:9b-nvfp4), fallback Win |
| `model_hint="X"` | First backend whose `models` contains X, regardless of tier |
| Direct IP given by caller | Use that one only (registered via `register_by_ip` first) |
| Nothing matches | Raise `NoBackendAvailableError` |

**Files:**
- Create: `perpetua/discovery/selector.py`
- Modify: `perpetua/discovery/errors.py`
- Create: `tests/discovery/test_selector.py`

- [ ] **Step 1: Failing test**

`tests/discovery/test_selector.py`:
```python
import pytest
from datetime import datetime, timezone
from perpetua.discovery.backend import Backend, BackendKind, BackendHealth
from perpetua.discovery.registry import BackendRegistry
from perpetua.discovery.selector import select_backend
from perpetua.discovery.errors import NoBackendAvailableError

NOW = datetime.now(timezone.utc)

def _online(name, url, kind, models):
    return Backend(name, url, kind, tuple(models), BackendHealth.ONLINE, NOW)


@pytest.fixture
def reg():
    r = BackendRegistry()
    r._backends["ollama-local"] = _online("ollama-local", "http://localhost:11434/v1",
                                          BackendKind.OLLAMA, ["qwen3.5:9b-nvfp4"])
    r._backends["lmstudio-win"] = _online("lmstudio-win", "http://192.168.254.103:1234/v1",
                                          BackendKind.LMSTUDIO, ["qwen3-coder-30b"])
    return r


def test_model_hint_wins_over_tier(reg):
    b = select_backend(reg, model_hint="qwen3-coder-30b", task_type="reasoning", target_tier="mac")
    assert b.name == "lmstudio-win"


def test_coding_on_shared_prefers_windows(reg):
    b = select_backend(reg, model_hint=None, task_type="coding", target_tier="shared")
    assert b.name == "lmstudio-win"


def test_reasoning_on_shared_prefers_mac(reg):
    b = select_backend(reg, model_hint=None, task_type="reasoning", target_tier="shared")
    assert b.name == "ollama-local"


def test_no_match_raises(reg):
    reg._backends.clear()
    with pytest.raises(NoBackendAvailableError):
        select_backend(reg, model_hint=None, task_type="coding", target_tier="shared")
```

- [ ] **Step 2: Watch it fail**

```bash
pytest tests/discovery/test_selector.py -v
```

- [ ] **Step 3: Implement**

Append to `perpetua/discovery/errors.py`:
```python


class NoBackendAvailableError(RuntimeError):
    """No registered backend satisfies the given routing constraints."""
```

`perpetua/discovery/selector.py`:
```python
from __future__ import annotations
from typing import Literal
from .backend import Backend, BackendKind, BackendHealth
from .registry import BackendRegistry
from .errors import NoBackendAvailableError

TaskType = Literal["coding", "reasoning", "research", "ops"]
Tier = Literal["mac", "windows", "shared"]

# Static preference table. Order matters: first match wins.
_TIER_PREF: dict[tuple[Tier, TaskType], tuple[BackendKind, ...]] = {
    ("mac",     "coding"):    (BackendKind.OLLAMA, BackendKind.LMSTUDIO),
    ("mac",     "reasoning"): (BackendKind.OLLAMA, BackendKind.LMSTUDIO),
    ("windows", "coding"):    (BackendKind.LMSTUDIO,),
    ("windows", "reasoning"): (BackendKind.LMSTUDIO,),
    ("shared",  "coding"):    (BackendKind.LMSTUDIO, BackendKind.OLLAMA),  # win-first
    ("shared",  "reasoning"): (BackendKind.OLLAMA, BackendKind.LMSTUDIO),  # mac-first
    ("shared",  "research"):  (BackendKind.LMSTUDIO, BackendKind.OLLAMA),
    ("shared",  "ops"):       (BackendKind.OLLAMA, BackendKind.LMSTUDIO),
}

# Tier-specific kinds (for hosting-machine match).
_TIER_HOSTS: dict[Tier, set[str]] = {
    "mac":     {"ollama-local", "lmstudio-mac"},
    "windows": {"lmstudio-win"},
    "shared":  set(),  # any
}


def select_backend(
    registry: BackendRegistry,
    *,
    model_hint: str | None,
    task_type: TaskType,
    target_tier: Tier,
) -> Backend:
    online = registry.online()

    # 1. model_hint always wins
    if model_hint:
        for b in online:
            if model_hint in b.models:
                return b

    # 2. tier-constrained candidates
    tier_hosts = _TIER_HOSTS[target_tier]
    candidates = [b for b in online if not tier_hosts or b.name in tier_hosts]

    # 3. apply kind preference order
    prefs = _TIER_PREF.get((target_tier, task_type), (BackendKind.OLLAMA, BackendKind.LMSTUDIO))
    for kind in prefs:
        for b in candidates:
            if b.kind is kind:
                return b

    raise NoBackendAvailableError(
        f"No online backend matches tier={target_tier} task={task_type} hint={model_hint}"
    )
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/discovery/ -v
```
Expected: 10 passed (3 backend + 3 probe + 3 registry + 4 selector — wait, fix: 1 + 3 + 3 + 4 = 11).

- [ ] **Step 5: Commit**

```bash
git add perpetua/discovery/selector.py perpetua/discovery/errors.py tests/discovery/test_selector.py
git commit -m "feat(discovery): selector with tier+task routing table (Task 4)"
```

---

### Task 4b — Wire `agent_launcher.py` to use the registry

**Files:**
- Modify: `orchestrator/agent_launcher.py`
- Create: `tests/test_agent_launcher_uses_registry.py`

**Concept:** `agent_launcher.launch_agent(spec)` previously read hardcoded `LMSTUDIO_WIN_URL` env vars. Now it asks the registry. Backwards-compat: if `spec.base_url_override` is set, use it directly (caller knows best).

- [ ] **Step 1: Read current agent_launcher to find dispatch site**

```bash
cd /Users/lawrencecyremelgarejo/Documents/Terminal\ xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools
grep -n "base_url\|LMSTUDIO\|OLLAMA_BASE" orchestrator/agent_launcher.py
```

- [ ] **Step 2: Failing test**

`tests/test_agent_launcher_uses_registry.py`:
```python
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from perpetua.discovery.backend import Backend, BackendKind, BackendHealth
from perpetua.discovery.registry import BackendRegistry
from orchestrator.agent_launcher import resolve_backend_for_spec


@pytest.mark.asyncio
async def test_launcher_uses_registry_selection():
    reg = BackendRegistry()
    reg._backends["lmstudio-win"] = Backend(
        "lmstudio-win", "http://192.168.254.103:1234/v1", BackendKind.LMSTUDIO,
        ("qwen3-coder-30b",), BackendHealth.ONLINE, datetime.now(timezone.utc),
    )
    spec = {"task_type": "coding", "target_tier": "shared", "model_hint": None,
            "base_url_override": None}
    backend = resolve_backend_for_spec(reg, spec)
    assert backend.base_url == "http://192.168.254.103:1234/v1"
```

- [ ] **Step 3: Watch it fail**

- [ ] **Step 4: Implement** — append to `orchestrator/agent_launcher.py`:

```python
# --- IP-aware backend resolution (added 2026-05-17, Task 4b) ---
from perpetua.discovery.registry import BackendRegistry
from perpetua.discovery.selector import select_backend
from perpetua.discovery.backend import Backend


def resolve_backend_for_spec(registry: BackendRegistry, spec: dict) -> Backend:
    """Resolve a launch spec to a concrete Backend.
    Honors spec['base_url_override'] for caller-forced direct-IP selection.
    Otherwise consults the registry's selector.
    """
    override = spec.get("base_url_override")
    if override:
        for b in registry.all():
            if b.base_url == override:
                return b
        # Caller forced a URL we don't know about — synthesize an unverified Backend.
        return Backend(name="adhoc", base_url=override,
                       kind=spec.get("kind", "lmstudio"),  # type: ignore[arg-type]
                       models=(), health="unknown", last_seen=None)  # type: ignore[arg-type]
    return select_backend(
        registry,
        model_hint=spec.get("model_hint"),
        task_type=spec.get("task_type", "reasoning"),
        target_tier=spec.get("target_tier", "shared"),
    )
```

- [ ] **Step 5: Test passes**

```bash
pytest tests/test_agent_launcher_uses_registry.py -v
```

- [ ] **Step 6: Commit**

```bash
git add orchestrator/agent_launcher.py tests/test_agent_launcher_uses_registry.py
git commit -m "feat(launcher): resolve_backend_for_spec via discovery registry (Task 4b)"
```

---

## TRACK B — v2-planning engine improvements (`oramasys/perpetua-core`)

**Generation:** **v2-planning** — architectural decisions; never back-ported to v1-legacy.

**Switch repos:**
```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
git checkout feat/salvage-plugins-rc1
# Claim Task 5 in PROGRESS.md before starting.
```

### Task 5 — Engine: `max_steps` cycle guard

**Why:** LangGraph's loop concept requires a safety net. Without it, a conditional edge that loops back to an earlier node can run forever. Per `docs/v2/15-phase1-as-built.md`, this is an explicit Phase 2 gap (OQ12). The canonical engine in `perpetua_core/graph/engine.py` does not yet have it.

**Files:**
- Modify: `perpetua_core/graph/engine.py`
- Create: `tests/graph/test_engine_max_steps.py`

- [ ] **Step 1: Failing test**

`tests/graph/test_engine_max_steps.py`:
```python
import pytest
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.engine import MiniGraph, START, END, MaxStepsExceeded


@pytest.mark.asyncio
async def test_max_steps_guard_breaks_infinite_loop():
    g = MiniGraph(max_steps=5)
    g.add_node("a", lambda s: {"scratchpad": {"hits": s.scratchpad.get("hits", 0) + 1}})
    g.add_edge(START, "a")
    g.add_edge("a", lambda s: "a")  # loops forever absent the guard
    with pytest.raises(MaxStepsExceeded) as exc:
        await g.ainvoke(PerpetuaState(session_id="t1"))
    assert exc.value.steps == 5


@pytest.mark.asyncio
async def test_default_max_steps_is_generous_enough_for_typical_graphs():
    # A bounded 3-node graph must complete with the default cap.
    g = MiniGraph()
    g.add_node("a", lambda s: {"scratchpad": {"step": "a"}})
    g.add_node("b", lambda s: {"scratchpad": {"step": "b"}})
    g.add_node("c", lambda s: {"scratchpad": {"step": "c"}})
    g.add_edge(START, "a"); g.add_edge("a", "b"); g.add_edge("b", "c"); g.add_edge("c", END)
    result = await g.ainvoke(PerpetuaState(session_id="t1"))
    assert result.status == "done"
```

- [ ] **Step 2: Watch it fail**

```bash
pytest tests/graph/test_engine_max_steps.py -v
```
Expected: `ImportError: cannot import name 'MaxStepsExceeded'`.

- [ ] **Step 3: Implement** — modify `perpetua_core/graph/engine.py`:

Replace the top of the file (above `class MiniGraph`) and the `__init__` + `ainvoke` methods. Show the diff intent:

```python
"""
MiniGraph — ~80-line state-machine kernel with cycle guard.

Nodes: async callables (state) -> dict
Edges: str (static) or callable (state) -> str (conditional)
No optional dependencies. No plugin imports.
"""
from __future__ import annotations
import asyncio
from typing import Callable

from perpetua_core.state import PerpetuaState

START = "__start__"
END = "__end__"
_DEFAULT_MAX_STEPS = 200  # generous; cycles still trip well before runaway

NodeFn = Callable[[PerpetuaState], object]
EdgeFn = Callable[[PerpetuaState], str]


class MaxStepsExceeded(RuntimeError):
    def __init__(self, steps: int, last_node: str):
        super().__init__(f"MiniGraph exceeded max_steps={steps} (last node: {last_node})")
        self.steps = steps
        self.last_node = last_node


class MiniGraph:
    def __init__(self, *, interrupt_handler: str | None = None,
                 max_steps: int = _DEFAULT_MAX_STEPS):
        self._nodes: dict[str, NodeFn] = {}
        self._edges: dict[str, str | EdgeFn] = {}
        self._interrupt_handler = interrupt_handler
        self._max_steps = max_steps

    def add_node(self, name: str, fn: NodeFn) -> "MiniGraph":
        self._nodes[name] = fn
        return self

    def add_edge(self, src: str, dst: str | EdgeFn) -> "MiniGraph":
        self._edges[src] = dst
        return self

    async def ainvoke(self, state: PerpetuaState) -> PerpetuaState:
        node = self._edges.get(START, END)
        if callable(node):
            node = node(state)

        steps = 0
        last = node
        while node and node != END:
            steps += 1
            if steps > self._max_steps:
                raise MaxStepsExceeded(self._max_steps, last)
            last = node
            state = state.merge({"nodes_visited": [*state.nodes_visited, node]})
            fn = self._nodes[node]
            try:
                delta = await fn(state) if asyncio.iscoroutinefunction(fn) else fn(state)
            except Exception as exc:
                if _is_interrupt(exc):
                    return state.merge({
                        "status": "interrupted",
                        "metadata": {
                            **state.metadata,
                            "interrupt_prompt": exc.prompt,       # type: ignore[attr-defined]
                            "interrupt_payload": exc.payload,     # type: ignore[attr-defined]
                            "interrupt_node": node,
                        },
                    })
                raise
            state = state.merge(delta)
            edge = self._edges.get(node, END)
            node = edge(state) if callable(edge) else edge

        return state.merge({"status": "done"})


def _is_interrupt(exc: Exception) -> bool:
    return type(exc).__name__ == "Interrupt" and hasattr(exc, "prompt")
```

- [ ] **Step 4: Tests pass + existing engine tests still green**

```bash
pytest tests/graph/test_engine_max_steps.py -v
pytest tests/ -v  # full canonical suite (32 prior + new)
```

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/engine.py tests/graph/test_engine_max_steps.py
git commit -m "feat(engine): max_steps cycle guard, default 200, raises MaxStepsExceeded (Task 5)"
```

---

### Task 6 — Engine: `set_entry()` + `compile()` convenience

**Why:** LangGraph parity. Callers expect `graph.set_entry_point("node")` and `compiled = graph.compile()`. Today they must use `add_edge(START, "node")`. Compile freezes the graph and offers a single object whose `.ainvoke()` is the public surface (mirrors `CompiledGraph` in the wrong-repo's `engine.py`).

**Files:**
- Modify: `perpetua_core/graph/engine.py`
- Create: `tests/graph/test_engine_compile.py`

- [ ] **Step 1: Failing test**

`tests/graph/test_engine_compile.py`:
```python
import pytest
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.engine import MiniGraph, END


@pytest.mark.asyncio
async def test_set_entry_is_equivalent_to_add_edge_from_start():
    g = MiniGraph()
    g.add_node("a", lambda s: {"scratchpad": {"x": 1}})
    g.set_entry("a")
    g.add_edge("a", END)
    state = await g.ainvoke(PerpetuaState(session_id="t1"))
    assert state.scratchpad["x"] == 1


@pytest.mark.asyncio
async def test_compile_returns_frozen_graph_with_ainvoke():
    g = MiniGraph()
    g.add_node("a", lambda s: {"scratchpad": {"x": 1}})
    g.set_entry("a")
    g.add_edge("a", END)
    compiled = g.compile()
    state = await compiled.ainvoke(PerpetuaState(session_id="t1"))
    assert state.scratchpad["x"] == 1
    # compile() must return a distinct object — not the same MiniGraph (freezes mutation)
    assert compiled is not g
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement** — append to `perpetua_core/graph/engine.py`:

```python


    def set_entry(self, node: str) -> "MiniGraph":
        return self.add_edge(START, node)

    def compile(self) -> "CompiledGraph":
        return CompiledGraph(dict(self._nodes), dict(self._edges),
                             self._interrupt_handler, self._max_steps)


class CompiledGraph:
    """Frozen MiniGraph. Mutation methods are not present."""
    def __init__(self, nodes: dict, edges: dict, interrupt_handler: str | None, max_steps: int):
        # Reuse MiniGraph.ainvoke logic by constructing an internal graph.
        self._inner = MiniGraph(interrupt_handler=interrupt_handler, max_steps=max_steps)
        for n, fn in nodes.items():
            self._inner.add_node(n, fn)
        for src, dst in edges.items():
            self._inner.add_edge(src, dst)

    async def ainvoke(self, state: PerpetuaState) -> PerpetuaState:
        return await self._inner.ainvoke(state)
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/graph/test_engine_compile.py -v
pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/engine.py tests/graph/test_engine_compile.py
git commit -m "feat(engine): set_entry() + compile() → CompiledGraph (Task 6)"
```

---

---

## TRACK C — v2-planning new plugins (`oramasys/perpetua-core/perpetua_core/graph/plugins/`)

**Generation:** **v2-planning** — plugin contracts are architectural; never back-ported to v1-legacy. Each plugin is independent; Tasks 7–12 can be parallelized via subagent dispatch.

### Task 7 — Plugin: `routing` (conditional edge label registry)

**Why:** Conditional edges today require an inline lambda. The wrong-repo `ConditionalEdge` exposed a label registry: `route(state) -> "label"` then `register("label", "node_name")`. That decouples policy (which branch) from topology (which node implements it). Salvageable.

**Files:**
- Create: `perpetua_core/graph/plugins/routing.py`
- Create: `tests/graph/plugins/__init__.py`
- Create: `tests/graph/plugins/test_routing.py`

- [ ] **Step 1: Failing test**

`tests/graph/plugins/test_routing.py`:
```python
import pytest
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.engine import MiniGraph, END
from perpetua_core.graph.plugins.routing import LabelRouter


@pytest.mark.asyncio
async def test_label_router_dispatches_to_registered_node():
    router = LabelRouter(lambda s: "fast" if s.optimize_for == "speed" else "deep")
    router.register("fast", "fast_node")
    router.register("deep", "deep_node")

    g = MiniGraph()
    g.add_node("entry", lambda s: {"scratchpad": {"hit": "entry"}})
    g.add_node("fast_node", lambda s: {"scratchpad": {**s.scratchpad, "hit": "fast"}})
    g.add_node("deep_node", lambda s: {"scratchpad": {**s.scratchpad, "hit": "deep"}})
    g.set_entry("entry")
    g.add_edge("entry", router.as_edge())
    g.add_edge("fast_node", END)
    g.add_edge("deep_node", END)

    state = await g.ainvoke(PerpetuaState(session_id="t1", optimize_for="speed"))
    assert state.scratchpad["hit"] == "fast"


def test_router_raises_on_unregistered_label():
    router = LabelRouter(lambda s: "unknown")
    with pytest.raises(KeyError, match="unknown"):
        router.as_edge()(PerpetuaState(session_id="t1"))
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/graph/plugins/routing.py`:
```python
"""LabelRouter — separates branch-policy (label) from topology (target node)."""
from __future__ import annotations
from typing import Callable
from perpetua_core.state import PerpetuaState

PolicyFn = Callable[[PerpetuaState], str]


class LabelRouter:
    def __init__(self, policy: PolicyFn):
        self._policy = policy
        self._labels: dict[str, str] = {}

    def register(self, label: str, node: str) -> "LabelRouter":
        self._labels[label] = node
        return self

    def as_edge(self) -> Callable[[PerpetuaState], str]:
        def edge(state: PerpetuaState) -> str:
            label = self._policy(state)
            if label not in self._labels:
                raise KeyError(f"LabelRouter: no node registered for label {label!r}")
            return self._labels[label]
        return edge
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/graph/plugins/test_routing.py -v
```

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/plugins/routing.py tests/graph/plugins/__init__.py tests/graph/plugins/test_routing.py
git commit -m "feat(plugins): LabelRouter for decoupled conditional edges (Task 7)"
```

---

### Task 8 — Plugin: `tool_node` (CLI subprocess wrapper as a node)

**Why:** The wrong-repo's `ToolNode` wrapped subprocess calls (e.g., codex/gemini CLI) as a graph node. Existing `tool.py` is the `@tool` decorator for in-process function calls — different concern. We need both. Idiomatic translation: `subprocess.run` → `asyncio.create_subprocess_exec` (matches canonical's all-async stance).

**Files:**
- Create: `perpetua_core/graph/plugins/tool_node.py`
- Create: `tests/graph/plugins/test_tool_node.py`

- [ ] **Step 1: Failing test**

`tests/graph/plugins/test_tool_node.py`:
```python
import pytest
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.plugins.tool_node import ToolNode, ToolNodeError


@pytest.mark.asyncio
async def test_tool_node_captures_stdout():
    node = ToolNode(argv=["bash", "-c", "echo hello-from-tool"], output_key="cli_out")
    delta = await node(PerpetuaState(session_id="t1"))
    assert delta["scratchpad"]["cli_out"] == "hello-from-tool"


@pytest.mark.asyncio
async def test_tool_node_raises_on_nonzero_exit():
    node = ToolNode(argv=["bash", "-c", "exit 7"], output_key="cli_out")
    with pytest.raises(ToolNodeError) as exc:
        await node(PerpetuaState(session_id="t1"))
    assert exc.value.returncode == 7


@pytest.mark.asyncio
async def test_tool_node_supports_argv_templating_from_state():
    node = ToolNode(
        argv_template=["bash", "-c", "echo session={session_id}"],
        output_key="cli_out",
    )
    delta = await node(PerpetuaState(session_id="abc123"))
    assert delta["scratchpad"]["cli_out"] == "session=abc123"
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/graph/plugins/tool_node.py`:
```python
"""ToolNode — wrap a CLI subprocess as a graph node. Idiomatic async."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from perpetua_core.state import PerpetuaState

_TIMEOUT_S = 60.0


class ToolNodeError(RuntimeError):
    def __init__(self, returncode: int, stderr: str):
        super().__init__(f"tool exited {returncode}: {stderr.strip()}")
        self.returncode = returncode
        self.stderr = stderr


@dataclass
class ToolNode:
    argv: list[str] | None = None
    argv_template: list[str] | None = None
    output_key: str = "tool_out"
    timeout: float = _TIMEOUT_S
    env: dict[str, str] = field(default_factory=dict)

    async def __call__(self, state: PerpetuaState) -> dict:
        if self.argv_template:
            argv = [a.format(**state.model_dump()) for a in self.argv_template]
        elif self.argv:
            argv = list(self.argv)
        else:
            raise ValueError("ToolNode requires argv or argv_template")

        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**self._inherited_env(), **self.env} if self.env else None,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise ToolNodeError(-1, "timeout")

        if proc.returncode != 0:
            raise ToolNodeError(proc.returncode, stderr_b.decode("utf-8", errors="replace"))

        return {"scratchpad": {**state.scratchpad,
                               self.output_key: stdout_b.decode("utf-8").strip()}}

    @staticmethod
    def _inherited_env() -> dict[str, str]:
        import os
        return dict(os.environ)
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/graph/plugins/test_tool_node.py -v
```

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/plugins/tool_node.py tests/graph/plugins/test_tool_node.py
git commit -m "feat(plugins): ToolNode async subprocess wrapper (Task 8)"
```

---

### Task 9 — Plugin: `validator` (pre/post node validation gate)

**Why:** The wrong-repo had a node that validated inputs/outputs against a Pydantic schema and short-circuited on failure. Canonical does not. Pattern: wrap any node with `Validated(node, pre=PreSchema, post=PostSchema)`.

**Files:**
- Create: `perpetua_core/graph/plugins/validator.py`
- Create: `tests/graph/plugins/test_validator.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from pydantic import BaseModel, Field
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.plugins.validator import Validated, ValidationError


class HasModelHint(BaseModel):
    model_hint: str = Field(min_length=1)


class HasResponse(BaseModel):
    response: str = Field(min_length=1)


@pytest.mark.asyncio
async def test_validator_passes_state_through_when_valid():
    async def inner(state):
        return {"scratchpad": {**state.scratchpad, "response": "ok"}}
    node = Validated(inner, pre=HasModelHint, post=HasResponse)
    state = PerpetuaState(session_id="t1", model_hint="qwen3-coder-30b")
    delta = await node(state)
    assert delta["scratchpad"]["response"] == "ok"


@pytest.mark.asyncio
async def test_validator_raises_when_precondition_fails():
    async def inner(state):
        return {}
    node = Validated(inner, pre=HasModelHint, post=HasResponse)
    state = PerpetuaState(session_id="t1", model_hint=None)
    with pytest.raises(ValidationError, match="pre"):
        await node(state)


@pytest.mark.asyncio
async def test_validator_raises_when_postcondition_fails():
    async def inner(state):
        return {"scratchpad": {"response": ""}}  # fails post (min_length=1)
    node = Validated(inner, pre=HasModelHint, post=HasResponse)
    state = PerpetuaState(session_id="t1", model_hint="x")
    with pytest.raises(ValidationError, match="post"):
        await node(state)
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/graph/plugins/validator.py`:
```python
"""Validated — pre/post Pydantic validation wrapping any node."""
from __future__ import annotations
import asyncio
from typing import Callable
from pydantic import BaseModel, ValidationError as PydanticValidationError
from perpetua_core.state import PerpetuaState

NodeFn = Callable[[PerpetuaState], object]


class ValidationError(RuntimeError):
    pass


class Validated:
    def __init__(self, inner: NodeFn, *, pre: type[BaseModel] | None = None,
                 post: type[BaseModel] | None = None):
        self._inner = inner
        self._pre = pre
        self._post = post

    async def __call__(self, state: PerpetuaState) -> dict:
        if self._pre:
            try:
                self._pre(**state.model_dump())
            except PydanticValidationError as e:
                raise ValidationError(f"pre: {e}") from e

        fn = self._inner
        delta = await fn(state) if asyncio.iscoroutinefunction(fn) else fn(state)

        if self._post:
            try:
                merged = {**state.scratchpad, **(delta.get("scratchpad") or {})}
                self._post(**merged)
            except PydanticValidationError as e:
                raise ValidationError(f"post: {e}") from e
        return delta
```

- [ ] **Step 4: Tests pass**

```bash
pytest tests/graph/plugins/test_validator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/plugins/validator.py tests/graph/plugins/test_validator.py
git commit -m "feat(plugins): Validated wrapper for pre/post Pydantic gates (Task 9)"
```

---

### Task 10 — Plugin: `interrupt_guard` (merge-vs-drop policy)

**Why:** The wrong-repo had logic deciding whether an interrupt's resumed value should be MERGED into state or REPLACE a specific scratchpad key. Canonical's `interrupts.py` exposes `Interrupt`/`aresume()` but no policy layer. Add it as a thin plugin so callers don't reinvent.

**Files:**
- Create: `perpetua_core/graph/plugins/interrupt_guard.py`
- Create: `tests/graph/plugins/test_interrupt_guard.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.plugins.interrupt_guard import resume_policy, ResumeMode


def test_merge_mode_blends_resume_value_into_scratchpad():
    state = PerpetuaState(session_id="t1", scratchpad={"existing": "old"})
    result = resume_policy(state, {"existing": "new", "added": "x"}, mode=ResumeMode.MERGE)
    assert result.scratchpad == {"existing": "new", "added": "x"}


def test_drop_mode_replaces_one_key_only():
    state = PerpetuaState(session_id="t1", scratchpad={"a": 1, "b": 2})
    result = resume_policy(state, {"b": 99}, mode=ResumeMode.DROP, drop_key="b")
    assert result.scratchpad == {"a": 1, "b": 99}


def test_drop_mode_requires_drop_key():
    state = PerpetuaState(session_id="t1")
    with pytest.raises(ValueError):
        resume_policy(state, {"x": 1}, mode=ResumeMode.DROP)
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/graph/plugins/interrupt_guard.py`:
```python
"""resume_policy — apply MERGE or DROP semantics to interrupt resume values."""
from __future__ import annotations
from enum import Enum
from perpetua_core.state import PerpetuaState


class ResumeMode(str, Enum):
    MERGE = "merge"      # resume value is dict, merged into scratchpad
    DROP = "drop"        # resume value replaces ONE specified key only


def resume_policy(
    state: PerpetuaState,
    resume_value: dict,
    *,
    mode: ResumeMode,
    drop_key: str | None = None,
) -> PerpetuaState:
    if mode is ResumeMode.MERGE:
        return state.merge({"scratchpad": {**state.scratchpad, **resume_value}})
    if mode is ResumeMode.DROP:
        if not drop_key:
            raise ValueError("DROP mode requires drop_key")
        if drop_key not in resume_value:
            raise ValueError(f"resume_value lacks drop_key={drop_key!r}")
        return state.merge({"scratchpad": {**state.scratchpad, drop_key: resume_value[drop_key]}})
    raise ValueError(f"unknown ResumeMode: {mode}")
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/plugins/interrupt_guard.py tests/graph/plugins/test_interrupt_guard.py
git commit -m "feat(plugins): resume_policy MERGE/DROP for Interrupt resume values (Task 10)"
```

---

### Task 11 — Plugin: `parallel` (`Send()` fan-out for parallel dispatch)

**Why:** Closes "no parallel agent dispatch" from the user's concept map. The canonical engine is strictly sequential. This plugin adds a `parallel_dispatch(nodes, state)` helper that runs multiple node-fns concurrently and merges their deltas back into state with last-writer-wins on conflict (caller controls the order).

**Files:**
- Create: `perpetua_core/graph/plugins/parallel.py`
- Create: `tests/graph/plugins/test_parallel.py`

- [ ] **Step 1: Failing test**

```python
import pytest, asyncio
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.plugins.parallel import parallel_dispatch


@pytest.mark.asyncio
async def test_parallel_dispatch_runs_branches_concurrently():
    async def slow(state):
        await asyncio.sleep(0.05)
        return {"scratchpad": {**state.scratchpad, "slow": True}}

    async def fast(state):
        return {"scratchpad": {**state.scratchpad, "fast": True}}

    state = PerpetuaState(session_id="t1")
    result = await parallel_dispatch([("slow", slow), ("fast", fast)], state)
    assert result["scratchpad"]["slow"] is True
    assert result["scratchpad"]["fast"] is True


@pytest.mark.asyncio
async def test_parallel_dispatch_last_writer_wins_on_conflict():
    async def a(state):
        return {"scratchpad": {**state.scratchpad, "k": "from-a"}}

    async def b(state):
        return {"scratchpad": {**state.scratchpad, "k": "from-b"}}

    state = PerpetuaState(session_id="t1")
    result = await parallel_dispatch([("a", a), ("b", b)], state)
    assert result["scratchpad"]["k"] == "from-b"  # b is later in the list
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/graph/plugins/parallel.py`:
```python
"""parallel_dispatch — fan-out N node-fns concurrently, merge deltas in order."""
from __future__ import annotations
import asyncio
from typing import Awaitable, Callable
from perpetua_core.state import PerpetuaState

NodeFn = Callable[[PerpetuaState], Awaitable[dict] | dict]


async def parallel_dispatch(
    branches: list[tuple[str, NodeFn]],
    state: PerpetuaState,
) -> dict:
    """Run all branches concurrently. Returns merged delta dict.
    Merge rule: last branch in the list wins on key conflict (caller orders intent)."""
    async def _run(fn):
        out = fn(state)
        return await out if asyncio.iscoroutine(out) else out

    deltas = await asyncio.gather(*(_run(fn) for _, fn in branches))

    merged: dict = {}
    for d in deltas:
        if not d:
            continue
        for k, v in d.items():
            if k == "scratchpad" and isinstance(v, dict):
                merged["scratchpad"] = {**(merged.get("scratchpad") or {}), **v}
            else:
                merged[k] = v
    return merged
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/graph/plugins/parallel.py tests/graph/plugins/test_parallel.py
git commit -m "feat(plugins): parallel_dispatch for Send-style fan-out (Task 11)"
```

---

### Task 12 — `perpetua_core/message.py` typed wrapper (closes OQ17)

**Why:** v2 docs note that messages are plain `dict` everywhere, and Phase 3 LLMClient wiring blocks until there's a typed wrapper. This is OQ17 in `docs/v2/06-open-questions.md`. Small file, big leverage.

**Files:**
- Create: `perpetua_core/message.py`
- Create: `tests/test_message.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from perpetua_core.message import ChatMessage, ChatHistory


def test_chat_message_round_trip():
    m = ChatMessage(role="user", content="hi")
    d = m.to_openai_dict()
    assert d == {"role": "user", "content": "hi"}
    assert ChatMessage.from_openai_dict(d) == m


def test_chat_history_appends_and_serializes():
    h = ChatHistory()
    h.append(ChatMessage(role="system", content="be brief"))
    h.append(ChatMessage(role="user", content="hi"))
    payload = h.to_openai_messages()
    assert payload == [
        {"role": "system", "content": "be brief"},
        {"role": "user",   "content": "hi"},
    ]


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        ChatMessage(role="random", content="x")
```

- [ ] **Step 2: Watch it fail**

- [ ] **Step 3: Implement**

`perpetua_core/message.py`:
```python
"""Typed message wrapper. OpenAI-compat shape, no extra deps."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, get_args

Role = Literal["system", "user", "assistant", "tool"]
_VALID = set(get_args(Role))


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None

    def __post_init__(self):
        if self.role not in _VALID:
            raise ValueError(f"invalid role: {self.role!r}")

    def to_openai_dict(self) -> dict:
        d: dict = {"role": self.role, "content": self.content}
        if self.name is not None:
            d["name"] = self.name
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d

    @classmethod
    def from_openai_dict(cls, d: dict) -> "ChatMessage":
        return cls(role=d["role"], content=d.get("content", ""),
                   name=d.get("name"), tool_call_id=d.get("tool_call_id"))


@dataclass
class ChatHistory:
    messages: list[ChatMessage] = field(default_factory=list)

    def append(self, m: ChatMessage) -> "ChatHistory":
        self.messages.append(m); return self

    def to_openai_messages(self) -> list[dict]:
        return [m.to_openai_dict() for m in self.messages]
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git add perpetua_core/message.py tests/test_message.py
git commit -m "feat(core): ChatMessage + ChatHistory typed wrapper (closes OQ17, Task 12)"
```

---

## TRACK D — v2-planning bridge: port v1 discovery into v2 canon + wire dispatch

**Generation:** **v2-planning** (both repos: `oramasys/perpetua-core` + `oramasys/oramasys`).
**Discipline:** copy v1's `perpetua/discovery/*` byte-for-byte into `perpetua_core/discovery/*`. No drift. v2 is the canonical home from this commit forward.

### Task 13 — `discovery_adapter.py` bridge plugin (perpetua-core side)

**Why:** Avoid duplicating Backend/Registry/Selector logic in v2. The bridge re-exports the v1 shapes under canonical names, validates the contract holds. (v1 imports the bridge; v2 nodes import the bridge. One source of truth: v1's `perpetua/discovery/`.)

**Files:**
- Create: `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/__init__.py`
- Create: `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/adapter.py`
- Create: `tests/test_discovery_adapter.py`

**Decision:** the v2 `perpetua_core.discovery` package re-exports the *same dataclasses + selector* — copied verbatim from v1 (not imported, to keep v2 free of any v1 import). The bridge plugin merely declares the contract. Implementation is `cp -r perpetua/discovery/* perpetua_core/discovery/` then prune any v1-only deps.

- [ ] **Step 1: Copy v1 discovery sources into v2**

```bash
cd /Users/lawrencecyremelgarejo/Documents/Terminal\ xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools
cp perpetua/discovery/backend.py /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/backend.py
cp perpetua/discovery/probe.py /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/probe.py
cp perpetua/discovery/registry.py /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/registry.py
cp perpetua/discovery/selector.py /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/selector.py
cp perpetua/discovery/errors.py /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/perpetua_core/discovery/errors.py
```

- [ ] **Step 2: Create `__init__.py`**

`perpetua_core/discovery/__init__.py`:
```python
"""Canonical port of perpetua_tools.discovery. Identical shapes."""
from .backend import Backend, BackendKind, BackendHealth
from .registry import BackendRegistry
from .selector import select_backend
from .errors import BackendOfflineError, NoBackendAvailableError

__all__ = ["Backend", "BackendKind", "BackendHealth", "BackendRegistry",
           "select_backend", "BackendOfflineError", "NoBackendAvailableError"]
```

- [ ] **Step 3: Contract test — shapes match v1**

`tests/test_discovery_adapter.py`:
```python
from perpetua_core.discovery import (
    Backend, BackendKind, BackendHealth, BackendRegistry,
    select_backend, BackendOfflineError, NoBackendAvailableError,
)


def test_canonical_discovery_module_exports_full_v1_surface():
    # If this test compiles + imports succeed, the API surface matches v1.
    assert hasattr(BackendRegistry, "autodetect")
    assert hasattr(BackendRegistry, "register_by_ip")
    assert callable(select_backend)
```

- [ ] **Step 4: Tests pass**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
pytest tests/test_discovery_adapter.py -v
```

- [ ] **Step 5: Commit (perpetua-core)**

```bash
git add perpetua_core/discovery/ tests/test_discovery_adapter.py
git commit -m "feat(discovery): canonical port of v1 discovery shapes (Task 13)"
```

---

### Task 14 — Wire `dispatch_node` to discovery (oramasys/oramasys)

**Files:**
- Modify: `/Users/lawrencecyremelgarejo/Documents/oramasys/oramasys/orama/graph/perpetua_graph.py`
- Create: `/Users/lawrencecyremelgarejo/Documents/oramasys/oramasys/tests/test_dispatch_with_discovery.py`

**Switch repos:**
```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/oramasys
git checkout feat/dispatch-discovery-bridge
```

- [ ] **Step 1: Read current `dispatch_node`**

```bash
grep -n "dispatch_node\|async def dispatch\|async def route\|async def respond" orama/graph/perpetua_graph.py
```

- [ ] **Step 2: Failing integration test**

`tests/test_dispatch_with_discovery.py`:
```python
import pytest, respx, httpx
from perpetua_core.state import PerpetuaState
from perpetua_core.discovery import BackendRegistry
from orama.graph.perpetua_graph import build_graph


@pytest.mark.asyncio
@respx.mock
async def test_dispatch_routes_through_discovery_registry():
    # Seed registry with one online windows backend.
    respx.get("http://192.168.254.103:1234/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "qwen3-coder-30b"}]}))
    respx.get("http://localhost:11434/v1/models").mock(return_value=httpx.Response(404))
    respx.get("http://localhost:1234/v1/models").mock(return_value=httpx.Response(404))

    reg = BackendRegistry()
    await reg.autodetect()

    # Build graph with registry injected.
    graph = build_graph(registry=reg)
    state = PerpetuaState(session_id="t1", task_type="coding", target_tier="shared")
    result = await graph.ainvoke(state)
    assert result.metadata.get("resolved_backend") == "lmstudio-win"
    assert result.status == "done"
```

- [ ] **Step 3: Watch it fail**

```bash
pytest tests/test_dispatch_with_discovery.py -v
```

- [ ] **Step 4: Implement** — refactor `orama/graph/perpetua_graph.py` so `build_graph()` accepts a registry and the dispatch node consults it:

```python
# orama/graph/perpetua_graph.py — relevant excerpts
from perpetua_core.discovery import BackendRegistry, select_backend
from perpetua_core.graph.engine import MiniGraph, END
from perpetua_core.state import PerpetuaState


def build_graph(*, registry: BackendRegistry | None = None) -> "CompiledGraph":
    reg = registry or BackendRegistry()  # caller seeds; empty = no online backends

    async def route_node(state: PerpetuaState) -> dict:
        # Existing hardware affinity logic stays here; just no longer dispatches.
        return {"metadata": {**state.metadata, "routed_at": "route_node"}}

    async def dispatch_node(state: PerpetuaState) -> dict:
        backend = select_backend(
            reg,
            model_hint=state.model_hint,
            task_type=state.task_type,
            target_tier=state.target_tier,
        )
        # Placeholder until Phase 3 LLMClient wiring lands.
        return {"metadata": {**state.metadata, "resolved_backend": backend.name,
                             "resolved_url": backend.base_url}}

    async def respond_node(state: PerpetuaState) -> dict:
        return {"messages": [*state.messages,
                             {"role": "assistant",
                              "content": f"dispatched to {state.metadata.get('resolved_backend')}"}]}

    g = MiniGraph()
    g.add_node("route", route_node)
    g.add_node("dispatch", dispatch_node)
    g.add_node("respond", respond_node)
    g.set_entry("route")
    g.add_edge("route", "dispatch")
    g.add_edge("dispatch", "respond")
    g.add_edge("respond", END)
    return g.compile()
```

- [ ] **Step 5: Test passes + canonical suite green**

```bash
pytest tests/ -v  # this repo
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core && pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/oramasys
git add orama/graph/perpetua_graph.py tests/test_dispatch_with_discovery.py
git commit -m "feat(dispatch): wire perpetua_graph dispatch_node to discovery registry (Task 14)"
```

---

## TRACK E — cross-cutting verification

**Generation:** **cross-cutting** — invariants and regression checks govern both generations.

### Task 15 — Hypothesis property tests for engine invariants

**Why:** Per spec §6.4, property tests catch invariants that example-based tests miss. Three invariants:

1. **Determinism**: same state + same graph → same result.
2. **`nodes_visited` monotonicity**: list grows by exactly 1 per step.
3. **`max_steps` honored**: graphs with cycles raise iff steps exceed cap.

**Files:**
- Create: `tests/property/__init__.py`
- Create: `tests/property/test_engine_invariants.py`
- Create: requirement: `hypothesis>=6.0`

- [ ] **Step 1: Install hypothesis if missing**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
pip install hypothesis pytest-asyncio respx
```

- [ ] **Step 2: Failing test**

`tests/property/test_engine_invariants.py`:
```python
import pytest
from hypothesis import given, strategies as st, settings
from perpetua_core.state import PerpetuaState
from perpetua_core.graph.engine import MiniGraph, END, MaxStepsExceeded


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=1, max_value=10))
@pytest.mark.asyncio
async def test_linear_chain_visits_each_node_exactly_once(n: int):
    g = MiniGraph()
    names = [f"n{i}" for i in range(n)]
    for nm in names:
        g.add_node(nm, lambda s: {})
    g.set_entry(names[0])
    for i, nm in enumerate(names):
        g.add_edge(nm, names[i + 1] if i + 1 < n else END)
    result = await g.ainvoke(PerpetuaState(session_id="t1"))
    assert result.nodes_visited == names


@settings(max_examples=20, deadline=None)
@given(st.integers(min_value=2, max_value=15))
@pytest.mark.asyncio
async def test_cycle_always_raises_under_max_steps_cap(cap: int):
    g = MiniGraph(max_steps=cap)
    g.add_node("loop", lambda s: {})
    g.set_entry("loop")
    g.add_edge("loop", lambda s: "loop")
    with pytest.raises(MaxStepsExceeded):
        await g.ainvoke(PerpetuaState(session_id="t1"))
```

- [ ] **Step 3: Run**

```bash
pytest tests/property/ -v
```

- [ ] **Step 4: Commit**

```bash
git add tests/property/ requirements*.txt 2>/dev/null
git commit -m "test(property): Hypothesis invariants for engine determinism + cycle cap (Task 15)"
```

---

### Task 16 — Full regression sweep + PROGRESS.md DONE march

**Files:**
- Modify: `PROGRESS.md` (all rows → DONE with commit SHAs)

- [ ] **Step 1: Run full canonical suite**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
pytest tests/ -v --tb=short 2>&1 | tail -40
```
Expected: original 32 tests + new tests all green. Document the total count.

- [ ] **Step 2: Run v1 suite**

```bash
cd /Users/lawrencecyremelgarejo/Documents/Terminal\ xCode/claude/OpenClaw/perplexity-api/Perpetua-Tools
pytest tests/discovery/ tests/test_agent_launcher_uses_registry.py -v
```

- [ ] **Step 3: Run v2 suite**

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/oramasys
pytest tests/ -v
```

- [ ] **Step 4: Update PROGRESS.md** — fill in all `Status: DONE` + commit SHAs by running:

```bash
cd /Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core
git log feat/salvage-plugins-rc1 --oneline -25
```

Paste the SHA for each task into the matching row. Commit:

```bash
git add PROGRESS.md
git commit -m "chore(progress): mark all salvage tasks DONE with commit SHAs"
```

- [ ] **Step 5: Append LESSONS.md note**

In orama-system repo:

```bash
cat >> "/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/orama-system/docs/LESSONS.md" <<'EOF'

## 2026-05-17 — Salvage translation + v1 IP-aware discovery landed

Generation labeling (per Canonical Repo Registry):

- **v2-planning (`oramasys/perpetua-core` on `feat/salvage-plugins-rc1`):** max_steps guard, set_entry/compile, 5 new plugins (routing, tool_node, validator, interrupt_guard, parallel), typed ChatMessage/ChatHistory, canonical `perpetua_core/discovery/` (verbatim copy of v1 shapes — v2 is now the canonical home).
- **v2-planning (`oramasys/oramasys` on `feat/dispatch-discovery-bridge`):** `dispatch_node` consults `BackendRegistry` via the canonical discovery module.
- **v1-legacy (`diazMelgarejo/Perpetua-Tools` on `feat/ip-aware-discovery`):** tactical fix — `perpetua/discovery/` with autodetect + register_by_ip + health probe + tier+task selector. Wired into `agent_launcher.resolve_backend_for_spec`. Shape designed to match v2 canon (Track D copies it forward without drift).
- **cross-cutting (`orama-system/docs/`):** plan, spec, LESSONS append.

LangGraph concept map (CSV) mirrored 1:1 in v2-planning code:
State=PerpetuaState · Node=async fn · Edge=string · ConditionalEdge=LabelRouter · Cycle=max_steps · Checkpointer=plugin (already shipped) · Send()=parallel_dispatch · ToolNode=plugin · Validator=plugin · InterruptGuard=plugin.

Push policy: v1-legacy and v2-planning code branches stay local until user reviews end-to-end on Mac+Win; only cross-cutting docs push immediately.
EOF
```

Then commit + push the LESSONS update in orama-system (this repo only):

```bash
cd "/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/orama-system"
git add docs/LESSONS.md docs/superpowers/plans/2026-05-17-salvage-translation-v1-discovery.md
git commit -m "docs: salvage + v1 discovery implementation plan + lessons note"
git push origin main
```

---

## Definition of Done

- [ ] All 16 task commits exist on their respective local branches.
- [ ] PROGRESS.md shows DONE for every row with valid SHAs.
- [ ] `pytest tests/` green in all three repos (perpetua-core, oramasys, Perpetua-Tools).
- [ ] Hypothesis property tests run with `max_examples >= 20` and pass.
- [ ] No `oramasys/*` branch pushed to remote yet — user reviews before push.
- [ ] LESSONS.md note added to orama-system (this repo).

## Out of scope (deferred, separate plans later)

- WhatsApp frontdoor entry node
- SSE streaming + mid-stream tool call accumulator (the `streaming.py` skeleton — wait for v2 frontend work)
- LanceDB/DuckDB gossip persistence
- `api_server.py` glass-window refactor (separate plan; depends on Task 14 completing)
- Sentinel Node SWARM misalignment monitor (Phase 2 work, separate plan)
- v2 LLMClient + run_agent_loop wiring (Phase 3 work, separate plan — `message.py` from Task 12 unblocks this)

---

## Self-review (post-write, before handoff)

- [x] **Spec coverage**: Engine guard + 5 plugins + message.py from the salvage spec are each a numbered task. v1 discovery (which the spec did not enumerate but the user requested) gets Tracks A + D. v2 dispatch wiring closes the loop.
- [x] **Placeholders**: none — every step has runnable code or commands.
- [x] **Type consistency**: `Backend`, `BackendRegistry`, `BackendHealth`, `BackendKind` use the same shapes in v1 and v2 (Task 13 copies the source). `select_backend` signature identical in both. `PerpetuaState` fields referenced (`task_type`, `target_tier`, `model_hint`, `optimize_for`, `nodes_visited`, `scratchpad`) all verified in canonical state.py.
- [x] **TDD**: every task is failing test → watch fail → minimal code → pass → commit. Per `docs/TDD.md` pre-commit checklist.
- [x] **No premature push**: only orama-system pushes; perpetua-core and oramasys stay local until user review.

## Execution Handoff

Plan saved. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review between tasks, fast iteration. Codex CLI handles mechanical ports (Tasks 8, 11, 13). Gemini reviews after each task. Sonnet integrates. Opus orchestrates.

**2. Inline Execution** — execute tasks in this session with checkpoint review after each track (A, B, C, D, E).

Which approach?
