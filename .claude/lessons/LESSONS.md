# Lessons — Shared Knowledge Base

> **Canonical path**: `.claude/lessons/LESSONS.md`
> **Purpose**: GitHub-auditable persistent memory across all ECC, AutoResearcher, and Claude sessions.
>
> **Rules**:
>
> - Read this file at the start of every session
> - Append new learnings before ending a session
> - Keep entries dated and agent-tagged

## continuous-learning-v2

This repo uses [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).
Instincts: `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`
Import command: `/instinct-import .claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`

---

## Sessions Log

<!-- Append entries below. Format:
## YYYY-MM-DD — <agent: ECC | AutoResearcher | Claude> — <brief topic>
### What was learned
### Decisions made
### Open questions
-->

---

## 2026-04-06 — Claude — CI: ModuleNotFoundError for fastapi / hatchling backend missing

### What Went Wrong

Two cascading CI failures caused by a single refactor of the CI dependency install step:

**Failure 1 — `ModuleNotFoundError: No module named 'fastapi'`**

- The original install step was: `pip install . pytest hatchling build tomli`
- This was refactored to `pip install ".[test]" build` to consolidate deps via `[test]` extras
- BUT `[test]` extras had not yet been added to `pyproject.toml` at that point
- Result: fastapi, uvicorn, slowapi, httpx were all missing on the CI runner

**Failure 2 — `Backend 'hatchling.build' is not available`**

- When `[test]` extras were added on the next commit, `hatchling` was not included
- The old `pip install .` step had `hatchling` listed explicitly; the refactor silently dropped it
- `python -m build` needs `hatchling` pre-installed in the active env (not just in `build-system.requires`, which only applies to isolated builds)
- Result: build step failed immediately after test step passed

### Root Cause

**Refactoring a pip install line without first verifying the target extras group contains ALL previously explicit packages.**
The pattern: replacing `pip install pkg1 pkg2 pkg3` with `pip install ".[extras]"` carries an implicit assumption that `[extras]` lists everything `pkg1 pkg2 pkg3` provided. That assumption was not verified.

### Prevention Rules (encoded in `scripts/check_ci_deps.py` + `.pre-commit-config.yaml`)

1. **Never replace an explicit `pip install` with `.[extras]` without first auditing every removed package into the extras group.**
2. **`hatchling` MUST always be in `[project.optional-dependencies] test`** — it is required for `python -m build` to run outside of isolated mode, which is what `test-package-install.py` does with `--no-isolation`.
3. **`pyproject.toml` MUST have a `[project.optional-dependencies]` section with a `test` group** — verified by `scripts/check_ci_deps.py` on every commit touching `.py`, `.yaml`, or `.toml` files.
4. **CI workflow files MUST use `pip install ".[test]"` pattern** — never bare `pip install pytest ...` which bypasses package-declared deps.
5. **All 8 required modules must be importable at commit time**: `fastapi`, `httpx`, `uvicorn`, `pydantic`, `slowapi`, `pytest`, `hatchling`, `build`.

### What Was Added

- `scripts/check_ci_deps.py` — pre-commit guard that enforces all 5 rules above
- `.pre-commit-config.yaml` — `ci-deps-guard` hook runs on every Python/YAML/TOML change
- `pyproject.toml` — `[project.optional-dependencies] test` now includes `hatchling>=1.26.0` and `build>=1.2.0`

### Commit Trail

- `f078c8a` — introduced the gap (refactored install, dropped hatchling implicitly)
- `9653cfc` — added ci-deps-guard pre-commit hook
- `710fc47` — added hatchling+build to [test] extras (final fix)

---

## 2026-04-07 — Claude — Idempotent installs: subprocess permissions + model auto-discovery

### What Went Wrong

**1. `capture_output=True` hides all subprocess output**
- `openclaw_bootstrap.py` used `capture_output=True` on both `npm install -g openclaw@latest` and `openclaw onboard --install-daemon`
- This silenced all stdout/stderr, making the bootstrap appear frozen with no feedback
- Fix: remove `capture_output=True` entirely — let output stream through

**2. npm global install does not guarantee execute bits**
- `npm install -g` on some Node/macOS/nvm setups installs the binary without `+x` permissions
- `shutil.which("openclaw")` may still return a path (finds it in PATH by name), but `subprocess.run(["openclaw", ...])` raises `PermissionError: [Errno 13] Permission denied`
- This `PermissionError` is an `OSError`, NOT a `subprocess.CalledProcessError` — catching only `CalledProcessError` leaves it unhandled and propagates as a crash
- Fix: after npm install, explicitly check `stat().st_mode & S_IXUSR` and `chmod +x` if missing; also add a separate `except PermissionError` block that prints the exact fix command

**3. LM Studio model names must be discovered at runtime, not hardcoded**
- Hardcoded model names (e.g. `qwen3:8b-instruct`) cause `404` (Ollama) or `400` (LM Studio) on every inference call when that model isn't loaded
- LM Studio returns its currently-loaded model via `GET /v1/models` → `data[0].id`
- Ollama returns available models via `GET /api/tags` → `models[].name`
- Fix: add `_resolve_ollama_model()` and `_resolve_lmstudio_model()` that query the backend first and remap to the first available model if the preferred one is absent

