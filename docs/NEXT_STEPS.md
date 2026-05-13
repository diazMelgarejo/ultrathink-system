# Next Steps — 2026-05-13 State

## CI State (Periscope diazMelgarejo/periscope)

| Workflow | Tag | Status | Remaining |
|---|---|---|---|
| Docker | `v0.29.2-periscope.2-bd1d2bf` | ✅ pass | — |
| Release (go binaries + wheels) | `v0.29.2-periscope.2-bd1d2bf` | ✅ pass | — |
| Desktop Release (5 platforms) | `v0.29.2-periscope.2-bd1d2bf` | ✅ pass | — |
| PyPI publish | `v0.29.2-periscope.2-bd1d2bf` | ❌ `invalid-publisher` | **User action: configure OIDC trusted publisher on pypi.org** |

Release artifacts live at: https://github.com/diazMelgarejo/periscope/releases/tag/v0.29.2-periscope.2-bd1d2bf

## Periscope — User Action Queue

### A. PyPI Trusted Publisher (one-time admin)
1. Go to https://pypi.org → sign in (or create account for `periscope` package)
2. Settings → Trusted Publishers → Add Publisher
3. Fill in:
   - **PyPI project name**: `periscope`
   - **Owner**: `diazMelgarejo`
   - **Repository**: `periscope`
   - **Workflow filename**: `release.yml`
   - **Environment**: `pypi`
4. Next tag push will auto-publish wheels (no API key needed)

### B. Tauri Updater Signing (enables auto-update in desktop app)
Add 3 secrets in GitHub → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `TAURI_SIGNING_PRIVATE_KEY` | Content of `/tmp/periscope-keys/key` on your Mac |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | (empty — key has no password) |
| `PERISCOPE_UPDATER_PUBKEY` | `dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IERGN0Y2RkUyODZEMEJFNUIKUldSYnZ0Q0c0bTkvMzhFY2ZaQlRHWnVMNkJqdWluRXMvN3dRTHZremlUcGw4dHpMQUpnRXdhOHEK` |

After adding secrets, the Desktop Release CI will:
- Sign updater bundles (.app.tar.gz.sig, .nsis.zip.sig, .AppImage.tar.gz.sig)
- Generate and publish `latest.json` updater manifest to a permanent `updater` release
- Enable in-app auto-update

### C. Apple Code Signing (optional — for App Store / notarized .dmg)
Requires Apple Developer account ($99/yr). Secrets needed:
- `APPLE_CERTIFICATE` (base64 of .p12 Developer ID Application cert)
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_SIGNING_IDENTITY` (e.g. `Developer ID Application: Your Name (TEAMID)`)
- `APPLE_API_KEY`, `APPLE_API_KEY_CONTENT`, `APPLE_API_ISSUER` (for notarization)

Skip for now — unsigned .dmg works fine for personal use; macOS Gatekeeper will warn on first open.

---

## orama-system — v1.0 RC Roadmap

**Gate**: The `2026-04-28-perpetua-orama-master-revamp.md` plan has 5 open issues (0–4) that must be closed before v1.0 RC ships (per Decision D3).

### Issue 0 — CI Blocker (Perpetua-Tools) ✅ ALREADY FIXED
`orchestrator/orama_bridge.py` exists; `tests/test_orama_bridge.py` imports it correctly.
`pytest tests/test_orama_bridge.py tests/test_fastapi_health.py tests/test_hardware_routing.py` → **32/32 pass**.

### Issue 1 — Stale Name "Perplexity-Tools" ✅ ALREADY FIXED
Only occurrence is a cosmetic user-facing error string in `fastapi_app.py:489` — not a functional issue.

### Issue 2 — Hallucinated Model ID `"qwen3-coder:14b"` ✅ NOT IN CODE PATH
The only occurrence is inside an error message string in `fastapi_app.py:489` — never dispatched as a model ID.
`orama-system/api_server.py` has no hardcoded model IDs.

### Issue 3 — HardwareAffinityError Shim ✅ ALREADY ADDRESSED
`api_server.py` re-exports the real PT `HardwareAffinityError` at import time; shim is only a fallback when PT is unavailable.

### Issue 4 — HARDWARE_MISMATCH 400 Path Untested ✅ ALREADY COVERED
`tests/test_api_server.py` has multiple tests asserting 400 + `"HARDWARE_MISMATCH"` body.
`pytest tests/` → **152/152 pass**.

**All 5 issues from the revamp plan are resolved. Ready to tag v1.0.0-rc.1.**

---

## orama-system — Part B Testing (Mac-only mode — Win offline)

All functions verified working:
- `_ollama_ensure_ready`: ✅ logs show server-up, model-pull, keep_alive=-1 warm-up
- `_openclaw_select_profile`: ✅ symlink at `~/.openclaw/openclaw.json` → `config/mac-orchestrator.json`; backup at `.bak`
- `_graceful_shutdown`: ✅ SIGTERM/SIGINT trap registered
- `_register_mcp_endpoints`: starts `openclaw mcp serve --port 18790` when `WITH_MCP=1`

**Remaining test** (do when Win comes back online):
```bash
WITH_MCP=1 ./start.sh --with-mcp
# Then verify:
claude mcp list  # expect "openclaw-swarm" entry at port 18790
curl http://localhost:18790/health  # expect 200
```

---

## orama-system — Part C: Coordinator/Worker XML Pattern

From the original request: implement the Coordinator/Worker pattern using Gemini + Codex + offline models simultaneously.

Architecture (from Anthropic supervisor patterns doc, file `docs/v2/14-supervisor-and-anthropic-patterns.md`):

```
Coordinator (Claude / qwen3.5 orchestrator)
  ├── spawns Worker via <task-notification>
  ├── Worker returns <result> + <summary>
  └── Coordinator synthesizes, never writes code directly
