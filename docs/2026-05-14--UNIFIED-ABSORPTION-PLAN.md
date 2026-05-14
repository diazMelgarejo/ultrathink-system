# `docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md`

*Canonical spec for orama-system + Perpetua-Tools v1. Supersedes all prior PLAN / PLAN2 docs.*
*Source: `OpenClaw/v1/07-steps+combined.md` — synthesized from 4 prior design conversations.*

---

## § 0 — Critique and Corrections (Applied Before Canonicalization)

Three genuine errors in the source spec were corrected before adopting it. Everything
else is adopted verbatim.

### Error 1 — `contracts.py` creates a circular import (CORRECTED)

**Source spec says:** `models/contracts.py` lives in orama; PT imports it.

**Why it's wrong:** The one-way import is `orama → PT`. Putting contracts in orama
and importing them into PT (layer 2) reverses the dependency:
`PT → orama → PT` = circular.

**Correction:** Shared types (`OrchestrationSession`, `TaskEnvelope`, `WorkerAssignment`,
`WorkerResult`, `VerificationResult`) **live in PT** (`orchestrator/contracts.py`).
orama imports them from PT. This matches the existing `HardwareAffinityError` pattern.

### Error 2 — Pydantic V1 syntax (`@validator`) conflicts with repo mandate (CORRECTED)

**Source spec says:** `@validator("depth")` on `TaskEnvelope` and `JobSpec`.

**Why it's wrong:** `CLAUDE.md` mandates Pydantic V2 `@field_validator` (never
deprecated `@validator`). Every `@validator` in contracts becomes a silent no-op on
Pydantic v2 unless `from pydantic.v1 import ...` — which would pull in the compat shim.

**Correction:** All validators in `contracts.py` use `@field_validator` with
`mode='before'`. The `depth_must_be_zero` check becomes:
```python
@field_validator("depth", mode="before")
@classmethod
def depth_must_be_zero(cls, v: int) -> int:
    if v != 0:
        raise ValueError("Workers cannot spawn sub-workers in V1.")
    return v
```

### Error 3 — Env var name mismatch for Win host (CORRECTED)

**Source spec says:** `WIN_LM_STUDIO_HOST` and `WIN_LM_STUDIO_PORT`.

**Why it's wrong:** Our existing `.env.lmstudio`, `discover.py`, and `routing.json`
all use `LM_STUDIO_WIN_ENDPOINTS` (full URL, not host+port split). Introducing a new
env var name creates a second source of truth.

**Correction:** PT's `LMStudioWinBackend` reads `LM_STUDIO_WIN_ENDPOINTS` (full URL
like `http://192.168.254.102:1234`). Default is `REQUIRED_SET_IN_ENV` — invalid URL
that fails loudly, satisfying fail-closed.

### Steelman: What the spec gets definitively right

- **"Orchestrator" not "coordinator"** — enforced immediately in code (§ 2).
- **lmstudio-mac = always localhost** — already fixed in discover.py (commit `a82ab51`).
- **PT is runtime/state authority, orama is stateless** — matches existing architecture.
- **Verifier gates crystallization in code, not convention** — the right invariant level.
- **depth=0 validated, not trusted** — prevents worker recursion without relying on caller discipline.
- **XML/tags are prompt-rendering only** — prevents protocol confusion between wire format and LLM prompt format.
- **Fail-closed at gateways** — correctly scoped to `api_server.py`, not to topology tools like `discover.py` (discovery must degrade gracefully or the launchd watcher crashes every 60s).
- **Lockstep commits for shared contracts** — essential for a two-repo architecture.
- **GPU lock via `asyncio.Lock`** — right mechanism for single-GPU contention.

---

## § 1 — Governing Principles (Non-Negotiable)

These anchor every implementation decision. Contradicting them is wrong,
even if technically clever.

1. **"Orchestrator" is the only public control-plane term.** "Coordinator" may
   appear in internal prose comments to explain orchestrator *behavior*, but never
   in any public API, schema field, config key, route name, or doc heading.
   Applied to both repos immediately.

2. **Workers are one generic primitive.** Existing specialized roles (executor,
   verifier, crystallizer, autoresearch-coder, critic, refiner) are specializations
   of the generic worker contract — not a separate taxonomy. One template, many overlays.