**4. Hardware isolation: Windows GPU models cannot run on Mac**
- Windows LM Studio (RTX 3080) is at `192.168.254.103:1234` — calls must go there over the LAN
- Mac LM Studio is at `192.168.254.101:1234` — completely separate instance
- When Windows detection fails, coder falls back to `mac-degraded` (Mac endpoint) — win-researcher is then correctly skipped via `coder_backend != "mac-degraded"` guard

**5. AgentTracker `agents.json` collides with old `routing.json` format**
- Before the rename (`agents.json` → `routing.json` in agent_launcher), the tracker loaded flat routing dicts (`{"mac_ollama_ok": true, ...}`) instead of `AgentRecord` dicts
- `AgentRecord(**v)` raises `TypeError: argument after ** must be a mapping, not str` when `v` is a bool or string
- Fix: `_load()` must check `isinstance(v, dict)` before constructing `AgentRecord`; prune and rewrite the file on first load if stale entries are found

### Prevention Rules for All Idempotent Installs

1. **Never use `capture_output=True` in bootstrap scripts** — output should always stream to the user
2. **After any `npm install -g`, verify and fix execute bits** before running the binary:
   ```python
   import stat
   path = shutil.which("binary_name")
   if path and not (Path(path).stat().st_mode & stat.S_IXUSR):
       Path(path).chmod(Path(path).stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
   ```
3. **Catch `PermissionError` separately from `CalledProcessError`** in all subprocess blocks — they are different exception types
4. **Never hardcode model names** for LM Studio or Ollama — always query `/v1/models` or `/api/tags` and resolve at runtime; fall back to first available model
5. **Separate AgentTracker state file from routing state file** — never share the same JSON path between an AgentRecord registry and a flat routing dict
6. **All `_load()` methods for typed records must validate `isinstance(v, dict)`** before unpacking with `**v`

### Commits
- `3c9a4a8` (UTS) — fix(bootstrap): handle PermissionError + auto chmod +x after npm install
- `23bd01d` (UTS) — fix(bootstrap): remove capture_output=True
- `ffb1be0` (PT)  — fix(researchers): auto-discover loaded model via /v1/models + /api/tags
- `d9e4f50` (PT)  — fix(tracker): handle stale routing data in agents.json

---

## 2026-04-07 — Claude — Device identity + GPU crash recovery

### What was learned

**1. `127.0.0.1` and a LAN IP can point to the same physical machine**
- If `WINDOWS_IP` is mis-configured to the Mac's own LAN IP (e.g. `192.168.254.101`), the probe at `REMOTE_WINDOWS_URL` succeeds and the system treats one Mac as a distributed two-node cluster
- Fix: after probing, enumerate this machine's IPs via hostname resolution + UDP routing trick; zero out any "Windows" probe whose IP matches a local one

**2. One role per physical device**
- Running Mac Ollama + Mac LM Studio simultaneously on the same Mac GPU would cause two concurrent model loads — prioritise Ollama and ignore LM Studio when both are local
- Applies equally to any future n-device setup: each device gets exactly one researcher role

**3. Silent crash recovery burns GPU**
- Immediate retry after a 503/404/crash triggers repeated model load/unload; 30-second cooldown is the minimum safe buffer
- Progress bar with role label, crash classification, and per-second countdown makes recovery visible and distinguishable from a freeze

**4. Crash error classification**
- `HTTP 503` = model still loading (LM Studio startup)
- `HTTP 404` = model was unloaded (Ollama eviction or restart)
- `ConnectError/ConnectTimeout` = backend is offline
- Each class needs a distinct user message and consistent recovery behaviour

### Prevention Rules

1. Always call `_get_local_ips()` before trusting any "remote" endpoint URL
2. One role per physical device — zero out probes whose host IP matches local IPs
3. On same device: one inference backend — Ollama > LM Studio deterministically
4. Crash recovery ≥ 30 seconds — GPU needs this buffer between model cycles
5. Classify errors by status code before sleeping — 503 ≠ 404 ≠ ConnectError
6. Progress bar during recovery — `asyncio.sleep(N)` is invisible to the user

### Commits
- `8af62f5` (PT) — feat(routing): one-role-per-device guard + GPU crash recovery cooldown

---

## 2026-04-07 — Claude — Idempotent gateway discovery (commandeer-first bootstrap)

### What was learned

**Never start a new daemon if a compatible one is already running**
- The old bootstrap only checked `127.0.0.1:18789` (OpenClaw default) — if AlphaClaw or any other fork was running on a different port, it would start a second daemon, potentially conflicting with loaded agents
- The correct pattern: probe ALL known candidate ports FIRST; if any gateway responds to `/health` or `/v1/models`, commandeer it and skip the entire install/start flow
- AlphaClaw (chrysb/alphaclaw) and other OpenClaw-compatible gateways expose the same `/health` + `/v1/chat/completions` interface — they are indistinguishable at the protocol level and can be used transparently

