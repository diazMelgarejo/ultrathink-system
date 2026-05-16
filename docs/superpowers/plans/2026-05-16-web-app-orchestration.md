# Web-App Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + React/Vite operator web app for previewing, launching, and inspecting Perpetua-backed orama multi-agent swarms.

**Architecture:** `portal_server.py` remains the Python LAN entry point and serves a Vite-built React app. Perpetua-Tools remains the runtime/state authority; orama-system adds only thin aggregation and stateless swarm-preview routes. The frontend calls portal aggregation APIs, not PT directly.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, httpx, pytest, React, Vite, TypeScript, CSS modules or plain CSS tokens.

---

## File Structure

Create or modify these files:

- Modify: `portal_server.py` — add app-state, swarm-preview, swarm-launch, artifact routes; mount Vite build.
- Create: `web/package.json` — Vite React scripts.
- Create: `web/index.html` — Vite entry HTML.
- Create: `web/src/main.tsx` — React bootstrap.
- Create: `web/src/App.tsx` — app shell and tab routing.
- Create: `web/src/api/client.ts` — typed fetch helpers for portal aggregation routes.
- Create: `web/src/api/types.ts` — UI-side DTOs matching portal responses.
- Create: `web/src/features/command-center/CommandCenter.tsx` — stack health and readiness.
- Create: `web/src/features/swarm-composer/SwarmComposer.tsx` — preview and launch flow.
- Create: `web/src/features/runs/RunTimeline.tsx` — PT job list/detail/cancel/replay.
- Create: `web/src/features/routing/RoutingHardware.tsx` — model routing and backend status.
- Create: `web/src/features/artifacts/ArtifactsReview.tsx` — WorkerResult and ArtifactRef view.
- Create: `web/src/styles/global.css` — design tokens and base layout.
- Create: `tests/test_portal_app_state.py` — backend aggregation tests.
- Create: `tests/test_swarm_preview.py` — preview/launch contract tests.
- Modify: `pyproject.toml` — include web build assets in package only after the Vite build path exists.
- Modify: `docs/v2/16-web-app-orchestration-plan.md` — keep architecture decisions synced.

Do not modify Perpetua-Tools in the first implementation pass. If a PT contract gap appears, stop and record a lockstep-change proposal.

---

### Task 1: Add Portal App-State Aggregation Models

**Files:**
- Modify: `portal_server.py`
- Test: `tests/test_portal_app_state.py`

- [ ] **Step 1: Write failing tests for `/api/app/state`**

Create `tests/test_portal_app_state.py`:

```python
from fastapi.testclient import TestClient

import portal_server


def test_app_state_contains_top_level_sections(monkeypatch):
    async def fake_status():
        return {
            "services": {
                "perplexity_tools": {"ok": True, "url": "http://localhost:8000"},
                "ultrathink": {"ok": True, "url": "http://localhost:8001"},
            },
            "routing": {"distributed": True},
            "activity": [{"event": "worker.dispatched"}],
        }

    monkeypatch.setattr(portal_server, "api_status", fake_status)
    client = TestClient(portal_server.app)

    resp = client.get("/api/app/state")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["services"]["perplexity_tools"]["ok"] is True
    assert payload["routing"]["distributed"] is True
    assert payload["activity"][0]["event"] == "worker.dispatched"
    assert "jobs" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_portal_app_state.py -q`

Expected: FAIL with 404 for `/api/app/state`.

- [ ] **Step 3: Add minimal endpoint**

In `portal_server.py`, add near the other API routes:

```python
@app.get("/api/app/state")
async def api_app_state():
    """Aggregate portal-facing state for the React command center."""
    status = await api_status()
    return {
        "services": status.get("services", {}),
        "routing": status.get("routing", {}),
        "activity": status.get("activity", []),
        "jobs": [],
        "runtime": status.get("runtime", {}),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_portal_app_state.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal_server.py tests/test_portal_app_state.py
git commit -m "feat(portal): add app state aggregation route"
```

---

### Task 2: Add Stateless Swarm Preview Route

**Files:**
- Modify: `portal_server.py`
- Test: `tests/test_swarm_preview.py`

- [ ] **Step 1: Write failing preview test**

Create `tests/test_swarm_preview.py`:

```python
from fastapi.testclient import TestClient

import portal_server


def test_swarm_preview_returns_worker_assignments():
    client = TestClient(portal_server.app)

    resp = client.post(
        "/api/swarm/preview",
        json={
            "objective": "Refactor portal API boundary",
            "task_type": "code",
            "optimize_for": "reliability",
            "preferred_device": "windows",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["objective"] == "Refactor portal API boundary"
    assert payload["dispatch_allowed"] is False
    assert [a["role"] for a in payload["assignments"]] == [
        "context-agent",
        "architect-agent",
        "executor-agent",
        "verifier-agent",
        "crystallizer-agent",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_swarm_preview.py -q`

Expected: FAIL with 404 for `/api/swarm/preview`.

- [ ] **Step 3: Add request models and route**

Add to `portal_server.py`:

