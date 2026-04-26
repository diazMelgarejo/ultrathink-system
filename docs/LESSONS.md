# Lessons — orama-system

> **Canonical path**: `docs/LESSONS.md`
> **Previous path**: `.claude/lessons/LESSONS.md` (now redirects here)
> **Purpose**: GitHub-auditable persistent memory across all ECC, AutoResearcher, and Claude sessions.
> **Cross-repo companion**: [Perplexity-Tools/docs/LESSONS.md](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/LESSONS.md)
>
> **Rules**:
> - Read this file at the start of every session
> - Append new learnings before ending a session
> - Keep entries dated and agent-tagged (`ECC | AutoResearcher | Claude`)
> - For organized, deep-dive explanations see the **[wiki →](wiki/README.md)**
> - For agent behavioral rules see **[SKILL.md →](../SKILL.md)**

---

## continuous-learning-v2

This repo uses [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).
Instincts: `.claude/homunculus/instincts/inherited/orama-system-instincts.yaml`
Import command: `/instinct-import .claude/homunculus/instincts/inherited/orama-system-instincts.yaml`

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
- Canonical commit identity is `cyre <Lawrence@cyre.me>`.
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