3. **PT is the runtime/state authority.** Perpetua-Tools owns: job queue, job
   lifecycle, hardware affinity, model routing, GPU safety, LAN routing, durable
   artifacts, session state. orama never holds durable state.

4. **orama is the methodology/planning authority.** orama-system owns: stage
   planning, role templates, prompt contracts, verification rubrics, acceptance
   criteria. It is stateless. It returns plans, summaries, rubrics.

5. **Fail closed, always — at gateways.** Hardware affinity failures, missing
   `PERPETUATOOLSROOT` (at the API gateway), and unresolvable model IDs produce
   explicit errors — never silent fallback, never fail-open. Discovery tools
   (discover.py, network watcher) are exempt and must degrade gracefully.

6. **Workers do not spawn sub-workers in V1.** Hard rule. Max depth = 1 from
   orchestrator. Enforced as a runtime invariant in `JobSpec.depth` validation,
   not a convention.

7. **JSON/Pydantic is the canonical internal contract.** XML-like tags are
   prompt-rendering only — useful inside `<task-notification>` prompt sections
   or OpenClaw-facing text. Never as a Python wire format.

8. **Lockstep commits for shared contracts.** Any change to shared schema fields,
   exception classes, policy keys, or model IDs must commit to both repos in the
   same session. No partial updates.

---

## § 2 — Vocabulary Normalization (Immediate, Both Repos)

Grep acceptance criteria — all must return zero results after cleanup:

```bash
grep -r "Coordinator" . --include="*.py" --include="*.json" --include="*.yml"  # → 0 (except internal prose comments)
grep -r "coordinator" . --include="*.py" --include="*.json"                     # → 0 (same)
grep -r "deviceaffinity" . --include="*.py" --include="*.json"                  # → 0
grep -r "qwen3-coder" . --include="*.py"                                         # → 0
```

Note: `Perplexity-Tools` in CHANGELOG.md entries is **historical record** — acceptable.
Active code paths (`.py`, active `.md` docs, config `.json`) must use `Perpetua-Tools`.

| Banned term (public scope) | Correct term | Where |
|---|---|---|
| coordinator / Coordinator (role name) | orchestrator | All schemas, routes, config keys, doc headings |
| Perplexity-Tools (in active paths) | Perpetua-Tools | Active .py, config, docs |
| `deviceaffinity` | `affinity` | All JSON/YAML config, all Python readers |
| `qwen3-coder:14b` | `Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2` | Env defaults, any hardcoded model string |
| `WIN_LM_STUDIO_HOST` / `WIN_LM_STUDIO_PORT` | `LM_STUDIO_WIN_ENDPOINTS` | Env vars, backend config |

---

## § 3 — The Unified Schema: Five Shared Types

**Owner: Perpetua-Tools** (`orchestrator/contracts.py`). orama imports them.
All use Pydantic V2 field validators.

### 3.1 `OrchestrationSession` (PT-owned, durable)
```python
class OrchestrationSession(BaseModel):
    session_id: str           # uuid4, immutable
    created_at: datetime
    orchestrator_id: str
    objective: str
    constraints: list[str]
    acceptance_criteria: list[str]
    status: Literal["pending","running","verifying","done","failed","cancelled"]
    checkpoint: dict | None = None
    audit_log: list[AuditEvent] = []   # append-only, immutable
```

### 3.2 `TaskEnvelope` (generic worker input — all roles receive this)
Overlay fields go in `metadata`.
```python
class TaskEnvelope(BaseModel):
    job_id: str                        # uuid4, set by PT
    session_id: str
    parent_orchestrator_id: str
    role: str                          # "executor", "verifier", "crystallizer", etc.
    specialization: str | None = None  # "python-coding", "m&a-research", etc.
    intent: str
    prompt: str
    constraints: list[str] = []
    artifact_policy: ArtifactPolicy
    metadata: dict = {}
    handoff_summary: str | None = None # condensed output from previous worker
    depth: int = 0                     # ALWAYS 0 in V1 — validated server-side

    @field_validator("depth", mode="before")
    @classmethod
    def no_sub_workers(cls, v: int) -> int:
        if v != 0:
            raise ValueError("Workers cannot spawn sub-workers in V1.")
        return v
```

