# 16 — Web-App Orchestration Plan

> **Status:** Backend API facade shipped on 2026-05-16; React/Vite frontend remains.
> **Branch:** `web-app-orchestration-v2-plan`  
> **Date:** 2026-05-16  
> **Decision:** Target **FastAPI API + React/Vite frontend**. No progressive-HTML or hybrid extraction path.
> **Implementation branch:** `web-app-orchestration-v2-implementation`
> **Eng review update:** launch, jobs, artifacts, and PT contract handling shipped before frontend build-out.

---

## 1. Intent

Transform the existing `orama-system` portal/dashboard into a real operator web app for the
three-layer stack:

- **orama-system:** methodology/planning authority, stateless reasoning bridge, UI/API host.
- **Perpetua-Tools:** runtime/state authority, job queue, hardware policy, model routing, supervisor.
- **AlphaClaw/OpenClaw:** infrastructure/gateway layer, referenced through existing APIs only.

The result should repurpose the old portal and routing dashboard, but the target product is a
stateful web app, not a refreshed static dashboard and not a marketing page.

---

## 2. Inputs Reviewed

- `../v2/8.md` — hybrid MCP + Code DSL + Skills guide.
- `docs/v2/08-technical-architecture-review.md` — MiniGraph, GossipBus, Sentinel, MAESTRO/SWARM.
- `docs/v2/02-modules/multi-agent-network.md` — 7-agent carry-over into v2.
- `docs/v2/14-supervisor-and-anthropic-patterns.md` — V1 supervisor API and V2 persistence direction.
- `docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md` — PT owns runtime/state; orama owns methodology.
- `portal_server.py` — current inline FastAPI portal, status APIs, service controls, dashboard route.
- `docs/dashboard/routing-dashboard.html` — current static dark routing dashboard.
- `Perpetua-Tools/orchestrator/fastapi_app.py` — PT routes for runtime, models, `/orchestrate`,
  `/v1/jobs`, user input, autoresearch, and activity.
- `Perpetua-Tools/orchestrator/{supervisor.py,contracts.py,worker_registry.py,orama_bridge.py}` —
  supervisor primitives, shared contracts, role routing, and orama bridge.

---

## 3. Product Thesis

The UI should make the orchestration stack inspectable without exposing raw agent logs. The operator
needs to answer:

1. Can I launch this swarm safely?
2. Which models/devices will be used, and why?
3. What is running, waiting, failed, or blocked on human input?
4. What did each worker produce as compact summaries and artifacts?
5. What policy, budget, or hardware gate stopped the next step?

The app should feel like an operations console: dense, quiet, scan-friendly, and built for repeated
use.

---

## 4. Chosen Architecture

### Target Shape

```
orama-system/
├── portal_server.py          # FastAPI host + thin aggregation API + static web mount
├── api_server.py             # existing /ultrathink reasoning bridge, kept compatible
├── web/                      # React + Vite app
│   ├── src/api/              # typed fetch clients for portal + PT + orama
│   ├── src/components/       # app shell, tables, timelines, status chips
│   ├── src/features/         # command center, composer, runs, routing, artifacts
│   └── src/styles/           # tokens and global CSS
└── docs/v2/                  # architecture docs and plan
```

### Why This Path

React/Vite is the right target because the app needs local UI state, tabbed workflows, filters,
polling, detail panes, forms, lifecycle timelines, and approval gates. Keeping the orchestration
backend in Python preserves the current repo identity and avoids moving runtime authority out of
Perpetua-Tools.

`portal_server.py` remains the LAN entry point. It serves the built frontend and exposes only thin
aggregation routes. PT remains the source of durable state.

---

## 5. Two-Repo Review

### orama-system Current Fit

| Existing File | Use In Web App |
| --- | --- |
| `portal_server.py` | Keep as FastAPI web host; split inline UI into React build; add aggregation routes |
| `api_server.py` | Keep `/ultrathink`, `/health`, `/runtime-state` compatible |
| `docs/dashboard/routing-dashboard.html` | Mine UI concepts and data vocabulary; do not keep as primary UI |
| `docs/v2/*` | Product and architecture source of truth |
| `bin/agents/*` | Role vocabulary for swarm composer and WorkerAssignment previews |

### Perpetua-Tools Current Fit

| Existing File | Use In Web App |
| --- | --- |
| `orchestrator/fastapi_app.py` | Backing API for runtime, models, `/orchestrate`, `/v1/jobs`, user queue |
| `orchestrator/supervisor.py` | Job lifecycle source; file-backed V1 state remains acceptable initially |
| `orchestrator/contracts.py` | UI payload vocabulary: WorkerAssignment, WorkerResult, ArtifactRef, VerificationResult |
| `orchestrator/worker_registry.py` | Role/backend map shown in routing and composer previews |
| `orchestrator/orama_bridge.py` | Shows transport used: MCP vs HTTP fallback |