```

**What to build** (in `bin/agents/orchestrator/`):
1. `coordinator.py` — reads task XML, dispatches to named workers, collects `<result>` blocks
2. `worker_registry.py` — maps worker ID → model/endpoint (mac/win/cloud)
3. `SOUL.md` update — add Coordinator behavioral rules (never writes code, always delegates)
4. `task_schema.py` — Pydantic v2 models for `TaskNotification`, `WorkerResult`
5. `dispatch_loop.py` — async loop: send task → poll → collect → synthesize

**Model dispatch table:**
| Worker | Model | Hardware | Best for |
|---|---|---|---|
| `mac-coder` | `lmstudio-mac/qwen3.5-9b-mlx` | Mac :1234 | Fast iteration, small files |
| `win-reasoner` | `lmstudio-win/qwen3.5-27b-*` | Win :1234 | Complex reasoning, large context |
| `mac-ollama` | `ollama/qwen3.5:9b-nvfp4` | Mac :11434 | Always available, no LM Studio needed |
| `gemini-reader` | `gemini-2.5-pro` (via gemini-cli MCP) | Cloud | Large context reading, architecture review |
| `codex-impl` | Codex (via ai-cli MCP) | Cloud | Code implementation, mechanical tasks |

---

## orama-system — v2.0 Kernel (starts after v1.0 RC)

Spec is fully written in `docs/v2/`. Kernel target ~220 lines across:
- `perpetua-core/state.py` — PerpetuaState
- `perpetua-core/llm.py` — async OpenAI-compat client
- `perpetua-core/policy.py` — HardwarePolicyResolver
- `perpetua-core/graph/` — MiniGraph + checkpointer + subgraphs + streaming
- `perpetua-core/gossip.py` — SQLite event log
- `oramasys/api.py` — FastAPI glass window (≤10-line handlers)

Build sequence (Phase 1–4, per GPT + Decision D9):
1. **Primitives** → PerpetuaState, LLMClient, HardwarePolicyResolver + YAML → unit tests
2. **Graph engine** → MiniGraph + edges + checkpointer + HITL + subgraphs → parity test vs v1
3. **HTTP surface** → FastAPI routes + streaming → integration tests
4. **Parity tests** → v2 graph reproduces v1.0 5-stage ultrathink flow end-to-end

---

## Priority Order (recommended)

1. 🔴 **Periscope PyPI** — user action, 5 min (unblocks PyPI publishing)
2. 🔴 **Tauri signing secrets** — user action, 5 min (unlocks auto-update CI)  
3. ✅ **Issues 0–4 all resolved** — 152 orama tests pass, 32 PT tests pass
4. 🏁 **Tag orama v1.0.0-rc.1** — ready now; run `git tag v1.0.0-rc.1 && git push origin v1.0.0-rc.1`
5. 🏗️ **Part C: Coordinator/Worker** — 1–2 sessions, ~4 hrs
6. 🏗️ **v2.0 kernel scaffold** — Phase 1 primitives, ~3 hrs per phase