### 3.3 `WorkerAssignment` (orama plan → bridge input)
```python
class WorkerAssignment(BaseModel):
    role: str
    specialization: str | None = None
    intent: str
    constraints: list[str] = []
    expected_output_shape: str
    verification_rubric: str | None
    parallel_group: str | None = None  # same group = concurrent execution
```

### 3.4 `WorkerResult` (compact — no raw transcripts)
Written to `.state/jobs/<id>/result.json` **before** success event is emitted.
```python
class WorkerResult(BaseModel):
    job_id: str
    role: str
    status: Literal["done","failed","needs_revision"]
    summary: str                       # max ~500 tokens, no raw session logs
    artifacts: list[ArtifactRef] = []  # file paths, never raw transcripts
    tokens: TokenUsage
    errors: list[str] = []
    verification_hints: list[str] = [] # low-confidence signals for verifier
```

### 3.5 `VerificationResult` (gate before crystallization)
```python
class VerificationResult(BaseModel):
    job_id: str
    target_job_ids: list[str]
    verdict: Literal["approved","needs_revision","failed"]
    findings: list[str]
    revision_instructions: str | None
    # "approved"        → unlocks crystallization
    # "needs_revision"  → back to executor (NEVER to crystallizer)
    # "failed"          → halts session → MAESTRO gate (v2)
```

---

## § 4 — Orama Role Hierarchy (Methodology Layer)

Extend existing agent registry. All specialist roles inherit `worker_template`.

### 4.1 Worker template (add to agent_registry.json)
```json
"worker_template": {
  "type": "worker",
  "contract": "TaskEnvelope in, WorkerResult out",
  "hard_rules": [
    "Return compact summary only — no raw session logs in output",
    "Write artifacts to disk before returning status=done",
    "Set verification_hints for any low-confidence output",
    "depth is always 0 — workers do not enqueue sub-workers"
  ],
  "default_constraints": ["max_tokens:4096", "no_external_api_without_approval"]
}
```

### 4.2 Role table

| Orama Role | Stage | Worker? | Notes |
|---|---|---|---|
| `orchestrator` | All | **No** | Plans, emits `WorkerAssignment[]`. Never sends `TaskEnvelope`. |
| `context-agent` | context | Yes | Returns structured context summary |
| `architect-agent` | architecture | Yes | Returns design decisions + tradeoffs |
| `refiner-agent` | refinement | Yes | Iterates on prior artifact, returns diff+summary |
| `executor-agent` | execution | Yes | Writes code/artifacts; sets verification_hints |
| `verifier-agent` | verification | Yes | Returns `VerificationResult`; hard gate for crystallization |
| `crystallizer-agent` | crystallization | Yes | Returns final distilled output |

PT specializations that map to the same contract:
`top-level`, `strategy`, `coding`, `subagent`, `critic`, `autoresearch-coder`, `autoresearch-critic`.

---

## § 5 — Perpetua Runtime Layer

### 5.1 `JobSpec` extension (backward-compatible additions only)
```python
class JobSpec(BaseModel):
    # Existing fields — unchanged
    intent: str
    backend_hint: str | None = None
    constraints: list[str] = []
    metadata: dict = {}
    # New worker fields (all optional for backward compat)
    role: str | None = None
    specialization: str | None = None
    artifact_policy: str = "default"
    parent_orchestrator_id: str | None = None
    session_id: str | None = None
    depth: int = 0

    @field_validator("depth", mode="before")
    @classmethod
    def depth_must_be_zero(cls, v: int) -> int:
        if v != 0:
            raise ValueError("Workers cannot spawn sub-workers in V1.")
        return v
```

### 5.2 Role-aware backend resolution (priority order)
1. `role` + `specialization` → `ROLE_BACKEND_MAP` lookup
2. `intent` → existing intent-based routing (unchanged)
3. `backend_hint` → explicit override
4. Policy-defined default

All candidates pass through `policy.validate_or_raise()` — fail closed on affinity violation.

### 5.3 Role-to-backend map (ROLE_BACKEND_MAP in PT)