### Boundary Rule

The browser may read combined views through `portal_server.py`, but durable operations still land in
PT. orama-system must not become the state owner.

---

## 6. Primary Screens

### 6.1 Command Center

Shows stack health and readiness:

- PT, orama API, portal, OpenClaw gateway.
- Mac/Windows LM Studio and Ollama availability.
- Active route, fallback chain, thread ceiling, daily budget, blocked actions.
- Runtime bootstrap status from PT `/runtime`.

### 6.2 Swarm Composer

Turns an operator task into a previewable swarm plan:

- Objective, task type, optimize-for, preferred device.
- Role plan preview from orama methodology.
- WorkerAssignment rows: role, specialization, intent, expected output, verification rubric.
- Approval state for high-risk launch paths.

### 6.3 Run Timeline

Visualizes PT supervisor state:

- Jobs from `/v1/jobs`.
- Detail from `/v1/jobs/{job_id}`.
- Statuses: queued, running, waiting_input, succeeded, failed, cancelled.
- Cancel/replay controls.

### 6.4 Routing & Hardware

Modernizes the existing routing dashboard:

- Model registry and backend health.
- Role/backend map from PT.
- Dispatch priority chain and fail-closed affinity messages.
- MCP/HTTP transport status where relevant.

### 6.5 Artifacts & Review

Shows compact outputs only:

- WorkerResult summary.
- ArtifactRefs with path, mime type, size, sha256 when present.
- VerificationResult findings and replay instructions.
- No raw transcripts or model internals.

---

## 7. Backend Contract Plan

Existing services should remain source of truth:

| Concern | Source |
| --- | --- |
| Health/topology | portal `/api/status`, PT `/health`, orama `/health` |
| Runtime bootstrap | PT `/runtime`, `/runtime/bootstrap` |
| Model routing | PT `/models`, `/models/route`, `/orchestrate` |
| Supervisor jobs | PT `/v1/jobs`, `/v1/jobs/{id}`, `/cancel`, `/replay` |
| User queue | PT `/user-input`, `/user-input/next`, `/user-input/status` |
| orama reasoning | orama `/ultrathink` or PT `orama_bridge` |
| Hardware policy | portal `/api/hardware-policy`, PT policy helpers |

New portal routes should be aggregation or planning routes only:

- `GET /api/app/state` — health + runtime + models + jobs + activity in one payload.
- `POST /api/swarm/preview` — create a stateless WorkerAssignment preview, no dispatch.
- `POST /api/swarm/launch` — submit accepted plan to PT supervisor.
- `GET /api/jobs/{id}/artifacts` — safe ArtifactRef index, no raw transcript content.

### 7.1 Contract Lock From Eng Review

The implementation plan must account for current PT HTTP reality:

- PT `JobSpec` already has worker fields such as `role`, `specialization`, `session_id`,
  `parent_orchestrator_id`, `artifact_policy`, and `depth`.
- PT FastAPI `_JobSubmitRequest` currently exposes only `intent`, `prompt`, `backend_hint`,
  `constraints`, and `metadata`.
- First-pass orama launch may submit one PT `/v1/jobs` request per worker and encode worker
  fields in `metadata`.
- If role fields must become top-level PT HTTP fields, stop and create a lockstep PT change
  instead of silently drifting the portal contract.
- `/api/swarm/launch` must not call the old `/api/spawn-agent` path, because launch needs
  fail-closed policy behavior.

---

## 8. Hybrid MCP + DSL + Skills Mapping

The web app should implement the `../v2/8.md` hybrid pattern:

1. **MCP execution:** keep MCP optional and transport-agnostic for PT/orama.
2. **Code DSL:** introduce a small swarm DSL for plan generation and review.
3. **Skills:** use `SKILL.md`, `docs/LESSONS.md`, and role specs as persistent knowledge.

Draft DSL shape:

```python
swarm = SwarmPlan(objective="Refactor API boundary")
swarm.context(role="context-agent", specialization="codebase-map")
swarm.parallel("implementation", [
    Worker(role="executor-agent", specialization="python-coding", intent="patch"),
    Worker(role="verifier-agent", intent="test"),
])
swarm.verify(rubric="pytest green, contract unchanged")
swarm.crystallize()
```

The UI renders this plan before launch. After approval, portal converts it into PT-compatible
`JobSpec` submissions.

---

## 9. Design Direction

Use the existing dark routing dashboard as raw material, but mature it:

