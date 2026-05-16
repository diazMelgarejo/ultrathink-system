# Web-App Orchestration Implementation Plan

> **Status:** Backend Phases 1-2 shipped on 2026-05-16; Phases 3-9 remain.
> **Branch:** `web-app-orchestration-v2-implementation`
> **Required execution skill:** use `superpowers:subagent-driven-development` when splitting tasks across agents, or `superpowers:executing-plans` for inline execution.

## Goal

Build a FastAPI + React/Vite operator web app for previewing, launching, and inspecting
Perpetua-backed orama multi-agent swarms.

`portal_server.py` remains the LAN entry point and web host. Perpetua-Tools remains the
runtime/state authority. orama-system may add thin aggregation, preview, and safe proxy
routes, but it must not own durable job state.

## Eng Review Decisions

- **Do not implement the old minimal scaffold as-is.** It omitted launch, job detail,
  cancel, replay, artifact review, and contract-safe PT dispatch.
- **First implementation pass may modify orama-system only.** PT contract gaps must be
  handled through metadata-compatible requests or captured as a lockstep PT change.
- **Launch must fail closed.** Hardware or policy failures block launch, not warn and
  continue.
- **UI must not render raw transcripts.** Artifact screens show compact summaries and
  ArtifactRefs only.
- **The app-state route must aggregate real current payloads.** Do not return fake
  `jobs: []` or a nonexistent top-level `runtime`.

## Shipped In This Pass

- Added `GET /api/app/state` in `portal_server.py`.
- Added `POST /api/swarm/preview` in `portal_server.py`.
- Added `tests/test_portal_app_state.py`.
- Added `tests/test_swarm_preview.py`.
- Verified the full `orama-system` suite: `python3 -m pytest tests -q` → `170 passed`.

## Immediate Next

1. Implement Phase 3: `POST /api/swarm/launch` with explicit approval, server-side
   preview regeneration, fail-closed hardware policy checks, and PT `/v1/jobs`
   submissions using `metadata` for worker fields.
2. Implement Phase 4: `/api/jobs` list/detail/cancel/replay proxy routes.
3. Implement Phase 5: safe artifact index that redacts raw transcripts, raw prompts,
   tool traces, and model internals.
4. Start the React/Vite app only after the backend launch/jobs/artifact contracts are
   covered by tests.

## Current Repo Facts

### orama-system

- `portal_server.py` already exposes `/health`, `/api/status`, `/api/hardware-policy`,
  `/api/tools`, `/api/v1/jobs`, `/api/spawn-agent`, `/dashboard`, and `/`.
- `api_status()` currently returns `services`, `routing`, `hardware_policy`,
  `supervisor_jobs`, `tools`, and related probe data.
- `docs/dashboard/routing-dashboard.html` is useful vocabulary and visual reference,
  but should not remain the primary UI.
- `pyproject.toml` is Python-only today; Node/Vite tooling belongs under `web/`.

### Perpetua-Tools

- PT exposes `/runtime`, `/models`, `/models/route`, `/orchestrate`, `/activity`,
  `/user-input`, `/v1/jobs`, `/v1/jobs/{id}`, `/cancel`, and `/replay`.
- PT `JobSpec` already contains role fields such as `role`, `specialization`,
  `session_id`, `parent_orchestrator_id`, `artifact_policy`, and `depth`.
- PT FastAPI `_JobSubmitRequest` currently accepts only `intent`, `prompt`,
  `backend_hint`, `constraints`, and `metadata`. Therefore orama-system launch must
  either encode worker fields in `metadata` or stop and propose a PT API change.

## File Plan