| Role | Specialization | Provider | Model |
|---|---|---|---|
| `executor-agent` | python-coding, test-writing, default | `lmstudio-win` | Qwen3.5-27B-Claude-4.6-Opus |
| `context-agent` | market-research, m&a-research, default | `lmstudio-mac` | mlx-community/Qwen3.5-9B-MLX-4bit |
| `verifier-agent` | default | `lmstudio-win` | Qwen3.5-27B-Claude-4.6-Opus |
| `crystallizer-agent` | default | `lmstudio-mac` | mlx-community/gemma-4-e4b-it-4bit |
| `architect-agent` | default | `lmstudio-win` | Qwen3.5-27B-Claude-4.6-Opus |
| `refiner-agent` | default | `lmstudio-mac` | mlx-community/Qwen3.5-9B-MLX-4bit |

**lmstudio-mac** is always `http://localhost:1234/v1` — LAN IP is docs/discovery metadata only, never in Mac-local config. (§ 1 rule, commit `a82ab51`.)

### 5.4 `LMStudioWinBackend` (PT — first-class, not hinted)

`LM_STUDIO_WIN_ENDPOINTS` from env only — never hardcoded. Default `REQUIRED_SET_IN_ENV`
(invalid URL, fails loudly). GPU lock for heavy models.

```python
class LMStudioWinBackend:
    _endpoint = os.getenv("LM_STUDIO_WIN_ENDPOINTS", "REQUIRED_SET_IN_ENV")
    _gpu_lock = asyncio.Lock()
    _heavy_models = {"Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2"}

    async def complete(self, spec: JobSpec) -> WorkerResult:
        is_heavy = spec.metadata.get("model") in self._heavy_models
        async with (self._gpu_lock if is_heavy else nullcontext()):
            response = await httpx.AsyncClient().post(
                f"{self._endpoint}/v1/chat/completions",
                json={"model": spec.metadata["model"], "messages": spec.metadata["messages"]},
                timeout=300,
            )
            response.raise_for_status()
            await self._persist_artifacts(spec.job_id, response.json())  # BEFORE success event
            return self._to_worker_result(spec, response.json())
```

---

## § 6 — Cross-Repo Bridge Adapter

File: `orama/agents/dispatcher.py` (`OramaToPTBridge`).
Converts orama execution plan → PT `JobSpec`s. Returns compact `WorkerResult`s to orama.

Key invariant — **enforced in code, not convention:**
```python
def dispatch_crystallization(self, plan, verification_result: VerificationResult):
    if verification_result.verdict != "approved":
        raise PermissionError(
            f"Crystallization blocked: verifier verdict={verification_result.verdict}"
        )
    # proceed
```

Parallel workers in the same `parallel_group` run via `asyncio.gather`.
Worker outputs containing raw session logs are rejected before returning to orchestrator
context (sidechain isolation).

---

## § 7 — DEFERRED to v2: MAESTRO + HITL Gate Classes

*Do not implement in v1. Doc-only reference.*

| Gate Class | Trigger | Required |
|---|---|---|
| 0 | Read-only context | None |
| 1 | Single-worker, reversible | None |
| 2 | Multi-worker parallel | Operator plan review |
| 3 | Swarm / always-on / external writes | `approval_token` (24h expiry) |
| 4 | Irreversible / financial / external APIs | PGP/GPG/OIDC identity |
| Emergency | Scope exceeded / unexpected writes / VRAM spike | Unconditional kill switch |

---

## § 8 — DEFERRED to v2: IDE Integration API

*Do not implement in v1. Doc-only reference.*

```
POST /session/start           → OrchestrationSession (session_id)
POST /session/{id}/plan       → orama execution plan
GET  /session/{id}/status     → current stage, running jobs
POST /session/{id}/approve    → submit approval_token
GET  /session/{id}/result     → final output + WorkerResults
POST /session/{id}/cancel     → graceful cancel + checkpoint
```

---

## § 9 — Fix Queue (All Open Items from Source Review)

### Priority 0 — Already resolved (verified 2026-05-14)
| ID | What | Status |
|---|---|---|
| R5 | PT `test_orama_bridge.py` import | ✅ 32/32 tests pass |
| R2 | `qwen3-coder:14b` in agent_launcher + api_server | ✅ not in active code path |

