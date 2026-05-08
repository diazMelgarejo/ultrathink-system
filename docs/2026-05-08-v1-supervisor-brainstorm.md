# 2026-05-08 — V1 Persistent Supervisor Brainstorm

> **Inputs to this doc**
> - `OpenClaw/perpetua-v1-part2-followup.md` — the V1 spec (the "no single supervisor" diagnosis + 9 requirements)
> - Anthropic's public multi-agent patterns (https://platform.claude.com/docs/en/managed-agents/multi-agent — orchestrator-worker, isolated context windows, structured handoff, parallel fan-out)
> - Codex audit (gpt-5.3-codex, 2026-05-08, session `019e051b`) — entrypoint inventory + supervisor-gap punch list
>
> **Status**: Brainstorm + plan only. Not implementation.
> **Scope**: Smallest LoC, highest outcome. Mac-only verifiable today; Win+Mac LAN tests deferred ~2 days.
> **Gemini analysis was attempted but quota-exhausted (429)** — re-run when quota resets.

---

## 1. The supervisor gap, in one paragraph

PT and orama already have all the pieces — agent_launcher, alphaclaw_manager, fastapi_app, spawn_agents, hardware_policy_cli, control_plane, AgentTracker, the new startup_intelligence engine.  What's missing is **one durable contract** that ties them together: a `submit_job → get_status → cancel/replay` API that the portal, the shell wrappers, the MCP servers, and the Claude CLI all call into.  Today each surface re-implements its own ad-hoc dispatch path.  V1 is consolidation, not invention.

---

## 2. Five Anthropic patterns worth adopting

| # | Pattern | Where it lives | Why it solves the gap |
|---|---|---|---|
| 1 | **Orchestrator → Worker** with strict context isolation | PT — `orchestrator/supervisor.py` | Single decision point: the orchestrator picks the backend, workers (codex/gemini/lmstudio/ollama subprocesses) never see other workers' state. Eliminates the cross-script context bleeding the followup file complains about. |
| 2 | **Tool-call as the dispatch primitive** (return one message with `status + summary + artifact_pointer`) | PT — supervisor's worker contract | Replaces 6+ ad-hoc dispatch shapes (`spawn_agents.py`, `_dispatch_gemini`, portal handlers, MCP handlers) with one envelope. Workers become interchangeable. |
| 3 | **Durable job artifact store** (jsonl append-only + per-job log dir) | PT — `.state/jobs.jsonl` + `.state/jobs/<id>/` | Replay, cancel, and crash recovery all fall out of "the source of truth is on disk." Anthropic uses memory-tool / artifact uploads for the same reason. No Redis dependency required (preserves the orama stateless-API invariant). |
| 4 | **Parallel sub-agent fan-out, depth ≤ 1** | PT supervisor + `asyncio.gather` | We already have it conceptually (`spawn_agents.py --agent all` runs codex+gemini+lmstudio together). Anthropic's lesson: cap depth at 1 to avoid token/cost runaways — for us that maps to "no worker may spawn another worker." Cheap rule, big safety win. |
| 5 | **Structured handoff envelope** with explicit lifecycle states | PT — `JobState` enum | Replace today's `{"ok": bool, "output": str, "elapsed": float}` with `queued → running → waiting_input → succeeded → failed → cancelled`. The portal, MCP, and shell get one state machine to consume. |

---

## 3. What to AVOID adopting

