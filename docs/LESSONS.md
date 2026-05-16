# Lessons — orama-system

> **Canonical path**: `docs/LESSONS.md`<br/>
> **Previous path**: `.claude/lessons/LESSONS.md` (now redirects here)<br/>
> **Purpose**: GitHub-auditable persistent memory across all ECC, AutoResearcher, and Claude sessions.<br/>
> **Cross-repo companion**: [Perpetua-Tools/docs/LESSONS.md](../../perplexity-api/Perpetua-Tools/docs/LESSONS.md) · [GitHub](https://github.com/diazMelgarejo/Perpetua-Tools/blob/main/docs/LESSONS.md)
> **Architecture authority**: [2026-05-14--UNIFIED-ABSORPTION-PLAN.md](2026-05-14--UNIFIED-ABSORPTION-PLAN.md)
> **Navigation hub**: [CLAUDE-instru.md](../../../CLAUDE-instru.md)
>
> **Rules**:
>
> - Read this file at the start of every session
> - Append new learnings at the bottom before ending a session
> - Keep entries dated and agent-tagged (`ECC | AutoResearcher | Claude`)
> - For organized, deep-dive explanations see the **[wiki →](wiki/README.md)**
> - For agent behavioral rules see **[SKILL.md →](../SKILL.md)**

---

## continuous-learning-v2

This repo uses [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).

- Instincts: `.claude/homunculus/instincts/inherited/orama-system-instincts.yaml`
- Import command: `/instinct-import .claude/homunculus/instincts/inherited/orama-system-instincts.yaml`

---

## Sessions Log

<!-- Append entries below. Format:
## YYYY-MM-DD — <agent: ECC | AutoResearcher | Claude> — <brief topic>
### What was learned
### Decisions made
### Open questions
-->

---

## 2026-05-16 — Codex — Claude CLI auth must run outside sandbox

### What was learned

- Symptom: `claude -p --permission-mode dontAsk --max-budget-usd 0.25 "Reply with exactly: claude-ready"` returned `Not logged in · Please run /login`.
- False lead: repeated `claude auth login --claudeai` inside the sandbox printed `Login successful`, but `claude auth status --text` stayed unauthenticated.
- Root cause: Claude's OAuth callback server and credential persistence can fail inside a sandbox. Debug output showed `Failed to start OAuth callback server: Failed to start server. Is port 0 in use?`.
- A second risk was an install split: PATH `claude` pointed to a native install while the npm-global binary was newer. Auth probes must use the same binary that orchestration will call.

### Decisions made

- Run `claude auth login --claudeai` outside the sandbox or with explicit escalation when fixing auth for automated Claude workers.
- Treat `Login successful` as insufficient until both `claude auth status --text` and a real `claude -p` probe pass.
- Compare `which claude`, `claude --version`, and any known full binary path before debugging orchestration failures.

### Runbook

```bash
which claude
claude --version
claude auth login --claudeai
claude auth status --text
claude -p --permission-mode dontAsk --max-budget-usd 0.25 "Reply with exactly: claude-ready"
```

If failure persists:

```bash
claude --debug --debug-file /tmp/claude-auth-debug.log auth login --claudeai
sed -n '1,120p' /tmp/claude-auth-debug.log
```

Do not trust sandboxed login loops when the debug log reports an OAuth callback server failure.

## 2026-05-16 — Codex — GitHub MCP invalid transport postmortem

### What was learned

- `invalid transport` in `~/.codex/config.toml` is a schema error before it is an auth error.
- The npm GitHub MCP server is a stdio server: use `command = "npx"`, GitHub server `args`, and
  `[mcp_servers.github.env]`.
- `bearer_token_env_var` belongs to HTTP MCP config, not this stdio GitHub setup.
- A set PAT is not proof of a working MCP config; `codex mcp list` must parse, classify, launch, and
  show the env mapping.
- The failure was a classification failure: Codex stayed in "auth missing" mode while Claude moved to
  "transport schema invalid" mode and validated each change.
- Nuance matters: GitHub's remote HTTP MCP endpoint validly uses `bearer_token_env_var`; the local
  npm stdio server does not.

### Decisions made

- Saved this as a Codex memory and repo skill guidance.
- Future agents must validate MCP fixes with `codex mcp list`, not visual inspection.
- Created reusable skills for Codex MCP debugging and agent failure postmortems.

### Open questions

- Codex should improve its own warning so GitHub stdio setup does not suggest an HTTP-only auth field.

→ [wiki/11-codex-github-mcp-config.md](wiki/11-codex-github-mcp-config.md)

## 2026-04-06 — Claude — CI: ModuleNotFoundError for fastapi / hatchling backend missing

### What Went Wrong

Two cascading CI failures caused by a single refactor of the CI dependency install step:

**Failure 1 — `ModuleNotFoundError: No module named 'fastapi'`**

- Refactored `pip install . pytest hatchling build tomli` → `pip install ".[test]" build`
- `[test]` extras had not yet been added to `pyproject.toml` → fastapi, uvicorn, slowapi, httpx all missing on CI runner

**Failure 2 — `Backend 'hatchling.build' is not available`**

- Adding `[test]` extras on next commit didn't include `hatchling`
- `python -m build` needs `hatchling` pre-installed in active env (not just in `build-system.requires`)

### Root Cause

Replacing `pip install pkg1 pkg2 pkg3` with `pip install ".[extras]"` without first verifying the target extras group contains ALL previously explicit packages.

### Prevention Rules

1. Never replace explicit `pip install` with `.[extras]` without auditing every removed package into the extras group
2. `hatchling` MUST always be in `[project.optional-dependencies] test`
3. `pyproject.toml` MUST have a `[project.optional-dependencies]` section with a `test` group
4. CI workflow files MUST use `pip install ".[test]"` pattern
5. All 8 required modules must be importable at commit time: `fastapi`, `httpx`, `uvicorn`, `pydantic`, `slowapi`, `pytest`, `hatchling`, `build`

### Commits

- `f078c8a` — introduced the gap (refactored install, dropped hatchling implicitly)
- `9653cfc` — added ci-deps-guard pre-commit hook
- `710fc47` — added hatchling+build to [test] extras (final fix)

→ [wiki/01-ci-deps.md](wiki/01-ci-deps.md)

---

## 2026-04-07 — Claude — Idempotent installs: subprocess permissions + model auto-discovery

### What was learned

- **`capture_output=True` silences bootstrap scripts** — never use in user-facing install flows
- **`npm install -g` does not guarantee execute bits** — binary exists, `shutil.which()` finds it, but `subprocess.run()` raises `PermissionError: [Errno 13]`
- **`PermissionError` is NOT a `CalledProcessError`** — must be caught separately or crashes entire bootstrap
- **Hardcoded model names break inference** — LM Studio returns `400`, Ollama returns `404` when model isn't loaded; always resolve via `/v1/models` or `/api/tags` at runtime
- **Windows GPU models cannot be called on Mac** — LAN isolation required; never cross-wire endpoints
- **AgentTracker state must not share path with routing state** — flat routing dicts cause `AgentRecord(**v)` `TypeError`

### Decisions made

- `_resolve_ollama_model()` and `_resolve_lmstudio_model()` added — query backend before registering agent
- `openclaw_bootstrap.py` auto-`chmod +x` after `npm install -g` if execute bit missing
- `AgentTracker._load()` skips non-dict entries and rewrites file clean

### Commits

- `3c9a4a8` (UTS) — fix(bootstrap): handle PermissionError + auto chmod +x after npm install
- `23bd01d` (UTS) — fix(bootstrap): remove capture_output=True

→ [wiki/02-idempotent-installs.md](wiki/02-idempotent-installs.md)

---

## 2026-04-07 — Claude — Device identity + GPU crash recovery

### What was learned

1. **`127.0.0.1` and a LAN IP can point to the same machine** — UDP routing trick reveals outbound LAN IP; compare against configured endpoints before assigning roles
2. **One role per physical device** — running Mac Ollama + Mac LM Studio simultaneously loads two models on same GPU; Ollama takes precedence
3. **Rapid model reload after crash burns GPU** — classify by HTTP status (503=loading, 404=unloaded, ConnectError=offline); enforce 30s cooldown minimum
4. **Terminal feedback during crash recovery is essential** — `asyncio.sleep(N)` is invisible; ASCII progress bar with role + countdown is required

### Prevention Rules

1. Always call `_get_local_ips()` before trusting any "remote" endpoint
2. One role per physical device — zero out probes whose host IP matches local IPs
3. On same device: Ollama > LM Studio deterministically
4. Crash recovery ≥ 30 seconds
5. Classify errors before sleeping — 503 ≠ 404 ≠ ConnectError
6. Show progress bar during recovery

### Commits

- `8af62f5` (PT) — feat(routing): one-role-per-device guard + GPU crash recovery cooldown

→ [wiki/03-device-identity.md](wiki/03-device-identity.md)

---

## 2026-04-07 — Claude — Idempotent gateway discovery (commandeer-first bootstrap)

### What was learned

- **Never start a new daemon if a compatible one is already running** — probe ALL known candidate ports first; if any gateway responds to `/health` or `/v1/models`, commandeer it
- **Commandeer = use existing + update config, never restart** — calling `openclaw onboard --install-daemon` on a running gateway evicts loaded models
- **Candidate port list should be configurable** — `OPENCLAW_CANDIDATE_PORTS` + `OPENCLAW_EXTRA_PORTS` env var

### Prevention Rules

1. All bootstrap scripts must probe before install
2. Commandeer-first, install-last
3. Never stop/restart a running daemon during bootstrap
4. Always set a discoverable env var (`*_URL`, `*_ENDPOINT`) pointing to the live gateway URL
5. Probe by interface (`/health`, `/v1/models`), not by process name

### Commits

- `6bc40d0` (UTS) — feat(bootstrap): probe all candidate ports and commandeer any running gateway

→ [wiki/04-gateway-discovery.md](wiki/04-gateway-discovery.md)

---

## 2026-04-07 — Claude — Bulk sed safety: check before editing / look for missing files

### What Went Wrong

A batch `sed -i` to replace `multi_agent\.` with `bin.` matched filename strings inside READMEs and shell scripts, converting `pytest tests/test_multi_agent.py` → `pytest tests/test_bin.py` (file doesn't exist). CI failed on broken `chk_f` references.

### Prevention Rules

1. `grep -rn` before any bulk `sed` — preview every match, read each context line; abort if any match is a filename
2. Scope module-import patterns to `.py` files only — never apply import-rename regexes to `.md`, `.sh`, `.yaml`
3. Verify files exist after substitution that changes a filename-like string
4. Keep filename strings and import module names disjoint in patterns
5. CI will catch broken references but catching it pre-commit is cheaper

### Commits

- `0364098` (UTS) — fix(tests): restore test filenames broken by over-eager multi_agent sed

→ [wiki/05-bulk-sed-safety.md](wiki/05-bulk-sed-safety.md)

---

## 2026-04-09 — Claude — PT-first orchestrator migration

### What was learned

- PT works best as the only repo making orchestration decisions — `orchestrator.py` and shared control-plane helpers became the single lifecycle authority
- Setup-time onboarding prevents silent runtime degradation — Perplexity credentials, AlphaClaw/OpenClaw readiness, and AutoResearch preflight all moved earlier
- Role routing needs a concrete artifact — manager-local plus researcher-remote topology became testable only after PT generated explicit role-routing state and `openclaw_config`
- Cross-repo handoff is safest when PT exports a resolved payload and UTS consumes it without reinterpretation

### Decisions made

- Added shared PT control plane: resolves routing, reconciles gateway state, runs staged bootstrap, writes runtime payload
- Unified Perplexity client initialization around explicit credential status and validation semantics
- Moved readiness reporting into PT so UTS can delegate instead of repeating lifecycle checks

### Open questions

- Whether runtime payload should grow into a versioned public contract document
- Whether setup-time UX should persist richer migration diagnostics for support cases

---

## 2026-04-12 — Claude — 48-hour multi-agent sprint: collaboration patterns + version registry

### Version Number Registry — All Canonical Locations

**Current version: `0.9.9.7`.** Do NOT bump without explicit user instruction.

| File | Field | Status |
|------|-------|--------|
| `pyproject.toml:7` | `version = "0.9.9.7"` | ✓ current |
| `bin/orama-system/SKILL.md:10` | `version: 0.9.9.7` | ✓ current |
| `bin/config/agent_registry.json:2` | `"version": "0.9.9.7"` | ✓ current |
| `portal_server.py:26` | `VERSION = "0.9.9.7"` | ✓ current |
| `bin/agents/*/agent.md:4` | `version: 0.9.9.7` | ✓ current (all 7 agents) |
| `CLAUDE.md:71` | `(v0.9.9.7)` | ✓ current |
| `docs/PERPLEXITY_BRIDGE.md:3` | `Version 0.9.9.7` | ✓ current |

### Multi-Agent Collaboration Protocol

1. **Read LESSONS.md first** — mandatory, in CLAUDE.md
2. **Scope claim** — append `[IN PROGRESS]` marker before touching files
3. **Additive changes** — prefer appending over rewriting (no conflict risk)
4. **Commit message as communication** — state which constants/APIs changed
5. **Never hardcode ephemeral runtime values** — `127.0.0.1` default, real IP in `.env`
6. **One canonical source per constant** — two files defining the same IP string will diverge
7. **Test isolation** — `autouse` fixture that restores module-level state after `importlib.reload()`

### Embedded Git Repo: `.ecc/`

`.ecc/` is a gitlink (submodule stub). Do NOT delete, gitignore, or `git rm` it.
Other cloners need `git submodule update --init .ecc` to get the contents.

### Common Mistakes to Avoid

- Creating feature branches without `origin/main` as base — causes orphan branch with no common ancestor; `git rebase origin/main` produces add/add conflicts on EVERY file
- Hardcoded LAN IPs in source code defaults — breaks CI on all other machines; real IPs live in `.env` only

→ [wiki/06-multi-agent-collab.md](wiki/06-multi-agent-collab.md)

---

## 2026-04-13 — Claude — Startup fix: IP detection, stdin deadlock, concurrent backend probing

### Learned

- **Abort trap: 6 root cause**: `_gather_alphaclaw_credentials()` spawned a daemon thread calling `input()`. After `t.join(30)` timed out, Python shutdown tried to flush/close the stdin `BufferedReader` → SIGABRT. Fix: (1) `sys.stdin.isatty()` guard, (2) `</dev/null` in start.sh, (3) `stdin=subprocess.DEVNULL` on gateway `Popen`
- **IP misconfiguration was silent**: `agent_launcher.py` read `MAC_LMS_HOST`/`WINDOWS_IP` but neither was exported by start.sh or in `.env` — fallback hard-coded defaults always used
- **`agent_launcher.py` never called `load_dotenv()`** — only saw shell-exported vars; added `load_dotenv(".env")` + `load_dotenv(".env.local", override=True)`
- **`asyncio.create_task()` fires immediately; `gather()` blocks** — fire all probes at t=0, await in two phases (local first, then LAN) for correct ordering without sequential delay
- **`_persist_detected_ips()`** — confirmed live endpoints written back to `.env` after each probe; config becomes self-correcting

### Decided

- Hard-coded defaults: `.110` Mac LM Studio, `.108` Windows
- `network_autoconfig.py` `preferred_ips` updated to `.110` / `.108`
- `LM_STUDIO_MAC_ENDPOINT` parsed in `agent_launcher.py` to derive `MAC_LMS_HOST`/`MAC_LMS_PORT`
- `.env.local` corrected: `WINDOWS_IP=192.168.254.108`, `WINDOWS_PORT=11434`

→ [wiki/07-startup-ip-detection.md](wiki/07-startup-ip-detection.md)

---

## 2026-04-13 — Claude — Portal update: visibility, user-input textbox, correct IPs

### What was learned

1. **`portal_server.py` never loaded `.env`** — default IPs always used even when `.env` had correct values; fixed by adding dotenv loading at module import
2. **Agents-as-services need a user-input gate** — autonomous loops with no stop condition make it impossible to steer agents without killing the process; 3-round confirmation pattern: agents confirm live, then wait for instructions

### Decisions made

- Portal now loads `.env`/`.env.local` at startup
- Added `POST /api/user-input` endpoint (proxies to PT `http://localhost:8000/user-input`)
- New HTML template sections: Routing State, Active Agents, input textbox + JS fetch

### Commits

- `691787a` (UTS) — fix(portal): dotenv load, correct IPs, routing card, agent state, user input textbox

---

## Wiki

All lessons above are expanded with root causes, exact fixes, and verification commands:

| # | Page | Topic |
| --- | --- | --- |
| 01 | [CI Dependencies](wiki/01-ci-deps.md) | pip extras, hatchling, pyproject.toml guard |
| 02 | [Idempotent Installs](wiki/02-idempotent-installs.md) | execute bits, capture_output, model discovery |
| 03 | [Device Identity](wiki/03-device-identity.md) | one-role-per-device, GPU crash recovery, cooldown |
| 04 | [Gateway Discovery](wiki/04-gateway-discovery.md) | commandeer-first bootstrap, candidate ports |
| 05 | [Bulk Sed Safety](wiki/05-bulk-sed-safety.md) | grep-first, scope to .py only |
| 06 | [Multi-Agent Collab](wiki/06-multi-agent-collab.md) | version registry, scope claims, orphan branches |
| 07 | [Startup IP Detection](wiki/07-startup-ip-detection.md) | stdin deadlock, load_dotenv, asyncio probing |
| 08 | [Git Hygiene and Branching](wiki/08-git-hygiene-and-branching.md) | clean-lineage salvage, identity checks, protected branch flow |

---

## 2026-04-20 — Claude — Gate 1: start.sh thinned; orama is now a pure PT delegator

### What was learned

**orama is a delegate, not a decision-maker.** The key lesson from Gate 1: any line in start.sh that reads routing.json, probes backends, or determines "distributed vs single vs offline" mode is a policy violation. That logic belongs in PT. orama reads the result; it never re-derives it.

**Thinning pattern for shell delegation:**

```bash
_PT_ENV_EXPORTS="$(
  "$PT_PYTHON" -m orchestrator.alphaclaw_manager --resolve --env-only \
    --mac-ip "${MAC_IP}" --win-ip "${WIN_IP}" \
    2>&1 | tee /dev/stderr | grep '^export '
)" && eval "$_PT_ENV_EXPORTS"
```

The `tee /dev/stderr` keeps progress messages visible while `grep '^export '` captures only the `eval`-able lines. This is cleaner than temp files.

**New file to know:** `orchestrator/alphaclaw_manager.py` (in PT) is the authoritative Python lifecycle manager. Start there when debugging gateway issues. It wraps `agent_launcher.py` (probe) and `alphaclaw_bootstrap.py` (lifecycle).

**FUSE git limitation persists:** git operations in the sandbox FUSE mount still fail with `index.lock` or `Resource deadlock avoided`. Always provide Mac terminal commands for commits.

### Decisions Made

- start.sh v0.9.9.8 is the canonical thinned version. Sections 2a and 2c are gone — absorbed into PT's `alphaclaw_manager.py`.
- start.sh now labels services as "orama" (not "ultrathink") everywhere.
- The security warning (AlphaClaw default password) is preserved — it reads from `.state/onboarding.json` written by PT's bootstrap.
- `PT_MODE`, `PT_DISTRIBUTED`, `PT_ALPHACLAW_PORT` env vars are now available in orama's shell environment after PT resolve.

### Open

- `openclaw_bootstrap.py` in orama still has gateway decision logic — Gate 2 work to scope it down to apply-config only.
- Autoresearcher launch (was start.sh §distributed check) needs to move to PT's `alphaclaw_manager.py` resolve payload as a flag — Gate 2.

→ [PT docs/MIGRATION.md §Gate 1](https://github.com/diazMelgarejo/Perpetua-Tools/blob/main/docs/MIGRATION.md)
→ [PT orchestrator/alphaclaw_manager.py](https://github.com/diazMelgarejo/Perpetua-Tools/blob/main/orchestrator/alphaclaw_manager.py)

---

## 2026-04-24 — Codex — Clean-lineage salvage guardrails

### What was learned

Directly replaying a useful tail is unsafe when commit metadata, tracked private
config, generated path files, and symlink assumptions are mixed into the same
range. The safer approach is to branch from the verified clean anchor, snapshot
both repos, and manual-port only reviewed intent.

### Decisions Made

- Salvage branch format is `yyyy-mm-dd-001-brief-summary`.
- Canonical commit identity is `cyre <Lawrence@cyre.me> or Codex <codex@openai.com>`.
- `.env`, `.env.local`, and `.paths` are ignored runtime files; examples are the only tracked contract.
- `.ecc` must not be both a gitlink expectation and a symlink in the working tree.
- `repo_hygiene.py` and `check_identity.sh` are the pre-commit guardrails for this recovery path.

→ [docs/recovery/2026-04-24-001-orama-history-recovery.md](recovery/2026-04-24-001-orama-history-recovery.md)
→ [docs/recovery/2026-04-24-002-commit-salvage-matrix.md](recovery/2026-04-24-002-commit-salvage-matrix.md)
→ [docs/recovery/2026-04-24-003-git-safety-guardrails.md](recovery/2026-04-24-003-git-safety-guardrails.md)

---

## 2026-04-24 — Claude — Salvage forensics + systematic rename + hygiene pipeline

### What was learned

1. **Forensics First, Action Last**: Gemini's corrupted commits involved not just metadata shifts but destructive configuration purges (stripping `.env`). Never rebase a corrupted tail blindly. Map the drift first.
2. **Identity Restoration via `.mailmap`**: Git's identity corruption (unauthorized email/name) is best fixed at the repo level with a canonical `.mailmap` file, ensuring all historical logs attribute correctly without rewriting every commit object.
3. **Historical Rename Strategy**: The migration from `ultrathink-system` to `orama-system` required a multi-stage approach:
    - `sed` batch for internal references (excluding historical docs and hygiene configs).
    - `git mv` for folders and individual filenames.
    - Automated hygiene check to verify no "active" legacy references remained.
4. **Idempotent Setup Bug**: A `TypeError` in `setup_macos.py` (incorrect `_skip` signature) proved that even "no-op" dry-runs must be tested. Idempotent guards must accept optional detail strings consistently.

### Decisions made

- `orama-system` is the authoritative name and directory.
- `scripts/review/repo_hygiene.py` is the primary guardrail for identity and naming consistency.
- [docs/wiki/08-git-hygiene-and-branching.md](wiki/08-git-hygiene-and-branching.md) tracks the active Git hygiene and branching guardrails.

### Prevention Rules

1. Always run `python3 scripts/review/repo_hygiene.py` before committing a major refactor.
2. Maintain `.mailmap` as the "Source of Truth" for author identity.
3. Use `yyyy-mm-dd-NNN-summary` branch naming for salvage work.
4. Verify `_skip` and `_log` signatures in setup scripts after any logging refactor.

### Commits

- `dc45482` — chore(rename): systematic migration to orama-system
- `f43a9b2` — fix(setup): fix _skip call signature in setup_macos.py

→ [docs/wiki/08-git-hygiene-and-branching.md](wiki/08-git-hygiene-and-branching.md)
→ [scripts/review/repo_hygiene.py](../scripts/review/repo_hygiene.py)

---

## 2026-04-24 — Codex — Xcode metadata hygiene + docs-only handoff discipline

### What was learned

1. **`.gitignore` does not protect `.git/` internals**: Finder or Xcode can leave `.DS_Store` under `.git/refs`, which breaks Git with `badRefName` even though `.DS_Store` is ignored for normal tracked files.
2. **Generated artifacts need two layers of defense**: Ignore patterns prevent new working-tree noise, while hygiene checks catch already-tracked macOS metadata, Xcode user state, Python caches, wheels, and build outputs.
3. **Docs-only commits need explicit staging**: When code hygiene work and documentation edits coexist, stage named docs files only. Do not let unrelated guardrail changes leak into a documentation commit.
4. **Future agents need link maps, not large context dumps**: `CONTRIBUTING.md` should point to canonical methodology, coordination, recovery, and verification markdowns so agents can load the smallest relevant context.

### Decisions made

- Treat `git fsck --no-reflogs --full --unreachable --no-progress` as the fast signal for malformed refs after macOS/Xcode metadata incidents.
- Check `.git/refs` directly with `find .git/refs -name '.DS_Store' -print` when Xcode Beta or Finder has touched the checkout.
- Keep contribution guidance relative-link-only so GitHub renders it and agents do not depend on sibling local checkouts or absolute machine paths.
- Add new operational learnings here before ending a session; link deeper guidance through [CONTRIBUTING.md](../CONTRIBUTING.md), [docs/wiki/README.md](wiki/README.md), and [tests/README.md](../tests/README.md).

### Prevention rules

1. Before committing from a macOS/Xcode-touched checkout, run `python3 scripts/review/repo_hygiene.py .` and `git fsck --no-reflogs --full --unreachable --no-progress`.
2. If `.git/refs/.DS_Store` appears, remove only that metadata file and rerun `git fsck`; do not reset or rewrite history for a local Finder artifact.
3. For docs-only commits, verify the staged set with `git diff --cached --name-only` and keep it limited to markdown files.

---

## 2026-04-24 — Codex — Markdown redirect and size guardrails

### What was learned

Markdown edits need their own pre-commit discipline. Absolute local links, missing canonical-path notes after moves, and oversized single-file docs make future agent handoffs brittle even when tests pass.

### Decisions made

- `scripts/review/repo_hygiene.py` blocks absolute filesystem links in tracked markdown.
- Changed markdown files now warn when a new file exceeds 200 lines or an existing file exceeds 500 lines.
- Agents must ask before crossing those limits and suggest moving detail into `references/`, `docs/wiki/`, or sub-skills.
- The root skill, packaged skill, Claude skill mirror, CIDF, and verification checklist all carry the same markdown edit rule.

### Prevention rules

1. Before committing markdown, run `python3 scripts/review/repo_hygiene.py .`.
2. Keep links relative and GitHub-renderable unless the target is an intentional external URL.
3. Preserve redirect or canonical-path breadcrumbs when moving markdown.

---

# 2026-04-26 — Hardware Model Affinity Incident

**Context:**
`orama-system/scripts/discover.py` was writing unfiltered LM Studio model lists
to `openclaw.json`. This could cause `lmstudio-mac` to advertise Windows-only
27B/26B models, creating a hardware damage risk on the M2 Pro, while
`lmstudio-win` could advertise Mac-only MLX / Apple Silicon models.

**Root cause:**
Discovery trusted endpoint responses without cross-referencing a hardware policy.

**Defense-in-depth solution:**

- L1: `discover.py` filters through `Perpetua-Tools/config/model_hardware_policy.yml`
  before writing discovery state, `openclaw.json`, or `.env.lmstudio`.
- L2: Perpetua-Tools `utils/hardware_policy.py`, `alphaclaw_manager.py`, and
  `agent_launcher.py` enforce affinity before routing/spawn decisions.
- L3: `api_server.py` returns HTTP 400 `HARDWARE_MISMATCH` at the API boundary.

**Canonical policy file:** `../perplexity-api/Perpetua-Tools/config/model_hardware_policy.yml`

**Known hallucinations removed:** `qwen3-coder-14b` and `gemma4:e4b` appeared in
AI-generated drafts of this plan. They are NOT verified model IDs in this system.
Do not re-add them.

**Status:** Implemented 2026-04-26.

**Follow-up — unified CLI/GUI management:**
Do not multiply human entry points. Hardware policy validation is exposed through
the existing orama CLI (`./start.sh --hardware-policy`, `./start.sh --status`)
and the existing Orama Portal (`http://localhost:8002`, Hardware Policy & Safe
Defaults section). Perpetua-Tools `scripts/hardware_policy_cli.py` is a helper
used by the existing CLI, tests, and agents — not a separate product surface.

---

## [2026-04-26] Session: Twin-System Recovery & Integration Hardening

### Context

Full-session work across Perpetua-Tools (Layer 2) and orama-system (Layer 3). AlphaClaw untouched.

### Key Facts Confirmed

| Fact | Value |
|------|-------|
| Win RTX 3080 LAN IP | `192.168.254.103:1234` (was wrong as .101/.107/.109) |
| Mac M2 Pro LAN IP | `192.168.254.105:1234` (always `localhost:1234` locally) |
| OpenClaw gateway | `localhost:18789`, loopback-only, bearer token auth |
| Tier 1 confirmed | Both nodes live after IP fix + `discover.py --force` |
| Gstack version | v1.12.2.0 at `~/.claude/skills/gstack` |
| Gbrain identity | `mcp__gbrain__*` tools (used by Gstack commands) |

### Patterns Learned

**IP drift is multi-file.** When LAN IPs change, update simultaneously:
`~/.openclaw/openclaw.json` → `config/devices.yml` → `.env.local` → run `discover.py --force`.
Use `grep -r "192.168.254" .` across all three repos as the audit command.

**GPT-5.5 model fallback rule.** Try `gpt-5.5` first. Downgrade to `gpt-5.4` ONLY on:
`"message":"The 'gpt-5.5' model is not supported when using Codex with a ChatGPT account."`
Do not preemptively downgrade.

**Gemini API type is critical.** Use `google-generative-ai` type for Gemini providers in OpenClaw — NOT `openai-completions`. The wrong type causes the gateway process to crash silently.

**Self-improve skill trigger = Option C.** Auto-suggest at session end; commit only when user approves. Never auto-commit without the A/B/C gate.

**Empty git dirs after rename.** `git mv` fails with "source directory is empty" when the dir has no tracked files. Use `rm -rf` for untracked artifact dirs — don't try to rename them.

**PR merge timing.** Cherry-pick post-branch commits onto main after PR merge. The last commit on a feature branch can be left behind if pushed after the PR was merged. Always verify with `git log --oneline origin/main..HEAD` after switching to main.

### Skills & Agents Created This Session

| Artifact | Location | Purpose |
|----------|----------|---------|
| `alphaclaw-session` v1.1.0 | PT `.claude/skills/alphaclaw-session/SKILL.md` | DO's/DON'Ts, self-healing, IP roster |
| `self-improve` v1.0.0 | PT + orama `.claude/skills/self-improve/SKILL.md` | Session crystallization (Option C) |
| `gemini-analyzer` agent | PT `.claude/agents/gemini-analyzer.md` | Gemini Reader role, large-context |
| `codex-coder` agent | PT `.claude/agents/codex-coder.md` | GPT-5.5 coder, Gbrain bridge, Gstack |

### Open Items (carry forward)

- Model ID case test (gateway was offline this session)
- Merge orama-system `2026-04-24-001-orama-salvage` → main
- Live Gbrain ↔ Codex test via Gstack
- Live Gemini-coder test via `mcp__gemini-cli__ask-gemini`

---

## 2026-04-26 — Claude — Part 2 session: Gemini audit + registry schema fix + commit hygiene

### What was learned

**1. agent_registry.json schema gap (agents[] had no `affinity` keys)**
The `agents` array (7 orama stage agents) was added before the hardware-policy work. None had
`"affinity"` keys. The `openclaw_agents` section and `autoresearch_agents` section both had
affinity info, but the stage agents were silently unguarded. Fixed in commit b2ed93b.

**2. api_server.py silent stub degradation**
When `PERPETUA_TOOLS_ROOT` doesn't exist or `utils.hardware_policy` can't be imported, the
except block fell back to no-op stubs with zero log output. Operators had no way to know enforcement
was disabled. Fixed: added `logger.warning()` with the PERPETUA_TOOLS_ROOT path in the except block.

**3. `ultrathink_bridge` import regression was the real blocker**
The prior session's attempt_completion was failing because `fastapi_app.py` still imported from
`orchestrator.ultrathink_bridge`, which was renamed to `orama_bridge` during the repo rename.
This caused ALL test collection to fail. Once fixed (from orchestrator.orama_bridge import ...),
11/11 tests passed immediately. The 4 "open architectural questions" were not actually blocking —
they were resolved in the implementation already.

**4. MCP server registration must use `-s user` scope**
`claude mcp add` without `-s user` scopes the server to the current working directory only.
Running the installer from a different directory (or a new shell) means the servers are invisible.
Always use: `claude mcp add -s user <name> -- <command>`.

**5. `device_affinity` vs `affinity` key inconsistency**
`autoresearch_agents` entries use `"device_affinity": "win-rtx3080"` while `agents` array entries
now use `"affinity": "win"`. These need to be normalized (Part 2, Phase 7). Any routing code
that reads `device_affinity` needs to be audited.

### Decisions made

- `executor-agent` gets `affinity: "win"` — it's the heavy compute worker (code_generator + performance_profiler)
- All other stage agents (orchestrator, context, architect, refiner, verifier, crystallizer) get `affinity: "mac"` — they are Claude Code subagent types, not LM Studio GPU workers
- `shared:` section in policy YAML stays empty until both machines are physically online and `discover.py --status` is run

### Open questions

- What models are genuinely cross-platform? (needs both machines online — Phase 5, Part 2)
- Should `device_affinity` in autoresearch_agents be normalized to `affinity`? (Phase 7, Part 2)

### Follow-up plan

`docs/tripartite-plan/2026-04-26-hardware-model-routing-004-PART2-PLAN.md`

---

# 2026-04-27 — Part 2 Complete: Disaster Recovery, Gemini Plan Review, AlphaClaw Fixes

## G3 + G2 closed (Part 2 Plan phases 7 + 8)

**G3 — device_affinity → affinity key rename:**

- `PT/config/routing.yml` autoresearch routes: renamed `device_affinity` → `affinity` (key only; value `win-rtx3080` preserved intentionally — future Windows hardware profiles will share the windows_only blocklist but have distinct whitelists, so specific device IDs are required)
- `orama/bin/config/agent_registry.json` autoresearch_agents: same rename
- Added regression guard `test_routing_affinity_keys_normalized` (PT) and `test_no_device_affinity_anywhere_in_registry` (orama)
- **Lesson: never normalize `win-rtx3080` to generic `win`** — device-specific affinity values are the extension point for multi-Windows-profile support

**G2 — PERPETUA_TOOLS_ROOT documented:**

- Added to `PT/.env.example` and `orama/.env.example` with cross-repo usage notes

**G1 — shared: section:**

- Commented out in `PT/config/model_hardware_policy.yml` with TODO block pointing to Part 2 Phase 5
- Added parametrized tests for both PyYAML and `_simple_policy_parse` paths (3 YAML variants: commented, absent, explicit-empty)
- Added `_POLICY_CACHE` autouse fixture to prevent cross-test contamination

## Disaster Recovery: HardwarePolicyResolver

**Problem:** PT is authoritative for hardware policy, but orama needs to run even if PT is temporarily unreachable. Previous design silently disabled enforcement on import failure.

**Solution:** 3-layer `HardwarePolicyResolver` in `api_server.py`:

- L1: sys.path import from PERPETUA_TOOLS_ROOT → PT-authoritative (preferred)
- L2: `config/hardware_policy_cache.yml` → vendored YAML snapshot, logs CRITICAL warning
- L3: hard fail if cache also missing — never silently skip enforcement

**PT final handoff audit trail:** Every response includes `metadata.policy_source` and `metadata.pt_authoritative`. `/health` endpoint exposes `hardware_policy.source`. This lets callers and ops know whether any routing decision was PT-authoritative or cache-degraded.

**FastAPI lifespan:** Moved policy initialization from module-level (breaks test imports + `--reload`) to `@asynccontextmanager lifespan`. Startup probe happens once; result is stable for the server lifetime.

**`hardware_policy_cache.yml`:** Created at `orama-system/config/hardware_policy_cache.yml` — refresh instructions in the file header.

## Gemini v3.1 Plan Review

**Accepted:**

- Step 2 (PERPETUA_TOOLS_ROOT env consolidation) — already done via .env.example
- Step 4 (hallucination purge) — already done in prior session; bad IDs live only in docs warning about them

**Rejected:**

- Step 1.1 (symlink orama/utils/hardware_policy.py → PT/utils/hardware_policy.py): fragile across machines, breaks on Windows (no Unix symlinks), breaks in Docker/CI, breaks when repos at different paths. sys.path approach is more portable.
- Step 1.2 (remove _simple_policy_parse fallback): this IS the disaster recovery fallback for PyYAML-absent environments. Removing it reduces resilience.

## AlphaClaw Plugin Config Fixes

**Problem 1 — duplicate plugin ID:** `usage-tracker` was being loaded twice — once as a bundled built-in AND again because startup code adds `lib/plugin/usage-tracker` to `plugins.load.paths`. Harmless but noisy.

**Problem 2 — restart unavailable:** `openclaw restart` requires `"restart"` in `plugins.allow`. It was absent.

**Fix:** Added to both `~/.alphaclaw/openclaw.json` and `alphaclaw-observability/config/openclaw.json`:

```json
"plugins": {
  "allow": ["usage-tracker", "restart", "memory-core"],
  "entries": { "usage-tracker": { "enabled": true }, "restart": { "enabled": true } },
  "load": { "paths": [] }
}
```

Setting `load.paths: []` prevents the startup code from adding the dev-repo path (which caused the duplicate).

**Architecture clarification:** AlphaClaw is a WRAPPER that orchestrates OpenClaw instances. OpenClaw runs standalone. AlphaClaw manages the gateway, plugins, and agent lifecycle AROUND OpenClaw sessions. This is the opposite of what the config file naming suggests — `openclaw.json` is AlphaClaw's config for managing OpenClaw.

## Tests Summary

- PT: 24/24 pass (16 original + 5 new: parametrized YAML parser + routing affinity key guard + ORAMA_ENDPOINT fix)
- orama: 23/23 pass (16 original + 7 new: agent_registry schema consistency tests)

## Open

- G1 (shared models): blocked — needs both machines online simultaneously
- G4 (live openclaw.json repair): blocked — needs both machines online
- Codex: `@openai/codex-darwin-arm64` native binary missing; use Gemini as second voice until fixed

---

## Session 2026-04-27b — Agent Automation, Portal Dashboard, Multi-Agent Dispatch

### What Was Built

**1. Codex PTY Automation (THE KEY PATTERN)**
Codex `--full-auto` requires a TTY. When spawned from any Python subprocess (Claude Code, portal API, CI), there is no TTY → "stdin is not a terminal" error.

**Fix: `pty.openpty()` pseudo-terminal wrapper**

```python
import pty, select, os

master_fd, slave_fd = pty.openpty()
proc = subprocess.Popen(
    ["codex", "--full-auto", task],
    stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
    close_fds=True,
)
os.close(slave_fd)  # parent doesn't need slave end
# read from master_fd with select() to collect all output
```

This makes Codex fully automatable — no human terminal ever required.

**Live in:** `orama-system/scripts/spawn_agents.py → _dispatch_codex()`

**2. Gemini CLI Node Version Fix**
Gemini CLI (installed under nvm v24) uses `??=` (ES2021). But `#!/usr/bin/env node` resolves to nvm v14 in Claude Code's shell. Fix: create `~/.local/bin/gemini` wrapper:

```bash
#!/usr/bin/env bash
exec /Users/lawrencecyremelgarejo/.nvm/versions/node/v24.14.1/bin/node \
     /Users/lawrencecyremelgarejo/.nvm/versions/node/v24.14.1/bin/gemini "$@"
```

`~/.local/bin/` comes before nvm in PATH → wrapper always wins.
**Live in:** `scripts/setup_codex.sh` (auto-creates wrapper on every `start.sh`)

**3. spawn_agents.py — Parallel Agent Dispatch**
File: `orama-system/scripts/spawn_agents.py` and `PT/scripts/spawn_agents.py` (shim)

Supports: `codex`, `gemini`, `lmstudio-mac`, `lmstudio-win`, `all`

- Codex + Gemini + LM Studio Mac run in parallel
- LM Studio Win serialized via `asyncio.Lock()` (one GPU model at a time)
- CLI: `python scripts/spawn_agents.py --task "..." --agent codex`
- API: `POST /api/spawn-agent` from the portal

**4. Portal Tools & APIs Panel**
All 18 tools/APIs from AlphaClaw + PT visible in `portal_server.py`:

- Groups: AI Providers, Search & Tools, Messaging Channels, GitHub, CLI, Gateways
- 3 states: READY (green) / NOT CONFIGURED (amber, inline configure) / KEY SET BUT FAILING (red, replace button)
- `POST /api/configure-tool` writes to `.env.local` safely (atomic + file lock + rate limit)
- No terminal needed to configure any API key

**5. Policy Cache Refresh Automation**
`scripts/refresh_policy_cache.py` syncs `config/hardware_policy_cache.yml` from PT on every `start.sh`. This keeps the L2 disaster recovery fallback always fresh.

### How to Dispatch Agents (from any context)

```bash
# From terminal
cd orama-system
python scripts/spawn_agents.py --status           # check availability
python scripts/spawn_agents.py --task "..." --agent codex
python scripts/spawn_agents.py --task "..." --agent gemini
python scripts/spawn_agents.py --task "..." --agent all   # parallel

# From portal (browser)
# Tools & APIs panel → Agent Dispatch panel → type task → click Send

# From Claude session (spawn sub-agent)
# Use Agent() tool with spawn_agents.py as the worker
```

### Gemini Review Pattern (tested and works)

```bash
# --yolo (alias: -y) auto-approves Gemini tool prompts.
# Without it, the subprocess hangs at the first sandbox/tool gate.
~/.local/bin/gemini --yolo -p "Review X for Y. Be concise."
```

Returns structured bullet-point feedback in ~3s.

### Key Architecture Invariants (updated)

- `spawn_agents.py` is the canonical multi-agent dispatcher for both orama and PT
- The portal `/api/spawn-agent` always loads spawn_agents.py via importlib + `sys.modules` registration
- Windows GPU: always `asyncio.Lock()` before LM Studio Win calls
- `setup_codex.sh` runs on every `start.sh` — codex + gemini are always fixed

### Open Items

- G1 (shared models): still blocked — needs both machines online
- G4 (live openclaw.json sync): still blocked
- Gemini CLI broken binary: wrapper fixes runtime but underlying package may need updating: `nvm use 24 && npm update -g @google/gemini-cli`
- Win LM Studio offline during this session — need both machines for full parallel dispatch

---

# 2026-04-27 — Dynamic LAN IP Detection & Self-Healing Architecture

**Context:**
Windows GPU machine (RTX 3080) had IP `.103` but system had stale `.101`/`.108` hardcoded in
`portal_server.py`, `spawn_agents.py`, `ip_detection_solution.py`, and PT's `lan_discovery.py`.
Auto-detection existed in `start.sh` (4-priority chain) but `portal_server.py`/`spawn_agents.py`
didn't use it when started standalone. The portal showed wrong IPs and couldn't reach Win LMS.

**Root causes (5):**

| # | File | Problem |
|---|------|---------|
| RC-1 | `portal_server.py:50-58` | Hardcoded `.101` fallback — ignored `openclaw.json` entirely |
| RC-2 | `scripts/spawn_agents.py:45` | Same — hardcoded `.101` |
| RC-3 | `~/.openclaw/state/discovery.json` | Win IP was empty (Win was offline during last scan), so start.sh Priority 2 always missed |
| RC-4 | `ip_detection_solution.py:27` | Stale `.101` hardcoded for Windows |
| RC-5 | PT `lan_discovery.py:318` | Bug: computed `{subnet}.100` but comment said `.103` (typo) |

**Fix — shared `utils/ip_resolver.py`:**

Created `orama-system/utils/ip_resolver.py` — single authoritative source for Win IP:

```
P1: AlphaClaw gateway (:18789) — live, if running means openclaw.json is current
P2: ~/.openclaw/openclaw.json  — patched by discover.py after every successful scan
P3: ~/.openclaw/state/discovery.json — last probe state (may lag if Win was offline)
P4: PT detect_active_tilting_ip() — derives {mac-subnet}.103, subnet-portable
P5: LM_STUDIO_WIN_ENDPOINTS env var — operator / start.sh override
P6: {outbound-interface-subnet}.103 — absolute last resort, subnet-portable
```

**Key patterns to remember:**

1. **Never hardcode LAN IPs in module-level constants.** Use `ip_resolver.get_win_lms_url()` which
   re-reads `openclaw.json` on every call. One file read per 10s portal poll is cheap.

2. **`discover.py --force` must run at every startup**, not just when state is stale.
   LAN is always dynamic. A 4-5s subnet scan at startup is acceptable — much better than stale IPs.
   Hook: `start.sh` now runs `timeout 15 python3 ~/.openclaw/scripts/discover.py --force` before
   the IP detection block.

3. **Gossip write-back:** when portal's live probe hits Win LMS successfully, it calls
   `write_win_ip_to_openclaw_json(probed_ip)` to update `openclaw.json`. This means any
   process that reads `openclaw.json` next will have the correct IP, even if `discover.py`
   didn't run yet.

4. **Subnet-portable `.103` rule:** Windows GPU is always `.103` on whatever subnet the Mac is on.
   This works on legacy `192.168.1.x` AND current `192.168.254.x` without any config change.
   PT's `detect_active_tilting_ip()` had a bug (`.100` instead of `.103`) — fixed.

5. **`ip_resolver.py` test:** `python3 utils/ip_resolver.py` — should print Win IP, LMS URL,
   Ollama URL. If it prints `.103` you're reading from `openclaw.json` (P2).

6. **Files that still have static Win IP references (archive, not code paths):**
   - `AGENT_RESUME.md` — informational only
   - Comments in various files marking old IPs (`.108`, `.101`) as archive

**Files changed:**

- `utils/ip_resolver.py` — NEW shared resolver (P1-P6 chain)
- `utils/__init__.py` — NEW package init
- `portal_server.py` — uses ip_resolver; dynamic re-resolve in `api_status()`; gossip write-back
- `scripts/spawn_agents.py` — uses ip_resolver fallback
- `ip_detection_solution.py` — stale `.101` → `.103`
- `start.sh` — `discover.py --force` at startup; subnet.103 as last-resort
- `scripts/sync-companion-instincts.sh` — Perplexity-Tools → Perpetua-Tools (all refs)
- PT `orchestrator/lan_discovery.py` — bug fix `.100` → `.103`

**Sync reminder:**
Both repos (orama-system and Perpetua-Tools) must be pushed after these changes.

---

## 2026-04-29 — Win IP Migrated to .105; Docs Cleanup

**Context:** Session resumed after credits ran out 2 days earlier. Win GPU IP changed again
from `.103` → `.105` (committed in PT `0bac6ea chore(config): update win-rtx3080 lan_ip`).

**Key finding:** The `ip_resolver.py` 6-priority chain handled this automatically — no code
change needed. `openclaw.json` (P2) already shows `http://192.168.254.105:1234/v1`. The
resolver read this at P2 and returned `.105` correctly without manual intervention.
This confirms the self-healing architecture works as designed.

**What the `.103` fallback constant means:** The hardcoded `.103` fallback in `ip_resolver.py`
is priority 6 (last resort) and is a best-guess constant. It only fires if ALL of:

- AlphaClaw is down (P1 fails)
- `openclaw.json` is missing or malformed (P2 fails)
- `discovery.json` has no reachable entry (P3 fails)
- PT `detect_active_tilting_ip()` is unavailable (P4 fails)
- No env vars set (P5 fails)
- Subnet derivation via socket fails (also P6)
In practice the real IP (`openclaw.json` P2) always wins. The `.103` constant is a
subnet-portable guess (Windows is always 3rd host on the /24), not the actual IP.

**Docs fixed this session:**

- `PT/docs/MIGRATION.md` Gate 2: removed hardcoded `192.168.254.101:1234`, replaced with
  dynamic note: "Win GPU LAN IP — dynamic, read from `~/.openclaw/openclaw.json`, currently `.105:1234`"
- `PT/docs/adr/ADR-001-*`: formatting cleanup
- `PT/docs/system-design-three-repo-architecture.md`: formatting pass

**Pending (blocked on both machines online):**

- G1 shared models list — needs Win + Mac simultaneously
- G4 live openclaw.json sync across repos
- Unified `/agent/dispatch` L2 API in PT

**Repos synced:** PT pushed `c6b8cdf`, orama-system clean (all changes from previous session already committed).

---

## 2026-04-29 — G1/G3/G4 Closed; LM Studio Remote-as-Local Proxy Behavior Discovered

**Trigger:** Both machines came online simultaneously — first time since policy was written.

### Key Discovery: LM Studio proxies remote LAN endpoints as "local" models

**What LM Studio does:** When you add a remote server (Win LMS at 192.168.254.105:1234) as
a provider in Mac's LM Studio, ALL models on that remote server appear in Mac's own
`/v1/models` response as if they were locally loaded. The reverse is also true.

**Why this matters:**

- The original policy assumed you could tell a model's physical home by which machine's
  `/v1/models` endpoint it appeared in. **This assumption is WRONG.**
- `qwen3.5-27b-...` appears in Mac's `/v1/models` — but it physically runs on Win RTX 3080.
- `qwen3.5-9b-mlx` appears in Win's `/v1/models` — but it physically runs on Mac Apple Silicon.
- Both machines return all 5 models, yet each model has a true physical home.

**Correct mental model:**

```
Mac /v1/models  →  [mac-native models] + [win models proxied as local]
Win /v1/models  →  [win-native models] + [mac models proxied as local]
```

**Routing rule that actually works:**

- Do NOT use model presence in `/v1/models` to determine which machine to route to.
- Use the **provider name** (`lmstudio-mac` vs `lmstudio-win`) as the routing key.
- The policy YAML `mac_only` / `windows_only` enforces provider-level routing, not detection.

**Policy fix applied:**

- `mac_only: []`, `windows_only: []` — cleared; LMS proxy makes per-machine exclusion unenforceable at the API level
- `shared:` — all 5 confirmed models added (accessible from either provider endpoint)
- openclaw.json repaired: both `lmstudio-mac` and `lmstudio-win` now show 5 models each

**discover.py result (2026-04-29, both machines online):**

```
mac: ✅ localhost:1234     — 5 models
win: ✅ 192.168.254.105:1234 — 5 models
```

### Gaps Closed This Session

| Gap | Status |
|-----|--------|
| G1 shared models populated | ✅ Closed — all 5 models confirmed shared |
| G3 device_affinity → affinity key rename | ✅ Closed — 7/7 schema tests pass |
| G4 live openclaw.json repaired | ✅ Closed — both machines show 5 models, no violations |
| G2 PERPETUA_TOOLS_ROOT in .env.example | ✅ Already existed |

### Model physical homes (for performance routing, not strict enforcement)

| Model | Physical home | Notes |
|-------|--------------|-------|
| `qwen3.5-9b-mlx` | Mac (Apple Silicon) | MLX quantization — native on Mac |
| `qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2` | Win (RTX 3080) | Large GGUF — GPU preferred |
| `gemma-4-26b-a4b-it` | Win (RTX 3080) | Large model — GPU preferred |
| `gemma-4-e4b-it` | Mac or Win (small) | Small enough for either |
| `text-embedding-nomic-embed-text-v1.5` | Mac or Win | Embedding model, low cost |

**Win IP confirmed stable at .105 during this session.**

---

## 2026-04-29 — Claude — Cross-repo sync gist (from PT docs/LESSONS.md)

*(PT-owned lessons relevant to orama. Full text in [Perpetua-Tools `main` → `docs/LESSONS.md`](https://github.com/diazMelgarejo/Perpetua-Tools/blob/main/docs/LESSONS.md).)*

### Hardware × Agent Matrix Test — All 6 OpenClaw Agents (confirmed 2026-04-27)

- **Model IDs are case-sensitive** in LM Studio. Use all-lowercase: `qwen3.5-9b-mlx`, `qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2`. No `-4bit` suffix on Mac.
- **openclaw CLI requires Node.js ≥ v22**. Default v14 fails instantly. Use full path: `/Users/lawrencecyremelgarejo/.nvm/versions/node/v24.14.1/bin/openclaw`
- **All 6 agents pass**: win-researcher/coder/autoresearcher (Win 27B, 107–130s), main/mac-researcher/orchestrator (Mac 9B, 105–308s via Gemini fallback).
- **Thinking models return empty `text`** — reply is in `reasoning_content`. Always check both fields.
- **commandTimeout must be ≥ 300 000 ms** for reasoning model turns.

### thinkingDefault fix (automated, 2026-04-27)

- `thinkingLevel`/`modelParameters` fields are REJECTED by OpenClaw schema. Correct field: `thinkingDefault: "off"`.
- `setup_macos.py` step 3b writes this and strips stale keys on every `start.sh`. No manual LM Studio toggle needed.
- Win 27B: leave thinking as-is; it always returns `reasoning_content`.

### Known working versions (2026-04-27)

- AlphaClaw: **0.9.3–0.9.11** all confirmed working.
- OpenClaw: all versions working.
- `KNOWN_ALPHACLAW_VERSION` in setup_macos.py = `"0.9.3"` (minimum baseline).

### Git status hang — node_modules was tracked (2026-04-29)

- `packages/alphaclaw-mcp/node_modules/` (3818 files + 6 symlinks) was committed accidentally in PT.
- `git status` hung indefinitely (lstat of 3818 files + APFS symlink chains).
- Fix: add `node_modules/` to `.gitignore`, then `git rm -r --cached packages/*/node_modules`.
- **Universal rule**: never track `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`.

### AutoResearcher migration: karpathy → uditgoenka (2026-04-11)

- `AUTORESEARCH_REMOTE` is now an env var (default: `uditgoenka/autoresearch`).
- Plugin install is primary mode: `claude plugin marketplace add uditgoenka/autoresearch`.
- **Valid Windows model name**: `Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2`. `Qwen3.5-27B-Instruct` DOES NOT EXIST — never use it.
- `uv sync --dev` replaces bare `pip install` in bootstrap paths.

### Module rename: ultrathink → orama (2026-04-29)

**Problem**: Phase B renamed files but left internal references stale, causing 16 test failures:

1. `orama_bridge.py` still imported `from orchestrator.ultrathink_mcp_client import` (broken after file rename)
2. Tests imported from `orchestrator.ultrathink_bridge` / `orchestrator.ultrathink_mcp_client` (old paths)
3. Test assertions checked `ULTRATHINK_ENDPOINT` / `ultrathink_available` (routing.yml now uses `ORAMA_ENDPOINT` / `orama_available`)
4. Hardware policy tests relied on live `model_hardware_policy.yml` which was correctly emptied (LM Studio proxy discovery)

**Fixes**:

- `orama_bridge.py`: fix import + logger name to use `orchestrator.orama_mcp_client` / `"orchestrator.orama_bridge"`
- Tests: replace module paths and env var names to match new routing.yml contract
- Hardware policy tests: pass explicit `policy=` dicts — self-contained, not coupled to live policy file
- Add `.claude/hooks/pre-commit` to catch 5 categories of naming drift at commit time

**Rule**: After any file rename, grep all test files for the old module path immediately. File renames break test `patch()` strings even when the rename is intentional and correct.

**Pre-commit guard**: `.claude/hooks/pre-commit` in Perpetua-Tools blocks commits with stale:
`orchestrator.ultrathink_bridge`, `orchestrator.ultrathink_mcp_client`, `ULTRATHINK_ENDPOINT`, `ultrathink_available`, `Perplexity-Tools` in ecc-tools.json.

### Version bump atomicity: update ALL surfaces at once (2026-04-29)

- SKILL.md says "When bumping version, update ALL of these atomically" — 5 surfaces
- `pyproject.toml`, `bin/orama-system/SKILL.md`, `bin/config/agent_registry.json`, `docs/PERPLEXITY_BRIDGE.md`, `docs/SYNC_ANALYSIS.md`
- Missing any one causes `test_version_docs.py` failures
- Template: `grep -rn "0.9.9.X" . --include="*.toml" --include="*.md" --include="*.json" | grep -v ".git"` before each bump

### Always use .venv/bin/python3 -m pytest for orama tests (2026-04-29)

- System Python 3.13 lacks httpx → `test_api_server.py` fails with RuntimeError on import
- orama `.venv` uses Python 3.12 with all required packages (fastapi, httpx, starlette)
- Command: `cd orama-system && .venv/bin/python3 -m pytest tests/ -q`

### .DS_Store in .git/refs causes repo hygiene check failure (2026-04-29)

- macOS Finder creates `.DS_Store` inside `.git/refs/` — `repo_hygiene.py` hard-fails on this
- Fix: `rm -f .git/refs/.DS_Store` — idempotent, safe
- Add to `.gitignore_global` or monthly cleanup script

### qwen3.5-9b-mlx is a thinking model — requires 500+ max_tokens (2026-05-01)

- `qwen3.5-9b-mlx` confirmed running at `localhost:1234` (LM Studio Mac)
- It is a **thinking model**: response contains `reasoning_content` (chain-of-thought) + `content` (actual answer)
- `content` is empty (`""`) if `max_tokens < ~200`. Safe floor: 500 tokens
- When a real LM Studio HTTP client replaces `_call_with_fallback`, extract `choices[0].message.content`, NOT `reasoning_content`
- Model is already correctly listed as `mac_only` in `config/hardware_policy_cache.yml`
- Test: `curl http://localhost:1234/v1/chat/completions -d '{"model":"qwen3.5-9b-mlx","messages":[{"role":"user","content":"Reply: OK"}],"max_tokens":500}'` → `content: "\n\nOK"` (209 reasoning tokens + 4 content tokens)

## 2026-05-02 — Claude — v2 packages scaffolded + instinct sync

### v2 Phase 1–3 complete: perpetua-core + oramasys + agate (2026-05-02)

Three Python packages built and pushed to GitHub under `oramasys` org. All tests green:

- `perpetua-core` 32/32 tests — `PerpetuaState`, `LLMClient`, `HardwarePolicyResolver`, `MiniGraph` (~70 lines), `GossipBus`, 6 graph plugins (checkpointer, interrupts, streaming, structured_output, subgraphs, tool)
- `oramasys` 4/4 tests — FastAPI glass-window `/run` + `/health`, hardware-routed 3-node graph
- `agate` — JSON Schema + examples for `model_hardware_policy.yml`

Local paths: `/Users/lawrencecyremelgarejo/Documents/oramasys/{perpetua-core,oramasys,agate}`
GitHub: `github.com/oramasys/{perpetua-core,oramasys,agate}`

**Phase 4 (parity tests) is next.** `dispatch_node` is still an echo stub — needs real `LLMClient` wiring.

Missing from spec (still TODO): `message.py`, `graph/nodes.py`, `graph/edges.py`, `config/model_hardware_policy.example.yml`, `GossipBus` integration in graph.

### Python runtime split on this machine (2026-05-02)

Two Python runtimes coexist:

- **Python 3.13**: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` — has oramasys packages installed
- **Python 3.12**: `/Users/lawrencecyremelgarejo/miniconda3/bin/python` — does NOT have v2 packages

Use `python3` (or full path `pytest`) for v2 tests. Running `python -m pytest` from miniconda shell fails with `ModuleNotFoundError: No module named 'perpetua_core'`.

### instinct-import CLI not installed — copy YAML workaround (2026-05-02)

`continuous-learning-v2` script (`~/.claude/skills/continuous-learning-v2/scripts/instinct-cli.py`) does not exist on disk — plugin is listed but not installed. Running `/instinct-import` fails silently.

**Workaround**: copy YAML files directly into `.claude/homunculus/instincts/inherited/` so future installs pick them up. Done for:

- `Perpetua-Tools-instincts.yaml` → `orama-system/.claude/homunculus/instincts/inherited/`
- `everything-claude-code-instincts.yaml` → `orama-system/.claude/homunculus/instincts/inherited/`

Key instincts to apply manually until script is available: snake_case filenames, relative imports, `@field_validator` not `@validator`, scoped conventional commits (`feat(x):`), tests in `tests/` directory.

### gitStatus in session context is a snapshot — always re-verify (2026-05-02)

The `gitStatus` block injected at session start is captured once at launch. By the time a new session starts, repos may have been committed and pushed. Always run `git status` before assuming there is work to do. Both orama-system and Perpetua-Tools appeared dirty in the snapshot but were fully clean when re-checked.

## 2026-05-02 — Document Integrity & Archiving Policy

- **Symptom**: Critical legacy documentation (AGENT_RESUME.md) was overwritten by an automated summary, losing v1 context.
- **Cause**: AI tendency to replace files rather than merge or archive (destructive behavior).
- **Rule**: NEVER delete or overwrite historical context. Always archive legacy documentation to /docs/archive/ or wiki entries.
- **Merge Strategy**: We are additive. All new summaries must be appended to the current state or moved to dedicated files while preserving the parent document's soul.
- **Reference**: Legacy AGENT_RESUME.md recovered and archived at docs/archive/AGENT_RESUME_v1_legacy.md.

## 2026-05-02 — Roadmap Granularity & Documentation Ergonomics

- **Symptom**: Premature "DONE" markers in v2 build order led to confusion about active implementation vs. planned hardening.
- **Cause**: AI tendency to mark design completion as task completion.
- **Solution**: Split roadmap into explicit **PLANNING** and **Implementation** phases. Architecture is "launched" (a living process), not merely "concluded."
- **Rule**: Documentation MUST link to both Archived (v1) and Active (v2) repository organizations to maintain cross-generational visibility.
- **Formatting**: Use `ascii` tags for non-executable code blocks and blockquotes for high-level summaries to improve UX for the next agent.

## 2026-05-04 — Codex — Priority execution (P1–P6), checklist and fail-closed hardening

### What was learned

- Large multi-priority migrations are easy to report as complete while still missing execution-level proof unless a strict post-block checklist is run.
- Hardware-bound requests (`lmstudio-*`, `ollama-*`) must fail closed when policy authority is unavailable; warnings are not sufficient.
- Verification command drift (doc command vs repo script reality) causes false confidence and noisy handoffs.

### Decisions made

- Added a consolidated checklist discipline after each priority block with pass/warn/fail reporting.
- Added in-repo helper `scripts/hardware_policy_cli.py --check-openclaw` to make the documented check executable.
- Promoted this incident to the wiki for durable cross-session visibility.

### Open follow-ups

- Historical docs still contain many `Perplexity-Tools` references; active-path docs are cleaned first, historical artifacts are tracked as non-blocking warnings.

→ [wiki/09-policy-fail-closed-and-checklist.md](wiki/09-policy-fail-closed-and-checklist.md)

---

## 2026-05-06 — Claude — Cherry-pick conflict resolution silently truncates files

**Agent**: Claude (Sonnet 4.6)
**Branch**: check-recovery-gemini
**Severity**: High — data loss risk on every multi-commit cherry-pick

### Problem

After cherry-picking 4 recovery commits (16eacf9, 9e70566, 4de7b09, 9876706)
onto a branch based on main, conflict resolution incorrectly took the *recovery
branch's older/shorter* file versions instead of main's richer ones — for 5 files
across two separate incidents:

| File | main lines | branch after cherry-pick | Lost |
|------|-----------|--------------------------|------|
| `scripts/review/repo_hygiene.py` | 363 | 204 | 159 lines of checks |
| `tests/test_repo_hygiene.py` | 147 | 34 | 113 lines of tests |
| `scripts/git/check_identity.sh` | 32 | 27 (elif reimpl.) | loop extensibility |
| `docs/wiki/08-git-hygiene-and-branching.md` | 122 | 122 (wrong content) | Codex identity text |
| `CLAUDE.md` | 217 | 225 (duplicate block) | duplicate cyre-only block injected |

The first two were silent — `pytest` still ran (just against the 34-line stub),
reporting 147 passed. No error surfaced until human review of the PR diff.

### Root cause

During `git cherry-pick` with `--strategy-option=ours`, "ours" means the branch
being cherry-picked INTO at that point in time — which is based on main. But
add/add conflicts and some content conflicts were resolved in the wrong direction,
taking the recovery commit's older version of files that main had substantially
expanded.

### Detection method that works

After any cherry-pick with conflicts, run:

```bash
for f in $(git diff --name-only main...HEAD); do
  main_n=$(git show "main:$f" 2>/dev/null | wc -l | tr -d ' ')
  branch_n=$(git show "HEAD:$f" 2>/dev/null | wc -l | tr -d ' ')
  [ "$branch_n" -lt "$main_n" ] && echo "SHORTER ⚠  $f  main=$main_n branch=$branch_n"
done
```

Any file where branch < main line count is suspicious. Then do a full `git diff
main HEAD -- <file>` on each and classify every removed line as either intentional
or accidental.

### Fix

Restore truncated files verbatim from main:

```bash
git show main:path/to/file > path/to/file
git add path/to/file
```

Then verify content diffs for zero-delta files (same line count ≠ same content —
check for replaced paragraphs, reversed identity text, injected duplicates).

### Rule going forward

**Assume everything is wrong after a cherry-pick with conflicts.**
Treat the line-count audit as mandatory before any push, not optional.
Files shorter than main = immediate stop and manual review.
Line-count parity is necessary but not sufficient — run full `git diff main HEAD`
on every changed file and justify each removed line.

### Open follow-ups

- Add line-count audit step to `scripts/review/repo_hygiene.py` as a pre-merge
  CI gate for branches with cherry-pick history (future work).
## 2026-05-04 — Technical Architecture: Ghost Path Extraction

- **Symptom**: Advanced v1 features (symlink automation, IP sync) were lost during the structural rewrite to orama-system.
- **Cause**: Focus on 'clean lineage' led to a feature regression by discarding the 'messy' main backup.
- **Solution**: Use the `recovery-20260424` branch as a clean-room for extraction.
- **Rule**: Every 'v1 hack' is a potential v2 primitive. Audit the `backup-main` tag (1675ab4) for high-value logic before finalizing the v2 microkernel.
- **Reference**: Symlink automation logic identified in Commit 1675ab4 (start.sh).

---

## 2026-05-06 — Claude — Idempotency, validator drift, and CWD anchoring (Codex P1/P2)

**Agent**: Claude (Sonnet 4.6) + Codex (chatgpt-codex-connector)
**Branch**: check-recovery-gemini → PR #32
**Severity**: High — three latent footguns in `start.sh` + cross-validator drift

### What Codex caught that single-pass review missed

PR #32 (commit b7733f1) integrated the `_ensure_symlink` automation from
commit 1675ab4. Local `pytest` was green and a manual run of the symlink
logic against the real PT path "worked." Codex review then surfaced three
issues that would only manifest in production startups:

1. **Regular-file crash under `set -e`** — `_ensure_symlink` only checked
   `[ ! -L "$link" ]` (not a symlink) before `ln -s`. When the link path
   was a tracked regular file (e.g. `network_autoconfig.py` is a real
   tracked Python module in this repo), `ln -s` returned exit 1 with
   "File exists" and `set -e` killed `start.sh` before any service
   launched. **Local manual tests missed this** because the link path
   was empty during testing — the test environment hadn't simulated the
   tracked-file case.

2. **Validator policy drift** — `repo_hygiene.py` had momentarily been
   restored to a single-identity policy (`cyre <Lawrence@cyre.me>`),
   while `check_identity.sh` accepted both `cyre` and `Codex`. Codex
   sessions would pass the gate-script but fail the hygiene script and
   the test that wraps it. The two validators must enforce the *same*
   set or one becomes a fiction.

3. **CWD-dependent symlink** — `_ensure_symlink "network_autoconfig.py"
   "$_REL_NET_CONFIG"` ran with whatever CWD `start.sh` was invoked
   from, not `$SCRIPT_DIR`. Worked in dev because we always ran from
   the repo root. Would silently misroute the symlink the moment a user
   typed `/path/to/start.sh` from elsewhere.

### Root patterns

These three findings collapse to **two patterns** worth promoting to
v2 design decisions:

#### Pattern A — Idempotent filesystem helpers (4-state guard)

Any helper that mutates the filesystem must explicitly handle every
state of the destination, in priority order:

```bash
_ensure_symlink() {
  local link="$1" target="$2"
  if [ -L "$link" ] && [ -e "$link" ]; then
    return 0                                      # 1. valid symlink → no-op
  elif [ -L "$link" ] && [ ! -e "$link" ]; then
    # 2. broken symlink → re-link if target exists
    [ -e "$target" ] && rm "$link" && ln -s "$target" "$link"
  elif [ -e "$link" ]; then
    # 3. regular file/dir → warn and skip (do NOT clobber)
    echo "WARN: $link occupies path as regular file; skipping symlink"
  else
    # 4. nothing → create
    ln -s "$target" "$link"
  fi
}
```

The non-negotiable property: every branch returns 0. No state crashes
under `set -e`. Idempotent across N invocations.

#### Pattern B — Single-source policy, multi-validator consumption

Allowed-identity lists, hardware policies, port assignments, allow/deny
patterns — anything that two scripts both check — must live in **one
file** that both scripts load. Constants duplicated across `bash` and
`python` will drift. Drift only surfaces when the rare branch fires.

In v1 today: two validators, two source-of-truth lists. In v2:
`config/identities.yaml` (or equivalent), loaded by both bash and
python via shared shim.

#### Pattern C — Anchor every CWD-sensitive call

Operations that resolve paths from `pwd` (`ln -s`, `cd`, relative
`subprocess` calls, `Path()` without absolute prefix) must run inside
`(cd "$SCRIPT_DIR" && ...)` or use absolute paths. Defaulting to "the
caller's CWD" is a footgun that hides until invoked from elsewhere.

### Detection method

For any new shell script touching the filesystem:

```bash
# Smoke test — assume the worst case for every state
TMPDIR=$(mktemp -d) && cd "$TMPDIR"
echo "tracked" > foo                    # state: regular file
_ensure_symlink "foo" "/some/target"    # must NOT crash under set -e
ln -s /nonexistent broken_link          # state: broken symlink
_ensure_symlink "broken_link" "."       # must re-link or warn
ln -s . valid_link                      # state: valid symlink
_ensure_symlink "valid_link" "."        # must be no-op
_ensure_symlink "fresh" "."             # state: nothing
_ensure_symlink "fresh" "."             # second run — still no error (idempotency)
```

Run all four states. Run each twice. Exit code must be 0 every time.

### Multi-agent review beats single-agent review

This is the third independent finding from a Codex pass that Claude
single-pass review missed (Gemini caught the api_server.py state-env
mismatch on a prior session; Codex caught the cherry-pick truncation
on this session; Codex caught these three on the same PR). For
significant changes, multi-model review pays for itself.

### Open follow-ups → see v2 design

These patterns are now first-class v2 design requirements. See:
- `docs/v2/11-idempotency-and-guard-patterns.md` — codified patterns
- `docs/v2/10-v1-hacks-automation-orbit.md` — Link Watcher must use
  the 4-state guard from day one
- `docs/v2/01-kernel-spec.md` — kernel filesystem helpers MUST be
  idempotent + CWD-anchored; pre-merge CI gate must run the smoke
  test above against every fs helper

---

## 2026-05-06 — xAI model retirement 2026-05-15; grok-4.3 + grok-4.20-non-reasoning defaults

**What changed**

xAI is retiring 8 model IDs on 2026-05-15 12:00 PM PT. Any
`model_hardware_policy.yml` entry or router constant still referencing them
will cause a hard dispatch failure at that time.

**Retired IDs**

`grok-4-1-fast-reasoning`, `grok-4-1-fast-non-reasoning`,
`grok-4-fast-reasoning`, `grok-4-fast-non-reasoning`, `grok-4-0709`,
`grok-code-fast-1`, `grok-3`, `grok-imagine-image-pro`

**Replacement routing (v2 defaults)**

| Workload | New model | Notes |
|----------|-----------|-------|
| Reasoning / coding | `grok-4.3` | Coding → PLAN-ONLY until Win-coder slot available; reasoning → full ACT always |
| Non-reasoning / non-coding | `grok-4.20-non-reasoning` | research, ops, chat, summarisation |
| Image generation | *(no announced replacement)* | Surface error to user; do not silently fall back |

**Coding ACT gate**: resumes when `swarm_state.md` reports `WIN_CODER: AVAILABLE`
(same file already polled by the Windows-sequential-load rule).

**Design rule promoted to v2**

- All model ID lists must be single-source in `perpetua-core/config/` (Pattern B
  from `11-idempotency-and-guard-patterns.md`) — never duplicated in bash + python.
- Add CI gate `test_no_retired_model_ids` that greps `model_hardware_policy.yml`
  for any known-retired ID and fails if found.

**Spec doc**: `docs/v2/12-xai-model-migration-2026-05.md`

---

## 2026-05-07 — Codex CLI unknown-model fallback; local_models.json strategy; qwen3.5-local renamed

### Problem

Codex CLI ships a built-in model catalog for OpenAI cloud models only.
When pointing it at a local Ollama endpoint with an unregistered model ID
(`qwen3.5:9b-nvfp4`), Codex falls back to 272K token defaults. The local
server never sees a context that large; it crashes with overflow errors.
Plan mode and structured output also break silently because capability
flags (`supports_reasoning`, `supports_tools`) are unknown.

Compounding this: the previous local alias `qwen3.5-local:latest` was
deleted from Ollama and replaced by `qwen3.5:9b-nvfp4` — 6 source files
across two repos still referenced the old ID.

### Fix (immediate — local machine)

1. Created `~/.codex/local_models.json` with correct context caps and
   capability flags for all Ollama models (local + cloud-proxy).
2. Added `model_catalog_json = "~/.codex/local_models.json"` to
   `[model_providers.ollama-launch]` in `~/.codex/config.toml`.
3. Key values for `qwen3.5:9b-nvfp4`:
   - native `context_length = 262144` (from `ollama api/show model_info`)
   - safe local cap: `context_window = 32768` (Mac RAM constraint)
   - `supports_reasoning = true`, `supports_tools = true`

### Model ID rename sweep

| File | Old → New |
|------|-----------|
| `orama-system/setup_macos.py` | `qwen3.5-local:latest` → `qwen3.5:9b-nvfp4` |
| `orama-system/portal_server.py` (×2) | role string updated |
| `PT/packages/local-agents/src/client.js` | DEFAULTS + comment |
| `PT/packages/local-agents/tests/client.test.js` (×6) | test fixtures |

### Design rule promoted to v2

- `~/.codex/local_models.json` is the **single source of truth** for
  local Ollama model metadata (context caps, capability flags).
- Auto-generate with `scripts/gen_local_models_json.py` whenever Ollama
  model list changes. Never edit manually.
- In v2: `perpetua-core/config/ollama_catalog.json` mirrors this schema;
  `ollama_catalog.example.json` ships with the repo; real file gitignored.
- Apply Pattern B (`11-idempotency-and-guard-patterns.md` §3): one config
  file, many consumers (Codex CLI, HardwarePolicyResolver, LocalAgentClient).
- CI gate: `test_no_stale_model_ids` greps for retired / old-alias model
  IDs in all source files and fails if any are found.

**Spec doc**: `docs/v2/13-local-model-catalog-strategy.md`

---

## Session 2026-05-08 — start.sh Warm-Cache + Parallel Probes (Layer-3 side)

**Problem:** When PT's `alphaclaw_manager --resolve` failed (Python missing, network blip), `start.sh` fell back to bare offline defaults — services started with empty endpoints. Banner tier-detection ran 3 sequential `nc -z` probes (3s worst case).

**Fixes shipped (1 commit on `main`):**

1. **Warm-cache fallback** — when PT resolve fails, read `.state/routing.json` (last known good state from PT) and re-export `PT_MODE=cached`, `PT_DISTRIBUTED`, `PT_ALPHACLAW_PORT`, `WIN_IP`, `PT_SCENARIO`, `PT_MODE_SOURCE=cache`, `PT_AGENTS_STATE`. Stale-data warning is always printed so operators know cache is in use.
2. **Parallel banner probes** — 3 `nc -z -w 1` calls now run as background subshells writing to mktemp files, then `wait`. Total banner delay = max(1s) instead of 3s.

**Why this matters with PT v0.9.9.9:**
- PT now writes `scenario_name` into routing.json. Warm cache reads it and exports `PT_SCENARIO` so banner + portal can show the *last* scenario when resolve is dead.
- The PT scenario engine + warm cache together mean the constellation degrades gracefully: live → cached → offline-defaults, never opaque hang.

**Gemini CLI syntax update:** `gemini` invocations must now use `--yolo` (alias `-y`) so the subprocess auto-approves tool prompts. Without it Gemini stalls on the first sandbox gate. Patched `scripts/spawn_agents.py:_dispatch_gemini` and the `SKILL.md` example.

**Deferred** (both Mac + Win required):
- Live `start.sh` validation across LAN (cache hits when Win .108 unreachable but Mac .110 still pingable)
- Verify banner tier=1 (FULL) when both nodes online

Re-run in ~2 days:
```bash
./start.sh --probe-only       # just probes, no service start
nc -z -w 1 192.168.x.108 1234  # confirm Win LMS reachable
```

---

## 2026-05-08 — V1 supervisor shipped; v2/14 spec written

**Context:** Three reference files synthesised into V1 implementation + V2 spec.

**Perpetua-Tools changes (all in same commit):**
- `orchestrator/supervisor.py` — V1 `OrchestrationSupervisor` (jsonl, no DB)
- `orchestrator/worker_registry.py` — static WORKER_REGISTRY (echo, ollama-mac, lmstudio-mac, codex, gemini)
- `utils/action_validator.py` — two-phase gate
- `scripts/mac_probe.sh` — hardware detection (Mac14,9 = 16GB/16GPU/arm64/standard tier)
- 5 new FastAPI endpoints under `/v1/jobs`
- 192/192 tests green (including 13 new smoke tests)

**orama-system v2 spec added:**
- `docs/v2/14-supervisor-and-anthropic-patterns.md` — V2 DB persistence, audit log, MAESTRO/SWARM gates, token-efficiency rules, hardware-aware installer plan

**Key rules confirmed for all agent sessions:**
- `MAX_DEPTH=1`, `MAX_THREADS=25` (Anthropic hard limits)
- All backends: use POST API, never `ollama run` in a shell
- `gemini --yolo` required for non-interactive dispatch
- Checkpoint written BEFORE CancelledError propagation

**Legacy `orchestrator.py` FastAPI unchanged** — backwards-compatible, will be superseded by V2.

---

## 2026-05-08 — Cross-platform portal + start.sh + Windows counterpart

**Context:** All `start.sh` CLI modes were only surfaced at the terminal; the portal UI had no stop/restart/discover/policy buttons. `pid_on_port()` and `wait_for_port()` used `lsof` and `nc` exclusively, which are macOS-only. No Windows entry point existed.

### What broke / what was missing

| Gap | Root cause |
|-----|-----------|
| Portal version stuck at 0.9.9.7 | Forgot to bump `VERSION` constant after v1 work |
| `/v1/jobs` not visible in UI | V1 supervisor endpoints added to PT but portal never polled them |
| `--stop`, `--discover`, `--hardware-policy` terminal-only | `portal_server.py` had no corresponding routes |
| `lsof -ti tcp:PORT` fails on Linux | `lsof` not always installed; `ss` is the Linux equivalent |
| `nc -z` fails on bare containers | Minimal Docker images ship without `nc`; bash `/dev/tcp` is always available |
| `nc -z -w 1` banner probes sequential | 3 × 1s = 3s banner lag; should be 3 parallel subshells → max 1s |
| `setup_macos.py` runs on Linux/CI | Preflight has macOS-specific `xattr` and `codesign` calls; hard-errors on Linux |
| No Windows start script | No way to boot the stack on the Windows node without WSL |

### Fixes shipped (commit 252a473 on main)

**`portal_server.py`:**

1. `VERSION = "0.9.9.8"` — bump.
2. **Service Controls bar** (`_render_service_control_section()`):
   - `POST /api/stop` — SIGTERMs all three services using `_pid_on_port()` (cross-platform: `lsof` → `ss` → fallback)
   - `POST /api/restart/{service}` — kills + `subprocess.Popen(start_new_session=True)` respawn; logs to `.logs/<svc>.log`
   - `POST /api/rediscover` — runs `discover.py --force` in a thread executor; returns updated IP summary
   - `GET /api/hardware-policy` already existed; JS now calls it from the "Re-check Policy" button and toasts result
3. **Supervisor Jobs panel** (`_render_supervisor_jobs_section()`):
   - `_probe_supervisor_jobs()` added to the `asyncio.gather` in `api_status()` — zero extra RTT; result included in `supervisor_jobs` key
   - `GET /api/v1/jobs` proxies to PT; JS `refreshJobs()` polls every 8s independently
4. New CSS: `.svc-btn`, `.svc-ctrl`, `.jobs-table` — dark theme compatible
5. `import signal, subprocess, time` added (were missing)

**`start.sh`:**

```bash
# Before (macOS-only):
pid_on_port() { lsof -ti "tcp:$1" 2>/dev/null | head -1 || true; }
while ! nc -z localhost "$port" 2>/dev/null; do

# After (cross-platform):
pid_on_port() {
  if command -v lsof; then lsof -ti "tcp:$1" | head -1
  elif command -v ss;  then ss -tlnp "sport = :$1" | grep -oP 'pid=\K\d+' | head -1
  elif command -v fuser; then fuser "$1/tcp" | awk '{print $1}' | head -1
  fi
}
_port_open() {
  if command -v nc; then nc -z localhost "$1" 2>/dev/null
  else (echo >/dev/tcp/localhost/"$1") 2>/dev/null; fi
}
while ! _port_open "$port"; do
```

- `_nc_probe()` helper in banner — same `nc` vs `/dev/tcp` dual path; all 3 probes remain parallel
- `setup_macos.py` now guarded: `[ "$_OS_NAME" = "Darwin" ]` — Linux/CI skip with INFO log

**`windows/` folder:**

| File | Role |
|------|------|
| `start.ps1` | All 6 CLI modes; `Get-PidOnPort` (netstat), `Wait-ForPort` (TcpClient), `Start-Service` (Popen equivalent via `ProcessStartInfo`) |
| `install.ps1` | Idempotent venv + deps + openclaw.json defaults; pywin32 + colorama |
| `requirements-windows.txt` | pywin32, colorama, netifaces |
| `README.md` | Parity table + architecture notes |

**`windows/start.ps1` platform-translation table:**

| bash | PowerShell |
|------|-----------|
| `lsof -ti tcp:PORT` | `netstat -ano` + regex for LISTENING PID |
| `nc -z localhost PORT` | `TcpClient.ConnectAsync().Wait(500ms)` |
| `open URL` | `Start-Process URL` |
| `ipconfig getifaddr en0` | `Get-NetRoute` gateway → `.110` heuristic |
| `kill PID` | `Stop-Process -Id PID -Force` |
| subprocess bg `&` | `ProcessStartInfo(CreateNoWindow=true)` + async stream copy |
| `.paths` sourced file | `.paths.ps1` dot-sourced with `$PtDir`, `$UsPython` vars |

### Key rules derived

- **Never assume `lsof`** — it is missing on Debian minimal, Alpine, and distroless containers. Always cascade: `lsof → ss → fuser`.
- **Never assume `nc`** — Alpine and scratch images ship without it. Bash `/dev/tcp` is a shell built-in and always available.
- **`setup_macos.py` guard is mandatory** — the script calls `xattr -cr` and `codesign -s -` which are macOS-only binaries. It will `FileNotFoundError` on Linux.
- **`-w 1` (timeout) must come before the host in `nc`** — `-z -w 1 host port` works; `-z host port -w 1` silently ignores the flag on some Linux builds.
- **`Start-Job` vs `ProcessStartInfo`** — PowerShell `Start-Job` creates a new PS host (slow, large). `System.Diagnostics.ProcessStartInfo` with `CreateNoWindow=true` is the correct analogue of bash `cmd &`.
- **Windows GPU: 1 model at a time** — `install.ps1` prints this as a hard warning; `start.ps1` never sets `LM_STUDIO_WIN_ENDPOINTS` to multiple URLs.

### Verification

```bash
# macOS
bash -n start.sh && echo OK                           # syntax
bash scripts/mac_probe.sh | python3 -m json.tool       # JSON valid
python3 -c "import ast; ast.parse(open('portal_server.py').read()); print('OK')"

# Linux (simulate)
_OS_NAME=Linux bash start.sh --status                  # setup_macos skipped
ss --version && lsof --version || true                 # check which probe tools exist
```

### Deferred

- `start.ps1` end-to-end on a real Windows + PowerShell 5.1 box (no WSL)
- `install.ps1` tested with Python 3.11 from python.org (not conda/pyenv)
- Portal `POST /api/restart/portal` self-restart (kills the process serving the request — needs supervisor process or systemd watchdog to respawn)

---

## 2026-05-14: Monumental Error — Wrong Repo Build Documented as Canonical Phase 1

**Session:** docs/v2 enrichment (intended: post-Phase 1 reconciliation)
**Artifact:** `docs/wiki/10-wrong-repo-build-what-not-to-do.md` ← read this for the full delta record

### What happened

An AI agent (Claude) built a v2 kernel in the **wrong local directory**
(`OpenClaw/perpetua-core`) instead of the correct one (`Documents/oramasys/perpetua-core`),
pushed it to a **non-canonical GitHub remote** (`diazMelgarejo/perpetua-core`), then created
`docs/v2/15-phase1-as-built.md` and modified 4 other `docs/v2/` files documenting this
wrong build **as if it were the canonical Phase 1 implementation**.

The canonical v2 build had already been shipped **13 days earlier** (2026-05-01) at:
- `oramasys/perpetua-core` — commit `2f717f5`, 32 tests, 65-line kernel + all 6 plugins
- `oramasys/oramasys` — commit `d123420`, 4 tests, FastAPI glass-window
- `oramasys/agate` — commits `755e1de`/`f1d5a57`, hardware policy spec + GGUF RFC

All 3 canonical repos were `0 ahead / 0 behind` their GitHub remotes. The docs were
correct before the wrong commit (`5f21e83`).

### Violations of the agreed spec

| Spec decision | Canonical (`oramasys/perpetua-core`) | Divergent (`diazMelgarejo/perpetua-core`) |
|---------------|--------------------------------------|------------------------------------------|
| D8 revision: 65-line + plugins | ✅ 65-line engine + `graph/plugins/` | ❌ ~130-line integrated, no plugins/ |
| D7: Pydantic v2 BaseModel | ✅ `class PerpetuaState(BaseModel)` | ❌ `pydantic.dataclasses.dataclass` |
| Spec: `scratchpad: dict[str,Any]` | ✅ `scratchpad: dict[str, Any]` | ❌ `scratchpad: str = ""` |
| D2: `oramasys` org | ✅ `oramasys/perpetua-core` | ❌ `diazMelgarejo/perpetua-core` |
| Python 3.11+ | ✅ `requires-python = ">=3.11"` | ❌ Python 3.9.6 |
| `@tool` decorator | ✅ `graph/plugins/tool.py` done | ❌ absent |
| Async GossipBus | ✅ `aiosqlite` | ❌ `sqlite3` sync |

### Root cause

- Did not verify `git remote -v` before first push of the new repo
- Did not check whether canonical build already existed before "building Phase 1"
- Skipped the AskUserQuestion gates that the plan required
- Proceeded without brainstorming/planning approval

### Fix applied (this commit)

- `docs/v2/15-phase1-as-built.md` (wrong-build doc) → **MOVED** to `docs/wiki/10-wrong-repo-build-what-not-to-do.md` as a cautionary artifact
- `docs/v2/00-context-and-decisions.md`, `04-build-order.md`, `06-open-questions.md`, `README.md` → **REVERTED** to `935ce54` (pre-5f21e83, correct state)

### Never again

1. **Before any `git push` to a new repo:** run `git remote -v` and confirm the remote matches the agreed org (`oramasys/*` for v2, `diazMelgarejo/*` for v1-legacy)
2. **Before "building Phase 1":** search for the repo in the correct org — it may already exist
3. **Never skip `AskUserQuestion` gates** in a plan — they exist precisely to prevent this
4. **`oramasys/*` is the ONLY valid home for v2 code.** `diazMelgarejo/*` is v1-legacy only.
5. **The shipped canonical scaffold (`oramasys/*`) takes precedence** over any in-session build

**Full agent-readable post-mortem:** `docs/wiki/10-wrong-repo-build-what-not-to-do.md` — enriched 2026-05-16 with complete incident timeline, failure mode analysis, spec violation table, and "what future agents MUST do" checklist. Read this before any v2 docs/ or oramasys/ work.

---

## 2026-05-16: `.gbrain-source` is machine-local — never commit it

`.gbrain-source` is a kubectl-style worktree pin written by `/sync-gbrain`. It contains
the name of the indexed gbrain source for this worktree on this machine (e.g. `orama-src`).
Different machines register different source names; committing it would break gbrain routing
on every other machine that clones the repo.

**Fix:** Added `.gbrain-source` to `.gitignore` (2026-05-16).
**Rule:** If you see `.gbrain-source` untracked in any repo, add it to `.gitignore` immediately. Do not `git add` it.

- Linux `ip route get 8.8.8.8` — validate on Ubuntu 22.04 + Debian 12 + Alpine 3.19

---

## 2026-05-16: RC-1 Orchestration Session — Gemini routing, OpenRouter smart-merge, Vite pitfalls

### 1. Gemini is NOT the default reader — "Gemini-Analyzer use-case only"

**Decision (locked in RC-1 master plan):** Gemini is routed ONLY for:
- Visual diff / screenshot comparison
- Whole-repo architecture mapping (>5000-line diffs, multi-file cross-cutting)
- Multi-file stale-doc detection
- Second-opinion code review when explicitly requested

**The default reading/coding agent is the OpenRouter free-model stack** (Nemotron 3 Super → MiniMax M2.5 → DeepSeek V4 Flash → gpt-oss-120b → GLM 4.5 Air → Ling 2.6 Flash → Free Router).

**Why this matters:** Previous practice had Gemini mentioned generically as "the reader" — this caused agents to default to Gemini for every file read, wasting quota and adding latency. Gemini is a specialized instrument, not the default hammer.

**Canonical policy:** `bin/orama-system/mcp-orchestration/SKILL.md` §2 "Routing strategy".

---

### 2. Smart-merge pattern for OpenClaw config patching

**Problem:** Naively patching `openclaw.json` with a model policy risks overriding the user's local `primary` (which must remain `ollama/qwen3.5:9b-nvfp4` on Mac per CLAUDE.md hard requirement).

**Pattern established:**
- Policy file uses `fallbacks_to_merge` and `models_to_merge` keys (NOT `primary`/`fallbacks`)
- Apply script PRESERVES existing `agents.defaults.model.primary` unless `--force-primary` flag is passed
- Removes Gemini from the front of any existing fallbacks list before appending the OpenRouter chain
- Gemini is pushed to END of fallbacks as 3rd-choice (not 1st)
- Script lives at: `scripts/apply-openrouter-free-defaults.sh`
- Verify with: `scripts/verify-openrouter-models.sh`

**Rule:** Any script that patches live config must read the existing primary first and only append/merge fallbacks. Never clobber local primary.

---

### 3. jq dedup-preserve-order — avoid `unique_by(.)`

**Problem:** `unique_by(.)` in jq sorts alphabetically as a side effect. When deduping a fallbacks array after merging, this silently promoted Gemini to the top of the list (alphabetically first `google/*`), defeating the entire "Gemini as last resort" policy.

**Correct pattern:**
```bash
| reduce .[] as $item (
    [];
    if any(.[]; . == $item) then . else . + [$item] end
  )
```
This deduplicates while preserving insertion order — first occurrence wins. Use this whenever you need dedup-without-sort in jq.

**Why `unique_by(.)` is wrong:** It's documented to sort, but in practice you expect it to just dedupe. The combination of merge + unique_by produces a sorted array, not a priority-ordered one.

---

### 4. Vite + TypeScript composite-project pitfalls

Two distinct issues that both caused build/typecheck failures:

**Issue A: tsconfig composite conflict**
- Problem: `tsconfig.json` had `"include": ["src", "vite.config.ts"]`. The `tsconfig.node.json` used `composite: true` and also covered `vite.config.ts`. TypeScript expected pre-built `.d.ts`/`.js` output for the composite sub-project and errored with TS6305.
- Fix: Remove `vite.config.ts` from `tsconfig.json` include. The file is already handled by the node sub-project.
- Canonical: `"include": ["src"]` in `tsconfig.json`

**Issue B: Path aliases must be declared in BOTH places**
- Problem: `@/*` alias declared in `tsconfig.json` paths works for TypeScript type resolution but Vite's Rollup bundler doesn't read tsconfig. Build failed with "Rollup failed to resolve import `@/components/Shell`".
- Fix: Add `resolve.alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) }` to `vite.config.ts` in addition to the tsconfig paths entry.
- Rule: Every `@/*`-style alias needs two registrations: one in tsconfig (for tsc/IDE) and one in vite.config.ts (for Rollup/bundler).

---

### 5. MCP orchestration canonical SKILL.md location

**Before:** Two drift-prone root files (`OpenClaw/MCP_ORCHESTRATION_SKILL.md`, `OpenClaw/MCP_ORCHESTRATION_SKILL_v2.md`) each evolving independently.

**After:** Single canonical skill at `bin/orama-system/mcp-orchestration/SKILL.md`. The old root files are redirect stubs pointing to it.

**Rule:** If you see multiple files claiming to be "the MCP orchestration policy", the canonical one is in `bin/orama-system/mcp-orchestration/SKILL.md`. The others are stubs — do not edit them.

---

### 6. Vite operator console — build-verified RC-1 baseline

- Stack: React 18 + Vite 5 + TanStack Query 5 + Tailwind 3
- Source: `src/` (16 files, 0 TypeScript errors, build output ~68KB gzip)
- Backend proxy: `/api/*` → `http://localhost:8001` (portal_server.py)
- Key files: `src/features/command-center/CommandCenter.tsx` polls `/api/app/state` every 5s; falls back to `mockState` on error
- `src/data/mockState.ts` provides offline-capable fixtures so the console always renders
- Commit: `1cfb31e` on `web-app-orchestration-v2-implementation`

---

### 7. Branch hygiene — FF-merge timing

When feature work spans multiple commits across a branch and partial work is already on main:
- Merge foundation commits to main early (after a coherent milestone) so history stays linear
- Use `git merge --ff-only` when the branch has only additive commits ahead of main — avoids a merge commit in the log
- Do NOT squash multi-session work that has already been reviewed — preserves attribution per commit