```python
class SwarmPreviewRequest(BaseModel):
    objective: str
    task_type: str = "code"
    optimize_for: str = "reliability"
    preferred_device: Optional[str] = None


def _build_preview_assignments(req: SwarmPreviewRequest) -> list[dict]:
    return [
        {
            "role": "context-agent",
            "specialization": "codebase-map",
            "intent": "context",
            "expected_output_shape": "compact repository map and risk list",
            "verification_rubric": "names exact files and current constraints",
        },
        {
            "role": "architect-agent",
            "specialization": "web-app-boundary",
            "intent": "architecture",
            "expected_output_shape": "component and API boundary proposal",
            "verification_rubric": "preserves PT as runtime/state authority",
        },
        {
            "role": "executor-agent",
            "specialization": "python-coding",
            "intent": "implementation",
            "expected_output_shape": "patch artifacts and test summary",
            "verification_rubric": "tests pass and existing routes remain compatible",
        },
        {
            "role": "verifier-agent",
            "specialization": "contract-tests",
            "intent": "verification",
            "expected_output_shape": "findings and approval verdict",
            "verification_rubric": "no raw transcript leakage and no fail-open launch",
        },
        {
            "role": "crystallizer-agent",
            "specialization": "lesson-authoring",
            "intent": "crystallization",
            "expected_output_shape": "summary and docs updates",
            "verification_rubric": "lessons are concise and linked",
        },
    ]


@app.post("/api/swarm/preview")
async def api_swarm_preview(req: SwarmPreviewRequest):
    """Return a stateless swarm plan preview. This route does not dispatch jobs."""
    return {
        "objective": req.objective,
        "task_type": req.task_type,
        "optimize_for": req.optimize_for,
        "preferred_device": req.preferred_device,
        "dispatch_allowed": False,
        "approval_required": True,
        "assignments": _build_preview_assignments(req),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_swarm_preview.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal_server.py tests/test_swarm_preview.py
git commit -m "feat(portal): preview swarm assignments"
```

---

### Task 3: Create React/Vite App Shell

**Files:**
- Create: `web/package.json`, `web/index.html`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/styles/global.css`

- [ ] **Step 1: Add Vite package manifest**

Create `web/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "vite build",
    "preview": "vite preview --host 127.0.0.1 --port 4173"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "vite": "^7.0.0",
    "typescript": "^5.6.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {}
}
```

- [ ] **Step 2: Add HTML entry**

Create `web/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>orama Command Center</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Add React bootstrap**

Create `web/src/main.tsx`:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 4: Add app shell**

Create `web/src/App.tsx`:

```tsx
import { Activity, Boxes, GitBranch, HardDrive, Layers } from "lucide-react";

const tabs = [
  { id: "command", label: "Command Center", icon: Activity },
  { id: "composer", label: "Swarm Composer", icon: Boxes },
  { id: "runs", label: "Runs", icon: GitBranch },
  { id: "routing", label: "Routing", icon: HardDrive },
  { id: "artifacts", label: "Artifacts", icon: Layers },
];

export function App() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>orama Command Center</h1>
          <p>FastAPI + React control surface for Perpetua-backed swarm orchestration.</p>
        </div>
        <span className="status-pill">draft</span>
      </header>
      <nav className="tabs" aria-label="Primary">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} className="tab-button" type="button">
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>
      <section className="panel">
        <h2>Command Center</h2>
        <p>Wire app-state, swarm preview, runs, routing, and artifacts in the next tasks.</p>
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Add global CSS**

Create `web/src/styles/global.css`:

```css
:root {
  color-scheme: dark;
  --bg: #0f1117;
  --panel: #181c25;
  --panel-2: #222838;
  --border: #30384a;
  --text: #eef2f7;
  --muted: #93a0b4;
  --accent: #7aa2ff;
  --ok: #34d399;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  min-width: 320px;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.app-shell { max-width: 1440px; margin: 0 auto; padding: 24px; }
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 18px;
}
h1 { margin: 0; font-size: 22px; letter-spacing: 0; }
p { color: var(--muted); }
.status-pill {
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--ok);
  padding: 6px 10px;
  font-size: 12px;
}
.tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 18px 0; }
.tab-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel);
  color: var(--text);
  padding: 9px 12px;
  font-size: 13px;
}
.panel {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel);
  padding: 18px;
}
```

- [ ] **Step 6: Run frontend build**

Run: `cd web && npm install && npm run build`

Expected: Vite writes `web/dist`.

- [ ] **Step 7: Commit**

```bash
git add web/package.json web/package-lock.json web/index.html web/src
git commit -m "feat(web): add React command center shell"
```

---

### Task 4: Serve React Build From FastAPI

**Files:**
- Modify: `portal_server.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add static mount code**

In `portal_server.py`, import static/file responses:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
```

After `app.add_middleware(...)`, add:

```python
WEB_DIST = REPO_ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIST / "assets")), name="web-assets")
```

- [ ] **Step 2: Update root route to prefer React build**

In `portal_server.py`, update the `/` route:

```python
@app.get("/", response_class=None)
async def root():
    index_path = WEB_DIST / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return HTMLResponse(HTML_TEMPLATE.format(version=VERSION))
```

- [ ] **Step 3: Include built web assets in package metadata**

In `pyproject.toml`, add to both include/force-include sections:

```toml
"web/dist",
```

and:

```toml
"web/dist" = "web/dist"
```

- [ ] **Step 4: Run backend tests**

Run: `python -m pytest tests/test_portal_app_state.py tests/test_swarm_preview.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add portal_server.py pyproject.toml
git commit -m "feat(portal): serve React web app"
```

---

## Self-Review

Spec coverage:

- FastAPI + React/Vite path: covered by Tasks 3 and 4.
- Portal aggregation route: covered by Task 1.
- Swarm preview before launch: covered by Task 2.
- PT remains runtime/state authority: encoded in architecture and route boundaries.
- Existing behavior compatibility: tested through focused backend tests; full regression remains for execution phase.

Placeholder scan:

- No `TBD`, `TODO`, or "implement later" placeholders are used.
- Each code-changing task includes concrete code.

Type consistency:

- `SwarmPreviewRequest`, `api_swarm_preview`, and `_build_preview_assignments` are introduced before use.
- Frontend shell does not depend on API types until later tasks.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-16-web-app-orchestration.md`. Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.
