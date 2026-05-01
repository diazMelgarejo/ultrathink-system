# Perpetua-Tools & orama-system — Master Revamp Plan (2026-Q2)

**Strategy:** Opportunistic Hardening — Minimalist, Cross-Repo Synchronized  
**Repos:** [`Perpetua-Tools`](https://github.com/diazMelgarejo/Perpetua-Tools) · [`orama-system`](https://github.com/diazMelgarejo/orama-system)  
**Timeline:** 6 weeks, no hard deadline — one batch of fix commits at a time

Read `/docs` in both and follow Agent Guidelines:

1. Read [AlphaClaw/docs](https://github.com/diazMelgarejo/AlphaClaw/tree/feature/MacOS-post-install/docs) FIRST, that applies to all OpenClaw and AlphaClaw implementations throughout this process unless updated in later documents below, when in doubt, consult OpenClaw 2026.4.26 documentation,
2. Read Perpetua-Tools/docs and Agent Guidelines NEXT and learn, that applies to PT repo;
3. Read orama-system/docs LAST and learn, orama implements and extends both documents above and adopts and extends their Agent Guidelines.
4. When conflicts arise and big decisions need to be taken, **ALWAYS *AskUserQuestion*** first!

---

## Python Version Policy

| Constraint | Version |
|---|---|
| **Required minimum** | Python ≥ 3.11 |
| **Preferred** | Python ≥ 3.12 |
| **Maximum tested (CI)** | Python 3.13 via GitHub Actions |

All new code must be compatible with 3.11+. Type hints and syntax should not exceed 3.13 features until that becomes the minimum.

## Node.js Versions Used

* Built on : v22.22.2
* Tested on: v24.14.1

---

## Governing Principles

1. **Lockstep commits.** Any change to a shared contract (model IDs, exceptions, hardware policy) must land in both repos in the same session. No half-merges.
2. **Adjacent cleanup.** When a file is opened to fix a bug, clean adjacent imports, docstrings, and comments — but do not refactor beyond the touched area.
3. **Frugal testing.** Add high-impact tests for failure paths only. Do not chase coverage metrics. Every new test must cover a real risk.
4. **No backward-compatibility burden.** There are no external users. Breaking changes are allowed if both repos are harmonized.
5. **Defer platform expansion.** Windows-only and Linux-only dedicated test setups are deferred until MCP is fully implemented.
6. **Docs follow code.** Update `LESSONS.md` and `AGENT_RESUME.md` only after code changes are confirmed working.

---

## Issue Inventory & Summary Table

| # | Type | Repo | File | Line(s) | Issue |
|---|---|---|---|---|---|
| 0 | 🚨 CI Blocker | Perpetua-Tools | `tests/test_orama_bridge.py` | 23 | `ModuleNotFoundError: No module named 'orchestrator.ultrathink_bridge'` — 3 tests fail at collection, CI is red |
| 1 | 🔤 Typo | Perpetua-Tools | `agent_launcher.py`, `orchestrator.py` | 6, 1, 104 | `"Perplexity-Tools"` → `"Perpetua-Tools"` (stale repo name) |
| 2 | 🐛 Bug | Both | `agent_launcher.py`, `api_server.py` | 93, 46 | `"qwen3-coder:14b"` is a hallucinated model ID hardcoded as default — causes silent runtime failure |
| 3 | 📝 Doc/Comment | orama-system | `api_server.py` | 202 | `HardwareAffinityError` shim redefines instead of re-exports PT class — `except` blocks miss real exceptions |
| 4 | 🧪 Test | orama-system | `tests/test_api_server.py` | — | Zero coverage for the `HARDWARE_MISMATCH` 400 path — primary hardware safety gate is untested |

---

## Phase 1 — Immediate Correction & Unblocking

**Target: Days 1–3.** These are correctness and safety issues. Nothing else should be merged before these are green.

---

### 0 — Fix the CI Blocker (Perpetua-Tools)

**File:** `tests/test_orama_bridge.py` · **Line:** 23

The build is currently broken. Three test files fail at collection with:

```
tests/test_orama_bridge.py:23: in <module>
    from orchestrator.ultrathink_bridge import (
E   ModuleNotFoundError: No module named 'orchestrator.ultrathink_bridge'
============================ short test summary info ===========================
ERROR tests/test_fastapi_health.py
ERROR tests/test_hardware_routing.py
ERROR tests/test_orama_bridge.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
```

**Fix:** Update the import path in `test_orama_bridge.py` to the current module location. Verify by running `pytest tests/` locally until all three files collect cleanly.

This is **gate zero**. No other task should proceed until CI is green.

---

### 1 — Typo: Stale Repo Name (Perpetua-Tools)

**File:** `agent_launcher.py` · **Line 6**  
**File:** `orchestrator.py` · **Lines 1, 104**

```python
# agent_launcher.py line 6 — current:
Hardware-aware agent launcher for the Perplexity-Tools orchestration stack.

# Fix:
Hardware-aware agent launcher for the Perpetua-Tools orchestration stack.
```

```python
# orchestrator.py line 1 — current:
"""orchestrator.py — Perplexity-Tools Orchestrator (port 8000)

# Fix:
"""orchestrator.py — Perpetua-Tools Orchestrator (port 8000)
```

```python
# orchestrator.py line 104 — current:
app = FastAPI(title="Perplexity-Tools Orchestrator", version=VERSION)

# Fix:
app = FastAPI(title="Perpetua-Tools Orchestrator", version=VERSION)
```

All three changes land in one commit. Run a repo-wide grep for `Perplexity-Tools` and fix any remaining occurrences in the same pass.

```bash
grep -rn "Perplexity-Tools" . --include="*.py" --include="*.md" --include="*.yml"
```

---

### 2 — Bug: Hallucinated Model ID as Default (Both Repos)

**File:** `Perpetua-Tools/agent_launcher.py` · **Line 93**  
**File:** `orama-system/api_server.py` · **Line 46**

`qwen3-coder:14b` does not exist in the actual Ollama or LM Studio inventory on either machine. If the env var is never set, any request that reaches this default will silently fail or produce a confusing "model not found" error instead of a clean hardware policy violation.

```python
# agent_launcher.py line 93 — current:
WINDOWS_CODER_MODEL = os.getenv("WINDOWS_CODER_MODEL", "qwen3-coder:14b")

# Fix:
WINDOWS_CODER_MODEL = os.getenv(
    "WINDOWS_CODER_MODEL",
    "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",  # verified Windows-only model
)
```

```python
# api_server.py line 46 — current:
CODE_MODEL = os.getenv("CODE_MODEL", "qwen3-coder:14b")

# Fix:
CODE_MODEL = os.getenv(
    "CODE_MODEL",
    "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",  # verified Windows-only model
)
```

**Add a startup assertion in both files** that fires before the first request is served:

```python
import logging

_POLICY = load_policy()  # existing call
_valid_models = set(_POLICY.get("windows_only", [])) | set(_POLICY.get("shared", []))
if WINDOWS_CODER_MODEL not in _valid_models:  # (use CODE_MODEL in api_server.py)
    logging.critical(
        "Configured model '%s' is not in hardware policy. "
        "Requests will fail. Check WINDOWS_CODER_MODEL env var.",
        WINDOWS_CODER_MODEL,
    )
```

This must be a lockstep commit — both files change together.

---

## Phase 2 — Exception & Contract Stability

**Target: Week 1–2.** Standardize cross-repo communication so the two repos share one source of truth for safety exceptions.

---

### 3 — Doc/Comment: HardwareAffinityError Shim (orama-system)

**File:** `orama-system/api_server.py` · **Line 202**

The shim comment says "Legacy module-level shim for backward compatibility" — but the class body is `pass` with no inheritance from PT's `HardwareAffinityError`. Any `except HardwareAffinityError` in a test that imports from `api_server` silently misses exceptions raised by PT's `check_affinity()`.

```python
# Line 202 — current (wrong):
class HardwareAffinityError(RuntimeError):
    pass

# Fix — re-export, not redefine:
try:
    from utils.hardware_policy import HardwareAffinityError  # type: ignore[import]
except ImportError:
    class HardwareAffinityError(RuntimeError):  # type: ignore[no-redef]
        """Fallback shim — PT import failed. Active only in Layer-3 degraded mode."""
        pass
```

Update the comment to be accurate: the shim is **only active when PT is unreachable** (Layer-3 degraded mode), not a permanent backward-compat alias.

---

### 4 — Test: HARDWARE_MISMATCH Path Coverage (orama-system)

**File:** `orama-system/tests/test_api_server.py`

The existing 7 tests cover happy paths only. The `HARDWARE_MISMATCH` 400 response — the primary gate protecting Mac hardware from being accidentally loaded with Windows-only models — has zero test coverage.

Add both tests below. They follow the exact pattern of `test_http_bridge_maps_optimize_for_to_reasoning_depth` already in the file. No new infrastructure needed.

```python
def test_hardware_mismatch_mac_provider_with_windows_model(monkeypatch):
    """lmstudio-mac + Windows-only 27B model → must return 400 HARDWARE_MISMATCH."""
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        # Should never be reached — affinity check must fire first
        return "should not reach here", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Write a sorting algorithm",
                "task_type": "coding",
                "model_hint": "lmstudio-mac/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "HARDWARE_MISMATCH"
    assert "NEVER_MAC" in body["detail"]


def test_hardware_mismatch_win_provider_with_mac_model(monkeypatch):
    """lmstudio-win + Mac-only MLX model → must return 400 HARDWARE_MISMATCH."""
    async def fake_call_with_fallback(prompt, model, max_tokens, temperature):
        return "should not reach here", "http://redacted"

    monkeypatch.setattr(api_server, "_call_with_fallback", fake_call_with_fallback)

    with TestClient(api_server.app, raise_server_exceptions=True) as client:
        response = client.post(
            "/ultrathink",
            json={
                "task_description": "Run MLX inference",
                "task_type": "coding",
                "model_hint": "lmstudio-win/Qwen3.5-9B-MLX-4bit",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "HARDWARE_MISMATCH"
    assert "NEVER_WIN" in body["detail"]
```

The `lmstudio-mac/` and `lmstudio-win/` prefixes are the provider-routing syntax already parsed in `run_ultrathink()`. No mocking of hardware detection needed.

---

## Phase 3 — Rolling Cleanup & Documentation

**Target: Weeks 3–6.** Opportunistic hardening. Only touch these areas when adjacent to a real fix.

---

### Model ID Registry

Move validated model IDs out of hardcoded defaults and into a shared configuration source:

- A YAML/JSON config file as the canonical structured source
- Environment variables remain in sync and available for runtime overrides and engine compatibility
- Both must be synchronized — no divergence between what the config says and what the env var supplies by default

The startup validation added in Phase 1 (Task 2) becomes the enforcement mechanism. This registry work is the formalization of that pattern.

---

### Documentation Sync

When a file is touched during Phases 1 or 2, update these in the same commit:

- `README.md` — reflect current hardware routing logic if the touched module affects routing
- `LESSONS.md` — record the model ID hallucination pattern and the `HardwareAffinityError` re-export fix as permanent lessons for future agent sessions
- `AGENT_RESUME.md` — update only if the architecture or agent responsibilities changed

Do not launch a standalone docs rewrite pass. Docs follow code changes, not the other way around.

---

### Style Alignment

Apply `ruff` or `black` formatting **only to modules touched during Phases 1 and 2.** Do not run a repo-wide format sweep.

For all new or modified code, follow this practical rule set:

- Type hints on all public functions
- Explicit imports (no wildcard)
- Docstrings on non-trivial modules and public classes
- Small focused functions — single responsibility
- Structured logging for all safety-critical fallback paths
- No silent fallbacks for hardware-affinity or model-resolution failures

---

## Deferred — Post-MCP

Do not attempt these in the 6-week window:

- Windows-only dedicated test setup
- Linux-only dedicated test setup
- Full style normalization across the whole codebase
- Major package restructuring or namespace redesign
- Central exception framework beyond what Task 3 provides
- Sweeping architectural repackaging

These belong in a separate plan for full MCP implementation at v1.2 or later.

---

## Success Criteria

The revamp succeeds when all four are true:

1. **CI is green.** The `ModuleNotFoundError` is resolved. All three failing test files collect and pass. CI badges are green across both repos.
2. **Zero silent model failures.** No request path reaches a hallucinated or invalid model ID. The startup assertion fires a `CRITICAL` log if misconfigured.
3. **Hardware safety is tested.** The `HARDWARE_MISMATCH` path returns 400 and is verified by CI on every PR. The `HardwareAffinityError` raised by PT is correctly caught in orama-system.
4. **Naming is clean.** No active code path, primary doc, or API title references `Perplexity-Tools`.

---

## Commit Sequence Reference

| Commit | Scope | Content |
|---|---|---|
| `fix: unblock ci — correct ultrathink_bridge import` | PT | Task 0 |
| `fix: rename Perplexity-Tools → Perpetua-Tools in docstrings and app title` | PT | Task 1 |
| `fix: replace hallucinated qwen3-coder:14b default + startup model assertion` | PT + orama (lockstep) | Task 2 |
| `fix: re-export HardwareAffinityError from PT instead of redefining` | orama | Task 3 |
| `test: add HARDWARE_MISMATCH 400 path coverage` | orama | Task 4 |
| `docs: sync LESSONS.md and README with hardware routing changes` | Both | Phase 3 |