- Quiet operational UI, not decorative SaaS marketing.
- Dense but legible panels, 8px-or-smaller radius, restrained borders.
- Tabs for Command Center / Composer / Runs / Routing / Artifacts.
- Tables and timelines over card sprawl.
- Strong status language: `ready`, `blocked`, `waiting_input`, `failed`, `cancelled`.
- No raw chain-of-thought or raw transcripts.

Design concept pass before implementation:

1. Command Center desktop.
2. Swarm Composer with approval gate.
3. Run Timeline + Artifact Review.
4. Mobile/tablet collapsed operations view.

---

## 10. Implementation Phases

### Shipped — 2026-05-16

- `GET /api/app/state` aggregates portal status plus PT `/runtime`, `/models`,
  `/activity`, and `/v1/jobs` with per-section availability/error metadata.
- `POST /api/swarm/preview` returns the five-role stateless swarm preview with
  backend hints from PT `/models/route` when available and deterministic local
  fallback routing otherwise.
- `POST /api/swarm/launch` requires `approved: true`, regenerates preview server-side,
  fails closed on hardware policy violations, and submits PT `/v1/jobs` requests with
  worker fields encoded in `metadata`.
- `/api/jobs` list/detail/cancel/replay proxy routes keep PT as durable state owner.
- `/api/jobs/{job_id}/artifacts` returns summaries, ArtifactRefs, verification data,
  replay instructions, and redaction notices without raw transcripts or prompts.
- Added mocked-network backend tests for app-state, preview, launch, jobs, and artifacts.
- Verification: `python3 -m pytest tests -q` → `183 passed`.

### Next Backend Work

No backend blocker remains for first-pass frontend work. The next implementation step is
the React/Vite shell and typed clients. Future backend hardening can replace portal-side
fan-out with a PT-native swarm endpoint, but that is not required for the first UI.

### Phase 0 — Plan Lock

- [x] Review this doc.
- [x] Confirm `web/` as the React/Vite path.
- [x] Confirm browser calls portal aggregation routes, not PT directly.

### Phase 1 — API Facade

- [~] Add typed Pydantic models for app-state, preview, launch, jobs, and artifacts.
  App-state and preview are shipped; launch/jobs/artifacts remain.
- [x] Add `GET /api/app/state` using real current portal/PT payloads.
- [x] Add `POST /api/swarm/preview` with routing-aware backend hints.
- [x] Add `POST /api/swarm/launch` with explicit approval and fail-closed policy checks.
- [x] Add job proxy routes for list/detail/cancel/replay.
- [x] Add safe artifact index route that redacts raw transcripts and model internals.
- [x] Add tests with mocked PT/orama responses.

### Phase 2 — React/Vite Shell

- Add `web/` project.
- Build app shell, navigation, tabs, polling client, global tokens.
- Serve Vite build from `portal_server.py`.

### Phase 3 — Command Center + Routing

- Port health cards, model registry, and routing dashboard into React components.
- Preserve current `/dashboard` as redirect or compatibility route.

### Phase 4 — Swarm Composer

- Render previewed WorkerAssignment plan.
- Add launch flow through `POST /api/swarm/launch`.
- Show policy and approval gates before dispatch.

### Phase 5 — Runs + Artifacts

- Wire PT `/v1/jobs` list/detail/cancel/replay.
- Render compact summaries, ArtifactRefs, verification findings.

### Phase 6 — DSL + MCP Trace

- Add minimal DSL runtime around WorkerAssignment creation.
- Show transport used: HTTP vs MCP fallback.
- Add developer trace panel for payloads and contract schemas.

---

## 11. Risks

- **State ownership drift:** UI must not make orama durable; PT remains state authority.
- **Raw transcript leakage:** show summaries and artifacts only.
- **Hardware fail-open:** every launch path must preserve pre-spawn affinity checks.
- **Cross-repo contract drift:** shared type changes require lockstep commits.
- **Node toolchain creep:** document dev/prod commands and keep Python service primary.
- **Portal file size:** avoid adding more inline HTML to `portal_server.py`.

---

## 12. Open Questions

1. Should the future hardened version replace portal-side fan-out with a PT-native
   swarm endpoint?
2. What minimum approval gate is required for launch: visual confirmation only, or
   token-backed HITL?
3. Should design review approve static concepts before React implementation?

---

## 13. Initial Acceptance Criteria

- Existing `/health`, `/api/status`, `/dashboard`, and `/ultrathink` behavior remains compatible.
- Operator can preview a swarm plan before launching.
- Operator can see model/device routing before dispatch.
- Operator can list, inspect, cancel, and replay PT supervisor jobs.
- Worker outputs shown in UI are compact summaries or artifact refs, not raw transcripts.
- Hardware affinity failures are visible and block launch.
- Implementation includes Browser/IAB verification across desktop and mobile.