- Modify: `portal_server.py`
- Modify: `pyproject.toml`
- Modify: `docs/v2/16-web-app-orchestration-plan.md`
- Create: `tests/test_portal_app_state.py`
- Create: `tests/test_swarm_preview.py`
- Create: `tests/test_swarm_launch.py`
- Create: `tests/test_portal_jobs_proxy.py`
- Create: `tests/test_portal_artifacts.py`
- Create: `web/package.json`
- Create: `web/index.html`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/api/client.ts`
- Create: `web/src/api/types.ts`
- Create: `web/src/features/command-center/CommandCenter.tsx`
- Create: `web/src/features/swarm-composer/SwarmComposer.tsx`
- Create: `web/src/features/runs/RunTimeline.tsx`
- Create: `web/src/features/routing/RoutingHardware.tsx`
- Create: `web/src/features/artifacts/ArtifactsReview.tsx`
- Create: `web/src/styles/global.css`

## Phase 0 — Contract Lock

- [x] Confirm PT base URL resolution uses existing environment/config patterns in
  `portal_server.py`.
- [x] Add a comment near the new portal models stating PT remains the durable state
  owner.
- [~] Define portal DTOs that map cleanly to current PT HTTP contracts:
  `AppStateSection` and `SwarmPreviewRequest` are implemented; launch, job proxy,
  and artifact DTOs remain.
- [ ] Use a metadata-compatible launch shape for first pass:
  - top-level PT request fields: `intent`, `prompt`, `backend_hint`, `constraints`,
    `metadata`
  - metadata fields: `role`, `specialization`, `session_id`,
    `parent_orchestrator_id`, `artifact_policy`, `expected_output_shape`,
    `verification_rubric`
- [ ] Add a lockstep-change note if role fields must move from `metadata` to PT
  `_JobSubmitRequest` later.

## Phase 1 — Real App-State Aggregation

### Backend behavior

- [x] Add `GET /api/app/state`.
- [x] Call existing `api_status()` for portal health, routing, hardware, and tools.
- [x] Fetch PT `/runtime`, `/models`, `/activity`, and `/v1/jobs` with short
  timeouts.
- [x] Return partial-failure sections instead of failing the whole payload when one
  service is down.
- [x] Map current `supervisor_jobs` into `jobs` when PT `/v1/jobs` is unavailable.
- [x] Do not invent a top-level `runtime` from `api_status()`; source it from PT
  `/runtime` or mark it unavailable.

### Tests

- [x] `test_app_state_contains_real_sections`
- [x] `test_app_state_uses_supervisor_jobs_fallback`
- [x] `test_app_state_reports_pt_partial_failure`
- [x] No-live-network coverage via mocked `httpx.AsyncClient`

### Verification

- [x] `python3 -m pytest tests/test_portal_app_state.py -q`

## Phase 2 — Swarm Preview With Routing Awareness

### Backend behavior

- [x] Add `POST /api/swarm/preview`.
- [x] Validate non-empty objective and bounded string lengths.
- [x] Produce a five-role preview for first pass:
  `context-agent`, `architect-agent`, `executor-agent`, `verifier-agent`,
  `crystallizer-agent`.
- [x] Include `role`, `specialization`, `intent`, `expected_output_shape`,
  `verification_rubric`, `backend_hint`, and `routing_source`.
- [x] Prefer PT `/models/route` or role routing data where available.
- [x] Fall back to deterministic local routing metadata when PT routing is unavailable.
- [x] Always return `dispatch_allowed: false` for preview.

### Tests

- [x] `test_swarm_preview_returns_worker_assignments`
- [x] `test_swarm_preview_rejects_empty_objective`
- [x] `test_swarm_preview_includes_backend_hints`
- [x] `test_swarm_preview_marks_routing_fallback`

### Verification

- [x] `python3 -m pytest tests/test_swarm_preview.py -q`

## Phase 3 — Fail-Closed Swarm Launch

### Backend behavior

- [ ] Add `POST /api/swarm/launch`.
- [ ] Require an explicit `approved: true` flag in the request.
- [ ] Re-run preview generation server-side before dispatch; do not trust the browser's
  submitted assignments blindly.
- [ ] Check hardware policy and routing readiness before every dispatch.
- [ ] If any policy check fails, return `409` with `blocked: true` and no PT jobs.
- [ ] Submit one PT `/v1/jobs` request per approved worker assignment.
- [ ] Encode worker fields in PT `metadata` for first pass.
- [ ] Return accepted job ids, blocked assignments, and the generated session id.
- [ ] Do not call the existing `/api/spawn-agent` route from this path because that
  route currently treats affinity failures as warnings.

### Tests

- [ ] `test_swarm_launch_requires_approval`
- [ ] `test_swarm_launch_blocks_on_hardware_policy`
- [ ] `test_swarm_launch_submits_metadata_compatible_pt_jobs`
- [ ] `test_swarm_launch_returns_partial_dispatch_failure`
- [ ] `test_swarm_launch_never_uses_spawn_agent_warning_path`

### Verification

- [ ] `python -m pytest tests/test_swarm_launch.py -q`

## Phase 4 — Job Proxy Routes

### Backend behavior

- [ ] Add `GET /api/jobs`.
- [ ] Add `GET /api/jobs/{job_id}`.
- [ ] Add `POST /api/jobs/{job_id}/cancel`.
- [ ] Add `POST /api/jobs/{job_id}/replay`.
- [ ] Proxy PT `/v1/jobs` responses without mutating durable state in orama-system.
- [ ] Normalize unavailable PT into explicit UI-safe error payloads.

### Tests

- [ ] `test_jobs_proxy_lists_pt_jobs`
- [ ] `test_jobs_proxy_gets_detail`
- [ ] `test_jobs_proxy_cancel_posts_to_pt`
- [ ] `test_jobs_proxy_replay_posts_to_pt`
- [ ] `test_jobs_proxy_handles_pt_down`

### Verification

- [ ] `python -m pytest tests/test_portal_jobs_proxy.py -q`

## Phase 5 — Safe Artifact Index

### Backend behavior

- [ ] Add `GET /api/jobs/{job_id}/artifacts`.
- [ ] Fetch PT job detail.
- [ ] Extract only compact summaries, `ArtifactRef`-like entries, verification findings,
  and replay instructions.
- [ ] Redact or omit raw transcripts, raw prompts, tool traces, and model internals.
- [ ] Include `redacted_fields` so the UI can say content was intentionally withheld.
- [ ] Return a stable empty artifact list for jobs without artifacts.

### Tests

- [ ] `test_artifacts_returns_artifact_refs`
- [ ] `test_artifacts_redacts_raw_transcript_fields`
- [ ] `test_artifacts_handles_missing_result`
- [ ] `test_artifacts_handles_pt_404`

### Verification

- [ ] `python -m pytest tests/test_portal_artifacts.py -q`

## Phase 6 — React/Vite App Foundation

### Frontend setup

- [ ] Create `web/package.json` with React, Vite, TypeScript, and lucide icons.
- [ ] Keep Vite and TypeScript in `devDependencies`; keep React packages in
  `dependencies`.
- [ ] Create `web/index.html`.
- [ ] Create `web/src/main.tsx`.
- [ ] Create `web/src/App.tsx` with tab routing.
- [ ] Create `web/src/api/types.ts` matching portal DTOs.
- [ ] Create `web/src/api/client.ts` with typed fetch helpers and abort timeouts.
- [ ] Create `web/src/styles/global.css` using a restrained operational palette.

### Design constraints

- [ ] First screen is the app, not a landing page.
- [ ] Tabs: Command Center, Swarm Composer, Runs, Routing, Artifacts.
- [ ] Use dense tables, timelines, chips, icon buttons, and approval controls.
- [ ] Avoid raw decorative gradients and oversized marketing typography.
- [ ] Keep cards for repeated items only; page sections are unframed layouts or full
  bands.

### Verification

- [ ] `cd web && npm install`
- [ ] `cd web && npm run build`

## Phase 7 — Feature Screens

### Command Center

- [ ] Poll `/api/app/state`.
- [ ] Render PT, orama API, portal, and gateway readiness.
- [ ] Show runtime, model, activity, budget, and blocked-action summaries.
- [ ] Show partial failures without blanking the whole app.

### Swarm Composer

- [ ] Form fields: objective, task type, optimize-for, preferred device.
- [ ] Preview role assignments before launch.
- [ ] Show backend hints and policy gates.
- [ ] Require explicit launch approval.
- [ ] Surface launch blocked states from `409` responses.

### Runs

- [ ] List jobs from `/api/jobs`.
- [ ] Show selected job detail.
- [ ] Provide cancel and replay controls.
- [ ] Make waiting-input, failed, cancelled, and succeeded states visually distinct.

### Routing & Hardware

- [ ] Render model registry and backend status from app-state.
- [ ] Port useful vocabulary from `docs/dashboard/routing-dashboard.html`.
- [ ] Show fail-closed affinity messages.

### Artifacts

- [ ] Fetch `/api/jobs/{job_id}/artifacts`.
- [ ] Render summaries, ArtifactRefs, verification findings, and replay instructions.
- [ ] Display redaction notices for withheld raw content.

## Phase 8 — Serve Build From FastAPI

- [ ] Mount `web/dist/assets` at `/assets` only when the build exists.
- [ ] Update `/` to serve `web/dist/index.html` when present.
- [ ] Preserve compatibility for existing `/dashboard`.
- [ ] Include `web/dist` in package metadata only after it exists.
- [ ] Add backend tests for root fallback and static mount behavior if practical.

## Phase 9 — Verification Gate

- [ ] `python -m pytest tests/test_portal_app_state.py tests/test_swarm_preview.py tests/test_swarm_launch.py tests/test_portal_jobs_proxy.py tests/test_portal_artifacts.py -q`
- [ ] Existing focused portal tests still pass.
- [ ] `cd web && npm run build`
- [ ] Start the local portal server.
- [ ] Open the app in Browser/IAB on desktop and mobile-sized viewports.
- [ ] Verify the app is nonblank, tabs fit, no text overlaps, and blocked launch states
  are visible.
- [ ] Verify no raw transcript fields render in Artifacts.

## Subagent Work Split

Use separate subagents only after Phase 0 is locked:

- **Backend API worker:** Phases 1-5, owns `portal_server.py` and backend tests.
- **Frontend worker:** Phases 6-7, owns `web/`.
- **Packaging worker:** Phase 8, owns static serving and package metadata.
- **Verification worker:** Phase 9, read-only after implementation.

Workers are not alone in the codebase. They must not revert edits made by other agents,
and they must adapt to current branch state before editing.

## Commit Plan

1. `feat(portal): add app state and preview APIs` — current shipped commit.
3. `feat(portal): add launch jobs and artifact proxy APIs`
4. `feat(web): add React orchestration command center`
5. `feat(portal): serve React web app`

## Remaining Decisions Before Coding

- Whether to keep first-pass launch as a metadata-compatible PT shim or create a
  lockstep PT branch that extends `_JobSubmitRequest`.
- Whether launch should fan out one PT job per worker in orama-system or wait for a
  future PT swarm endpoint.
- Whether design review must approve static concepts before React implementation.