**Commandeer = use existing + update config, never restart**
- When commandeering: write/refresh `openclaw.json` and agent workspaces (routing stays current), but DO NOT call `openclaw onboard --install-daemon` — this would restart the daemon and could evict loaded models
- Set `OPENCLAW_GATEWAY_URL` env var to the discovered URL so all downstream consumers (orchestrator, researchers) target the right port without hardcoding

**Candidate port list should be configurable**
- Hardcoding only the default port is fragile; users may run AlphaClaw on 11435, dev proxies on 8080, etc.
- `OPENCLAW_CANDIDATE_PORTS` defines the probe order; `OPENCLAW_EXTRA_PORTS` env var extends it at runtime
- `OPENCLAW_GATEWAY_PORT` itself should be env-overridable (not a hardcoded constant)

### Prevention Rules

1. **All bootstrap scripts must probe before install** — check if the target service is already running across ALL known ports before touching npm/brew/apt
2. **Commandeer-first, install-last** — if a compatible service exists anywhere on localhost, use it; do not start a duplicate
3. **Never stop/restart a running daemon during bootstrap** — `onboard --install-daemon` and similar "start" commands should only run when nothing is listening
4. **Always set a discoverable env var** (`*_URL`, `*_ENDPOINT`) pointing to the live gateway URL so downstream code doesn't need to repeat the discovery logic
5. **Protocol compatibility > implementation identity** — probe by interface (`/health`, `/v1/models`), not by process name; this works across forks and versions

### Commits
- `6bc40d0` (UTS) — feat(bootstrap): probe all candidate ports and commandeer any running gateway

---

## 2026-04-07 — Claude — Bulk sed safety: check before editing / look for missing files

### What Went Wrong

A batch `sed -i` to replace old `multi_agent\.` import-style path references with `bin.` matched more than intended:
- Pattern `s|multi_agent\.\([a-z]\)|bin.\1|g` was applied across all text files (READMEs, shell scripts, Python files)
- It matched filename **strings** inside file contents, e.g.:
  - `chk_f tests/test_multi_agent.py` → `chk_f tests/test_bin.py` (wrong — file does not exist)
  - `pytest tests/test_multi_agent.py` → `pytest tests/test_bin.py` (docs reference broken)
  - `test_multi_agent.py` docstring self-reference → `test_bin.py`
- The same issue had previously hit `single_agent\.` → `test_bin.skills.py` in README
- These substitutions introduced CI failures: `chk_f` could not find `test_bin.py`

Root cause: **the pattern was designed for Python import statements** (`from multi_agent.foo`) but was applied broadly — it also matched shell commands, docstrings, and doc prose referencing actual filenames.

### Prevention Rules

1. **`grep -rn` before any bulk `sed`** — preview every match, read each context line; abort if any match is a filename or path to an existing file
2. **Scope module-import patterns to `.py` files only** — `find . -name "*.py" -exec sed`; never apply import-rename regexes to `.md`, `.sh`, `.yaml`, or `.txt`
3. **Verify files exist before referencing them in commands** — after any substitution that changes a filename-like string, run `ls` or `find` to confirm the referenced path actually exists
4. **Keep filename strings and import module names disjoint in patterns** — if the old module path happens to appear in filenames (e.g. `test_multi_agent.py`), use a more precise anchor (`from multi_agent\.` with the `from` prefix, or word-boundary assertions)
5. **CI will catch broken `chk_f` / `pytest` references** — but catching it post-push is costly; catch it pre-commit with a `grep` on the changed lines

### Commits
- `0364098` (UTS) — fix(tests): restore test filenames broken by over-eager multi_agent sed

---

## 2026-04-09 — Claude — PT-first orchestrator migration

### What was learned

- PT works best when it is the only repo making orchestration decisions. The migration became cleaner once `orchestrator.py` and shared control-plane helpers became the single lifecycle authority for gateway reconciliation, Perplexity onboarding, staged readiness, and runtime payload generation.
- Setup-time onboarding prevents silent runtime degradation. Perplexity credentials, AlphaClaw or OpenClaw readiness, and AutoResearch preflight all needed to move earlier in the user flow.
- Role routing needs a concrete artifact, not just a narrative. The manager-local plus researcher-remote topology became testable only after PT generated explicit role-routing state and `openclaw_config`.
- Cross-repo handoff is safest when PT exports a resolved payload and UTS consumes it without reinterpretation.

### Decisions made

- Added a shared PT control plane that resolves routing, reconciles gateway state, runs staged bootstrap, and writes a runtime payload.
- Unified Perplexity client initialization around explicit credential status and validation semantics.
- Moved more readiness reporting into PT so UTS can delegate instead of repeating lifecycle checks.

### Open questions

- Whether the runtime payload should grow into a versioned public contract document once more external consumers depend on it.
- Whether setup-time UX should eventually persist richer migration diagnostics for support cases.

---
