# V2 Supervisor — Anthropic Patterns + DB Persistence + MAESTRO/SWARM

> **Source files synthesized:**
> - `v1/B2-ai-cli-mcp.md` — token-efficiency and file-system-first payload strategy
> - `v1/003-Gemini-Hardware.md.md` — hardware probe, AI tier mapping, Ollama tuning
> - `v2/5-Anthropic-agent-design.md` — multi-agent patterns, code snippets, build sequence
>
> **V1 vs V2 split:**
> - V1 (shipped 2026-05-08): `Perpetua-Tools/orchestrator/supervisor.py` — file-based persistence (jsonl), no DB, legacy FastAPI intact
> - V2 (this spec): real DB persistence + MAESTRO+SWARM enforcement + public plugin API
>
> **Status:** Planning spec. Implementation begins after v1.0 RC ships (D3 from v2/00-context-and-decisions.md).

---

## 1. What V1 Gave Us (Do Not Break)

V1 ships five files (all in `Perpetua-Tools/`):

| File | Role |
|------|------|
| `orchestrator/supervisor.py` | `OrchestrationSupervisor` + `JobSpec` + `JobStatus` |
| `orchestrator/worker_registry.py` | Static `WORKER_REGISTRY` + `resolve_backend()` |
| `utils/action_validator.py` | Two-phase gate (irreversibility + HITL) |
| `scripts/mac_probe.sh` | Zero-dependency hardware detection |
| `tests/test_supervisor_smoke.py` | 13 Mac-only smoke tests (192/192 suite green) |

V1 API surface (backwards-compatible; DO NOT remove in V2):

```
POST /v1/jobs
GET  /v1/jobs
GET  /v1/jobs/{id}
POST /v1/jobs/{id}/cancel
POST /v1/jobs/{id}/replay
```

V1 invariants that carry forward into V2:
- `MAX_DEPTH = 1` (Anthropic hard constraint)
- `MAX_THREADS = 25` (Anthropic spec ceiling)
- Write final checkpoint BEFORE propagating `CancelledError` (not after)
- `HardwarePolicyResolver.check_affinity()` runs before any LLM call
- Fail-closed on `HardwareAffinityError` — no silent rerouting

---

## 2. V2 Persistence Layer — Real DB (SQLite → Postgres path)

V2 replaces the append-only jsonl with a proper relational store.

### 2a. Schema (SQLite for v2.0, Postgres-compatible for v2.1+)

```sql
-- jobs table: one row per job, updated in-place
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    intent      TEXT NOT NULL,
    payload     TEXT NOT NULL,            -- JobSpec JSON blob
    status      TEXT NOT NULL DEFAULT 'queued',
    result      TEXT,                     -- result JSON blob
    checkpoint  TEXT,                     -- last generator checkpoint
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    thread_id   TEXT,
    depth       INTEGER DEFAULT 0,
    policy_tag  INTEGER DEFAULT 0         -- 1 = MAESTRO-gated
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_intent ON jobs(intent);

-- audit_log table: immutable primary-thread event log
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL NOT NULL,
    event_type  TEXT NOT NULL,            -- session.thread_created | … | agent.result_received
    job_id      TEXT,
    thread_id   TEXT,
    agent_name  TEXT,
    payload     TEXT,
    requires_action INTEGER DEFAULT 0    -- 1 = blocks until human confirmation
);
CREATE INDEX IF NOT EXISTS idx_audit_ts    ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type);
```

### 2b. V2 JobState dataclass (replaces V1 JobSpec)

```python
from dataclasses import dataclass, field, asdict
from typing import Optional
import time

@dataclass
class JobState:
    job_id:      str
    intent:      str
    payload:     dict
    status:      str   = "queued"        # queued|running|idle|done|failed|cancelled
    result:      Optional[dict] = None
    checkpoint:  dict  = field(default_factory=dict)
    created_at:  float = field(default_factory=time.time)
    updated_at:  float = field(default_factory=time.time)
    thread_id:   Optional[str] = None
    depth:       int   = 0               # enforced MAX = 1

    def to_dict(self) -> dict:
        return asdict(self)
```

### 2c. V2 OrchestrationSupervisor (DB-backed)