| Anti-pattern | Why we skip |
|---|---|
| **Cloud-billed orchestrator** (Anthropic's managed-agents SDK as the supervisor itself) | We are local-first.  The supervisor must run inside PT's Python process and survive when the LAN is down. |
| **Anthropic Agent SDK as the worker contract** | Pins us to Anthropic's API shape. Our workers include codex, gemini-cli, LM Studio, Ollama, Perplexity — vendor-neutral subprocess+HTTP is the lowest common denominator. |
| **Recursive sub-agent spawning** | Each level multiplies the cost. Our hardware affinity gate is already non-trivial; nested workers would invalidate the GPU lock invariant. **Hard rule**: orchestrator → worker, depth = 1, no nesting. |
| **Auto-retry on policy errors** | When `HardwareAffinityError` fires, fail closed. Don't quietly route to a different backend — that's exactly the silent-degradation bug we just fixed in agent_launcher. |
| **Memory tool that mutates state across jobs** | Each job is independent. Cross-job context lives in `LESSONS.md` (human-curated), not in the supervisor. Keeps the supervisor stateless-per-job. |

---

## 4. Code sketches (≤15 lines each)

### 4a. `JobState` + `JobSpec` (the envelope)

```python
# perpetua-api/Perpetua-Tools/orchestrator/supervisor.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

class JobState(str, Enum):
    QUEUED = "queued"; RUNNING = "running"; WAITING_INPUT = "waiting_input"
    SUCCEEDED = "succeeded"; FAILED = "failed"; CANCELLED = "cancelled"

@dataclass
class JobSpec:
    job_id: str            # ulid or uuid4
    intent: str            # "code-review" | "debug" | "ml-experiment" | "freeform"
    backend_hint: str | None  # "auto" | "codex" | "gemini" | "lmstudio-mac" | ...
    prompt: str
    constraints: dict      # hardware/affinity, gpu_lock_required, max_seconds
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### 4b. Supervisor's submit + worker dispatch (orchestrator-worker shape)

```python
class OrchestrationSupervisor:
    async def submit_job(self, spec: JobSpec) -> str:
        backend = self._route(spec)             # uses startup_intelligence + hardware_policy
        await self._persist(spec, JobState.QUEUED, backend=backend)
        asyncio.create_task(self._run_worker(spec, backend))
        return spec.job_id

    async def _run_worker(self, spec: JobSpec, backend: str):
        await self._set_state(spec.job_id, JobState.RUNNING)
        try:
            result = await BACKENDS[backend].dispatch(spec)   # codex/gemini/lms/...
            await self._finalize(spec.job_id, JobState.SUCCEEDED, result)
        except HardwareAffinityError as e:
            await self._finalize(spec.job_id, JobState.FAILED, {"error": str(e), "policy": True})
        except asyncio.CancelledError:
            await self._finalize(spec.job_id, JobState.CANCELLED, {})
            raise
```

### 4c. Durable persistence (jsonl append-only)

```python
# Single jsonl per repo: .state/jobs.jsonl. One line per state transition.
# Replay = read tail until you find a SUCCEEDED for that job_id, copy spec, new id.
def _persist_event(self, job_id: str, event: dict):
    with self.jobs_file.open("a") as f:
        f.write(json.dumps({"ts": _now_iso(), "job_id": job_id, **event}) + "\n")

def list_jobs(self, state: JobState | None = None) -> list[dict]:
    return [j for j in self._load_all() if state is None or j["state"] == state.value]

async def replay(self, job_id: str, overrides: dict | None = None) -> str:
    spec = self._load_spec(job_id)
    new_spec = dataclasses.replace(spec, job_id=_new_id(), **(overrides or {}))
    return await self.submit_job(new_spec)
```

---

## 5. Mapping to V1 requirements (followup file §V1 1-9)

| Req | Mechanism | File(s) to modify/create |
|---|---|---|
| 1. One Mac entry, one Win entry | Keep `start.sh`; new `start.ps1` as thin wrapper that calls supervisor's `/health` + `/submit` HTTP | `orama-system/start.sh` (small), `orama-system/start.ps1` (NEW, deferred — needs Win box) |
| 2. Persistent supervisor: durable, status, cancel, retry, swappable session | NEW `OrchestrationSupervisor` (sec. 4) | `Perpetua-Tools/orchestrator/supervisor.py` (NEW), `Perpetua-Tools/orchestrator/fastapi_app.py` (delegate) |
| 3. Intent-routed dispatch | `_route(spec)` uses `startup_intelligence.classify_scenario` + intent table | `Perpetua-Tools/orchestrator/supervisor.py` (intent table inline) |
| 4. Execute orama-defined OpenClaw sub-agents through PT primitives | Add `BACKENDS["openclaw-subagent"]` worker that loads orama agent definition, then delegates | `Perpetua-Tools/orchestrator/workers/openclaw.py` (NEW) |
| 5. Gemini + Codex autonomous jobs | Already exist (`spawn_agents._dispatch_*`) — wrap as worker classes | `Perpetua-Tools/orchestrator/workers/{gemini,codex}.py` (NEW thin wrappers) |
| 6. Hardware/affinity fail-closed | Existing `check_affinity` + `HardwareAffinityError`; supervisor catches + finalizes FAILED | `_run_worker()` already in sketch 4b |
| 7. Surface state to portal | Portal subscribes to `.state/jobs.jsonl` tail (or HTTP polling) | `orama-system/portal_server.py` (read-only consumer; no logic changes) |
| 8. Acceptance tests for full flow | Mac-only smoke test (sec. 7); Win+Mac defer | `Perpetua-Tools/tests/test_supervisor_smoke.py` (NEW) |
| 9. Plan for deferred tests | This doc + dated stub in `tests/test_supervisor_lan.py` skipped with `@pytest.mark.skipif(not _both_nodes_up())` | `Perpetua-Tools/tests/test_supervisor_lan.py` (NEW skipped) |

---

## 6. 90-minute build order (Mac-only verifiable today)

1. **Create `orchestrator/supervisor.py` skeleton** — `JobState`, `JobSpec`, `OrchestrationSupervisor` with empty methods + tests for the dataclasses (~25 LoC). 10 min.
2. **Implement `_persist_event` + `_load_all`** — jsonl append + parse. Add a 5-test unit suite covering append, parse, replay-spec-extraction. 15 min.
3. **Wire `submit_job → _run_worker → _finalize`** — happy path only. One mock backend (`echo`) returning a canned dict. 15 min.
4. **Add real backend wrappers** — `workers/codex.py`, `workers/gemini.py` — each a 30-line file delegating to existing `spawn_agents._dispatch_*` (which is already battle-tested + has `--yolo` patch). 20 min.
5. **Mount supervisor on `fastapi_app.py`** — `POST /v1/jobs`, `GET /v1/jobs/{id}`, `POST /v1/jobs/{id}/cancel`, `POST /v1/jobs/{id}/replay`. 5 endpoints, ≤5 LoC each. 15 min.
6. **Mac smoke test** — `tests/test_supervisor_smoke.py`: submit echo job, poll until SUCCEEDED, assert artifact present. ~30 LoC. 10 min.
7. **Wire Codex audit's "delete" list** — open one PR per move (5 moves from Codex sec. 3) — but **do this in a separate session**; it's churn, not new code. Out of scope for the 90 min.

Acceptance for the 90-min cut: `pytest -k supervisor_smoke` green on Mac with no Windows box reachable.

---

## 7. Codex audit's top 5 consolidation moves (verbatim, kept for execution)

These are documented here so they survive the brainstorm session:

1. **`Perpetua-Tools/orchestrator/supervisor.py` + `fastapi_app.py`**: add `OrchestrationSupervisor`, thin endpoints. **+350 / -220 LoC**.
2. **`Perpetua-Tools/orchestrator.py`** (legacy FastAPI): delete the duplicate `/orchestrate` flow → 410 + migration shim. **-450 LoC**.
3. **`spawn_agents.py` (PT mirror) + portal direct module-loading**: replace with supervisor RPC. **-180 / +90 LoC**.
4. **`discover.py` + `network_autoconfig.py` + `ip_detection_solution.py` + 2× `discover-lm-studio.sh`**: fold into one PT-owned routing primitive. **-320 / +110 LoC**.
5. **`start.sh` + `check-stack.sh` + `openclaw_bootstrap.py`**: `start.sh` becomes strict launcher; supervisor reports readiness. **-260 / +70 LoC**.

Net: **~+620 / -1430 LoC = -810 LoC** across both repos for the same (or better) capability.

---

## 8. Mac-only quickstart (Codex audit's proof command)

```bash
cd orama-system && ./start.sh --no-open
```

Expected:

```text
[pt] resolved — mode=single  distributed=no
PT   starting → .logs/pt.log
orama starting → .logs/us.log
Portal starting → .logs/portal.log
── services ready ─────────────────────────────────────────
●  PT      http://localhost:8000/health
●  orama   http://localhost:8001/health
●  Portal  http://localhost:8002
```

After supervisor lands, append:

```bash
curl -X POST http://localhost:8000/v1/jobs -d '{"intent":"freeform","prompt":"echo hi"}'
# → {"job_id":"01HX...","state":"queued"}
sleep 3 && curl http://localhost:8000/v1/jobs/01HX...
# → {"state":"succeeded","artifact":".state/jobs/01HX.../result.json"}
```

---

## 9. Deferred (re-run in ~2 days when both Mac + Win are LAN-live)

- `tests/test_supervisor_lan.py::test_winonly_model_routes_to_win` — submit a Windows-only model job from Mac; assert routing lands on `192.168.x.108`, never on Mac
- `tests/test_supervisor_lan.py::test_failclosed_when_win_offline` — Win node down + Win-only model requested → `JobState.FAILED` with `policy=True`, recovery hint
- `start.ps1` end-to-end on a real Windows box
- Gemini-mined version of section 2/4 — Gemini quota was exhausted today (429), retry analysis once daily limit resets

---

## 10. Open questions for the next session

- **Q1**: Should `JobSpec.constraints.gpu_lock_required` be a hard gate at `submit_job` time (reject if Win GPU busy) or soft (queue until free)? Anthropic does soft-queue; our hardware affinity rule may favour hard-reject.
- **Q2**: Replay copies the spec verbatim. Should we copy artifacts too, or always re-execute fresh? Probably fresh (saves disk; matches "no cross-job state" rule).
- **Q3**: Where do the orama OpenClaw sub-agent definitions hand off to PT? Best guess: orama exposes a `/v1/agents/{name}/spec` endpoint returning JobSpec template; PT supervisor calls that, instantiates, submits.
- **Q4**: Cancellation propagation to subprocess — `asyncio.CancelledError` works for the asyncio task; we also need to send `SIGTERM`/`taskkill` to the spawned codex/gemini child. Probably handled in each worker's `dispatch()` cleanup.

---

## Sign-off

This brainstorm replaces the followup file's "no single supervisor" gap with one named class and one durable file format. Net code change is negative across both repos. Mac-verifiable path lands in 90 min of focused work. Win+Mac validation deferred to next LAN-live window.

— Claude (Sonnet 4.6, dispatched as Opus 4.7 for this brainstorm)
— Sub-agents consulted: Codex (gpt-5.3-codex, completed) — Gemini (quota-exhausted, retry pending)