### Priority 1 — Safety hardening
| ID | File | Fix |
|---|---|---|
| R7 | `orama/api_server.py:202` | Conditional import shim for `HardwareAffinityError` from PT |
| R3 | `PT/agent_launcher.py` | Re-raise `HardwareAffinityError`; remove silent fallback lane |
| R9 | `orama/api_server.py` | Fail closed (`POLICY_UNAVAILABLE`) when `PERPETUATOOLSROOT` absent + explicit provider |
| R8 | `orama/scripts/discover.py` | ✅ already degrade-gracefully (correct for a topology tool — see § 0 critique) |
| R15 | `orama/alphaclawmanager.py` | Confirm `validate_routing_affinity` in real spawn path |

### Priority 2 — Test coverage
| ID | File | Fix |
|---|---|---|
| R10 | `orama/tests/test_api_server.py` | `HARDWARE_MISMATCH`: mac+win-only-model and win+mac-only-model |
| R11 | Same | `POLICY_UNAVAILABLE`: missing `PERPETUATOOLSROOT` + explicit provider |
| New | `PT/tests/test_contracts.py` | All 5 shared types; depth validator; Pydantic v2 compat |
| New | `PT/tests/test_job_spec.py` | New role fields; old call sites pass unchanged |
| New | `PT/tests/test_backend_routing.py` | Role routing → intent fallback → explicit override |
| New | `orama/tests/test_bridge.py` | Verifier blocks crystallization; parallel fan-out |
| New | `PT/tests/test_lmstudio_win.py` | OpenAI-compat endpoint shape; GPU lock behavior |

### Priority 3 — Schema/docs hygiene
| ID | Fix |
|---|---|
| R1 | `s/Perplexity-Tools/Perpetua-Tools/g` in active PT files (SOUL.md, afrp/, active config) |
| R6 | `deviceaffinity` → `affinity`; normalize device IDs: `win-rtx3080`, add `win-rtx5080` |
| R4/R13 | Add `PERPETUATOOLSROOT` + `LM_STUDIO_WIN_ENDPOINTS` to both `.env.example` files |
| R12 | Fix invalid CLI commands in docs; mark Mac repair done, Windows pending |
| New | Add `ROLE_BACKEND_MAP` table to both repos' docs |
| Now | Fix `"type": "coordinator"` → `"type": "orchestrator"` in `agent_registry.json` (both copies) |
| Now | Fix `agent.md` line 14: "Main coordinator" → "Main orchestrator" |

### Priority 4 — New architecture files
| File | Repo | Notes |
|---|---|---|
| `orchestrator/contracts.py` | **PT** (not orama) | All 5 shared types; Pydantic v2 |
| `orchestrator/supervisor.py` | PT | |
| `orchestrator/worker_registry.py` | PT | `ROLE_BACKEND_MAP` |
| `utils/audit_log.py` | PT | Append-only immutable event log |
| `utils/action_validator.py` | PT | |
| `agents/dispatcher.py` | orama | `OramaToPTBridge` |

### Priority 5 — Blocked (both machines online)
R14 (populate `shared:` in policy YAML), Windows config repair,
Grok/xAI fallback, HF Model EXIF registry, MCP v1.2 gate.

---

## § 10 — Integration Test Acceptance Criteria

**Scenario A:** Plan → execution → verification (approved) → crystallization.
All artifacts in `.state/jobs/`. Session status `done`.

**Scenario B:** Verifier returns `needs_revision`. Crystallization never called.
Second executor pass → verifier approves → crystallization proceeds.

**Scenario C:** `lmstudio-mac` + Windows-only model → `HARDWARE_MISMATCH`.
Missing `PERPETUATOOLSROOT` + explicit provider → `POLICY_UNAVAILABLE`. No fallback, no orphaned VRAM.

**Scenario D:** Regression guard. `deep_reasoning` and `code_analysis` routes unchanged.
Autoresearch lanes unchanged. Zero regressions on existing golden fixtures.

---

## § 11 — Lockstep Commit Sequence

1. **P0:** Already done. CI green.
2. **P1:** PT safety + orama safety → same session, single commit per repo.
3. **P2:** Tests independent order; full suite after each.
4. **P3:** `.env.example` + `deviceaffinity` rename → lockstep.
5. **P4:** New files per repo; integration tests last.
6. **P5:** Blocked — do not start until both machines online.

**Hard rule:** No shared contract change in one repo without the matching change
in the other, in the same session.