```python
class OrchestrationSupervisorV2:
    MAX_DEPTH   = 1
    MAX_THREADS = 25

    def __init__(self, db_path: str = ".state/perpetua.db"):
        self.policy = HardwarePolicyResolver()
        self._db    = db_path
        self._active: dict[str, asyncio.Task] = {}
        self._audit = PrimaryThreadAuditLog(db_path.replace(".db", "_audit.db"))
        self._init_db()

    def enqueue(self, intent: str, payload: dict, depth: int = 0) -> str:
        if depth > self.MAX_DEPTH:
            raise ValueError(f"Depth {depth} > MAX_DEPTH={self.MAX_DEPTH}")
        import uuid
        job_id = str(uuid.uuid4())
        state  = JobState(job_id=job_id, intent=intent, payload=payload, depth=depth)
        self._persist(state)
        return job_id

    async def run_job(self, job_id: str):
        """Generator — each yield is a durable checkpoint."""
        state = self._load(job_id)
        model = self.policy.resolve(state.intent)  # raises HardwareAffinityError BEFORE LLM call

        self._audit.thread_created(job_id, state.thread_id, "supervisor")
        state.status = "running"
        self._persist(state)

        try:
            async for checkpoint in self._execute(state, model):
                state.checkpoint = checkpoint
                state.updated_at = time.time()
                self._persist(state)
                yield checkpoint

            state.status = "done"

        except asyncio.CancelledError:
            # Write checkpoint BEFORE killing — critical ordering
            state.status = "cancelled"
            self._persist(state)
            self._audit.thread_terminated(job_id, state.thread_id, "supervisor", "cancelled")
            await self._kill_workers(job_id)
            raise

        except Exception as exc:
            state.status = "failed"
            state.result = {"error": str(exc)}
            self._persist(state)
            self._audit.thread_terminated(job_id, state.thread_id, "supervisor", str(exc))
            raise

        finally:
            self._active.pop(job_id, None)
            self._persist(state)
```

---

## 3. Primary Thread Audit Log (V2 Pattern 5)

Maps to Anthropic's primary-thread condensed event view.  Every thread lifecycle
event is written here — worker internal reasoning stays in session thread logs.

Required by MAESTRO accountability layer (§4 below).

```python
class PrimaryThreadAuditLog:
    """Immutable append-only event log.  All cross-thread events go here."""

    def thread_created(self, job_id, thread_id, agent_name): …
    def thread_idle(self, job_id, thread_id, agent_name, stop_reason: dict): …
    def thread_terminated(self, job_id, thread_id, agent_name, reason: str = ""): …
    def agent_result_received(self, job_id, from_thread_id, from_agent, content): …
```

Full implementation → `Perpetua-Tools/utils/audit_log.py` (V2 task).

---

## 4. MAESTRO Gate Nodes (V2 Safety Layer)

MAESTRO 7-layer threat model integration (see `orama-system/docs/v2/03-safety-v2.5.md`).

### Gate class mapping

| MAESTRO Class | Trigger | V2 Enforcement |
|---|---|---|
| Class 2 | Normal inference request | Intent log + user confirm via HITL node |
| Class 3 | HITL-scoped tool (`send_message`, `modify_model_registry`) | `approval_token` required in `fan_out_workers()` |
| Class 4 | Irreversible action (`delete_file`, `push_to_remote`) | Cryptographic token + immutable audit entry |

### V2 API gate annotations

```
POST /ultrathink          → MAESTRO Class 2 gate
POST /v1/jobs/fan_out     → MAESTRO Class 3 gate (approval_token required)
POST /v1/jobs/swarm_launch → MAESTRO Class 4 gate (crypto token + audit)
```

### ActionValidator upgrade for V2

V1 `ActionValidator` has the correct shape.  V2 upgrades:
- Replace log-only Class 2 with real user confirmation node
- Add cryptographic token verification for Class 4
- Wire `PrimaryThreadAuditLog.log()` for every gate trigger

---

## 5. SWARM Misalignment Guardrails (V2.5)

Deferred to v2.5.  Planning notes:

- **Goal**: detect agent-to-agent context bleeding in parallel fan-out
- **Mechanism**: each worker session is isolated (Anthropic Pattern 2 — Context Firewall)
- **Audit hook**: `requires_action` events on any session thread get cross-posted to
  `PrimaryThreadAuditLog` and **block** until human confirmation arrives
- **Rollback**: if SWARM detects misalignment, cancel all `RUNNING` jobs in the
  affected fan-out group; write final checkpoint; emit `swarm.misalignment_detected`
  audit event

---

## 6. Token-Efficiency Rules (from B2-ai-cli-mcp.md)

These carry into V2 workers and MCP surface:

### File-system-first payload

```python
# WRONG — passes 500 lines through MCP context
result = await mcp_client.call("run_gemini", {"prompt": full_file_content})

# CORRECT — passes a path; Gemini writes result to disk
result = await mcp_client.call("run_gemini", {
    "prompt": f"Refactor auth.py and save to auth_v2.py",
    "cwd": str(project_dir),
})
# MCP response: {"status": "success", "file": "auth_v2.py"} — ~10 tokens
```

### CLI workers: always JSON mode

```python
# All CLI workers must strip ANSI / spinner artifacts:
cmd = ["gemini", "--yolo", "-p", prompt]          # Gemini — already done in V1
cmd = ["codex", "--approval-mode", "auto-edit", "--quiet", prompt]  # Codex — done in V1
```

### Schema trimming in openclaw.json

- Allowlist only `codex` and `gemini` tools in MCP client if that is all you use
- Local model already knows how to call `run_gemini` via system prompt → skip verbose description
- Target: local model stays in ≤ 8k context window even with full worker roster active

---

## 7. Hardware-Aware Installer (from 003-Gemini-Hardware.md)

`mac_probe.sh` (shipped in V1) gives us the hardware primitives.  V2 installer tasks:

### V2 tasks
1. **Model-ID to spec mapping** — bundle a local JSON file mapping `Mac16,11` → `{ai_tier, npu_cores, memory_bandwidth_gbps}`.  Source: community-maintained list (linusg/macos-model-identifiers or OpenCore project).
2. **Auto-configure Ollama** at install time:
   - Write `~/.config/ollama/config.json` with `OLLAMA_NUM_PARALLEL` from `mac_probe.sh` output
   - Set context window hint: `base` → 8k, `standard` → 16k, `ultra` → 32k
3. **Model recommendation at install** — show user suggested model based on tier:
   - `base` (< 16 GB): Llama-3.2-3B / Qwen2.5-3B
   - `standard` (16–32 GB): qwen3:8b / Mistral-Small
   - `ultra` (≥ 32 GB): qwen2.5-coder-32b / DeepSeek-R1-32B
4. **Windows GPU guard** — installer enforces `OLLAMA_NUM_PARALLEL=1` on Windows to prevent dual-model loading

---

## 8. V2 Build Sequence (from 5-Anthropic-agent-design.md §4, adapted)

```
Step 1 (V2.0 — after V1.0 RC ships):
  PT: orchestrator/supervisor_v2.py
    - OrchestrationSupervisorV2 with SQLite job queue
    - MAX_DEPTH=1 and MAX_THREADS=25 (same as V1)
    - Generator-based checkpointing (yield-as-checkpoint)
    - Checkpoint written BEFORE CancelledError propagation

Step 2 (V2.0):
  PT: utils/audit_log.py
    - PrimaryThreadAuditLog class
    - Wire into supervisor V2 run_job() at all 4 thread event types

Step 3 (V2.0):
  PT: utils/action_validator.py (upgrade from V1)
    - Add Class 4 cryptographic token verification
    - Wire into supervisor V2 _execute() before every tool call

Step 4 (V2.0):
  PT: Wire HardwarePolicyResolver as first gate in run_job()
    - policy.resolve(intent) before LLM call (same as V1)
    - Remove any qwen3-coder:14b fallback remnants

Step 5 (V2.0):
  orama: agents/dispatcher.py
    - fan_out_workers() with asyncio.gather
    - approval_token gate for require_approval=True plans
    - Depth guard: drop specs depth > MAX_DEPTH

Step 6 (V2.0):
  PT: orchestrator/worker_registry_v2.py
    - Extend V1 registry with lmstudio-win backend
    - Add escalation_threshold per worker config (escalate to Windows tier)

Step 7 (V2.0):
  PT: mac_probe.sh → Model-ID mapping JSON (Gemini hardware spec)
    - Bundle model_id_specs.json alongside mac_probe.sh
    - Installer reads tier and auto-configures Ollama

Step 8 (V2.5):
  orama: MAESTRO gate nodes on API endpoints
    - /ultrathink: Class 2
    - /v1/jobs/fan_out: Class 3
    - /v1/jobs/swarm_launch: Class 4

Step 9 (V2.5):
  Both: SWARM misalignment guardrails
    - Context firewall per worker session
    - Cross-post requires_action events to PrimaryThreadAuditLog
    - Auto-cancel fan-out group on misalignment detection
```

---

## 9. Open Questions for V2

- **Q1**: SQLite → Postgres migration path for V2.1+ (multi-machine shared state)?
  Best guess: SQLite in V2.0 (single-node), Postgres via env var swap in V2.1.
- **Q2**: V2.5 SWARM misalignment detection — pull-based (poll audit log) or push-based
  (async event via GossipBus)?  GossipBus is already in the V2 kernel spec.
- **Q3**: Gemini quota-exhausted (429) — retry policy in V2 worker?  V1 fails with error.
  V2 could add exponential backoff up to 1 retry, but not auto-reroute to a different model.
- **Q4**: `start.ps1` for Windows — integrates with V2 supervisor `/health` + `/submit`?
  Deferred to Win+Mac LAN test window.

---

*Generated: 2026-05-08 — Synthesized from B2-ai-cli-mcp.md, 003-Gemini-Hardware.md, 5-Anthropic-agent-design.md*
*V1 implementation shipped in same session: Perpetua-Tools commit (see LESSONS.md)*
