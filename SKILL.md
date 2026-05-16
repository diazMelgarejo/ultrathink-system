# orama-system Agent Skills

> **For agents:** This file is your behavioral ruleset for this repo. Read it before making any change. Rules here are derived from real bugs — every "never" has a story behind it.
>
> Full context for each rule lives in [docs/wiki/](docs/wiki/README.md).
> Session log lives in [docs/LESSONS.md](docs/LESSONS.md).

---

## Skill 1 — Read LESSONS.md First

**Trigger:** Start of every session, before any code change.

```bash
# Read the shared knowledge base
cat docs/LESSONS.md
```

**Never start coding without reading the session log.** Multi-agent sessions write scope claims and version updates here — missing them causes silent conflicts and version drift.

→ [docs/LESSONS.md](docs/LESSONS.md)

---

## Skill 2 — CI Dependency Guard

**Never replace `pip install pkg1 pkg2 pkg3` with `pip install ".[extras]"` without first auditing every removed package into the extras group.**

`hatchling` must ALWAYS be in `[project.optional-dependencies] test`:

```toml
[project.optional-dependencies]
test = [
  "pytest>=8.0.0",
  "hatchling>=1.26.0",   # required for python -m build --no-isolation
  ...
]
```

Verify before commit:
```bash
python -c "import fastapi, httpx, uvicorn, pydantic, slowapi, pytest, hatchling, build"
```

→ [docs/wiki/01-ci-deps.md](docs/wiki/01-ci-deps.md)

---

## Skill 3 — Idempotent Install Rules

After any `npm install -g`:
1. Check execute bits: `stat $(which binary) | grep Mode` — `+x` must be set
2. Auto-fix if missing: `chmod +x $(which binary)`
3. Catch `PermissionError` **separately** from `CalledProcessError` in every subprocess block
4. **Never `capture_output=True`** in bootstrap/install subprocess calls
5. **Never hardcode model names** — query `/v1/models` (LM Studio) or `/api/tags` (Ollama) at runtime

→ [docs/wiki/02-idempotent-installs.md](docs/wiki/02-idempotent-installs.md)

---

## Skill 4 — Device Identity & GPU Safety

**One inference backend per physical device.** Never load two models on the same GPU simultaneously.

```bash
# Before assigning researcher roles:
# 1. Detect local IPs via UDP routing trick
# 2. Zero out any "Windows" endpoint that resolves to a local IP
# 3. On same device: Ollama > LM Studio
```

**Crash recovery is always ≥ 30 seconds.** Immediate retry after 503/404 triggers GPU thrashing. Classify errors before sleeping:
- `503` = model loading (LM Studio startup)
- `404` = model unloaded (Ollama eviction)
- `ConnectError` = backend offline

**Always show a progress bar during recovery.** `asyncio.sleep(N)` is invisible.

→ [docs/wiki/03-device-identity.md](docs/wiki/03-device-identity.md)

---

## Skill 5 — Gateway Commandeer-First Bootstrap

**Probe before install. Never start a duplicate gateway.**

```python
# Correct order:
existing = await _find_running_gateway()  # probe all candidate ports
if existing:
    commandeer(existing)   # update config only — do NOT restart
    return
# Nothing found — proceed with install
```

`OPENCLAW_CANDIDATE_PORTS = [18789, 11435, 8080, 3000]` — extend via `OPENCLAW_EXTRA_PORTS` env var.

→ [docs/wiki/04-gateway-discovery.md](docs/wiki/04-gateway-discovery.md)

---

## Skill 6 — Bulk sed Safety

**`grep -rn` before any bulk `sed`. Scope import renames to `.py` files only.**

```bash
# Step 1 — preview ALL matches
grep -rn "old_pattern" --include="*.py" --include="*.md"
# Step 2 — if any match is a filename, narrow the pattern
find . -name "*.py" -exec sed -i 's/from old\./from new./g' {} +
# Step 3 — verify no filename strings were corrupted
```

Never apply import-rename regexes to `.md`, `.sh`, `.yaml`, `.txt`.

→ [docs/wiki/05-bulk-sed-safety.md](docs/wiki/05-bulk-sed-safety.md)

---

## Skill 7 — Multi-Agent Collaboration Protocol

When two agents may be working simultaneously:

1. **Read `docs/LESSONS.md` first** — scope claims are written here
2. **Claim scope** before touching files: append `<!-- IN PROGRESS: <name> — <file> -->` to LESSONS.md
3. **Additive changes only** — append, don't rewrite; avoids merge conflicts
4. **Commit body must name changed constants/APIs** — it's the only async channel between agents
5. **Never hardcode LAN IPs in source defaults** — `127.0.0.1` in code, real IPs in `.env` only
6. **Branch from `origin/main`** — never from a detached HEAD or agent-created branch
7. **Use dated salvage branches** for risky Git work: `yyyy-mm-dd-001-brief-summary`
8. **Confirm Git identity before committing**: `bash scripts/git/check_identity.sh`
9. **Stash untracked files before branch surgery**: `git stash push --include-untracked -m "preserve work before <operation>"`

Version registry: **current version is `0.9.9.8`**. Never bump without explicit user instruction. All canonical locations are listed in [docs/wiki/06-multi-agent-collab.md](docs/wiki/06-multi-agent-collab.md).

→ [docs/wiki/06-multi-agent-collab.md](docs/wiki/06-multi-agent-collab.md)

---

## Skill 8 — Startup & Environment Rules

1. **Never call `input()` in a daemon thread** — use `sys.stdin.isatty()` guard
2. **Redirect stdin in start.sh**: `python script.py </dev/null`
3. **`stdin=subprocess.DEVNULL`** on all long-running child `Popen` calls
4. **Always `load_dotenv(".env")` and `load_dotenv(".env.local", override=True)`** at module level — shell-exported vars alone are unreliable
5. **Fire all backend probes concurrently** with `asyncio.create_task()` — don't probe sequentially
6. **`_persist_detected_ips()`** after successful probes — config becomes self-correcting

→ [docs/wiki/07-startup-ip-detection.md](docs/wiki/07-startup-ip-detection.md)

---

## Skill 9 — Markdown Redirect & Size Rules

Before editing any `*.md` file:

1. Read `docs/LESSONS.md` and `docs/wiki/README.md` when the edit touches repo guidance, lessons, or moved docs.
2. Keep links relative and GitHub-renderable. Do not write absolute filesystem links into tracked markdown.
3. Preserve redirect/canonical-path notes when moving or renaming markdown.
4. Warn and ask the user before adding a new markdown file over 200 lines or growing an existing markdown file over 500 lines. Suggest moving details to `references/`, `docs/wiki/`, or a sub-skill.
5. Run `python3 scripts/review/repo_hygiene.py .` before committing markdown.

---

## Quick Reference: Session Commands

```bash
# Start of session
cat docs/LESSONS.md          # shared knowledge base — mandatory
git checkout main && git pull --ff-only origin main
python -m pytest -q          # must be green before new work

# Verify environment
python -c "import fastapi, httpx, uvicorn, pydantic, slowapi, pytest, hatchling, build"
uname -m                     # arm64 on M2 Mac (important for GPU routing)

# After new work
python -m pytest -q          # full suite before push
```

---

## Knowledge Wiki

All lessons, root-cause analyses, and architectural decisions:
**[docs/wiki/README.md](docs/wiki/README.md)**

Session logs:
- [docs/LESSONS.md](docs/LESSONS.md) — chronological, all agents

Companion repo:
- [Perplexity-Tools/SKILL.md](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/SKILL.md)
- [Perplexity-Tools/docs/LESSONS.md](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/LESSONS.md)

### Critical cautionary reference: Wrong Repo Build (2026-05-14)

**[docs/wiki/10-wrong-repo-build-what-not-to-do.md](docs/wiki/10-wrong-repo-build-what-not-to-do.md)**

An AI agent built the v2 kernel in the wrong local directory, pushed to the wrong GitHub org,
and documented it as canonical. Read this before any `docs/v2/` or `oramasys/*` work.

**The 4 checks that would have prevented it:**
1. `git remote -v` — verify remote matches `oramasys/*` before any v2 push
2. `ls ~/Documents/oramasys/<repo>/` — confirm canonical build doesn't already exist
3. Consult `CLAUDE-instru.md §1` or `project_repo_registry.md` — v1=`diazMelgarejo/*`, v2=`oramasys/*`
4. Never skip `AskUserQuestion` gates in a plan that modifies `docs/v2/`

### .gbrain-source is machine-local — never commit it

`.gbrain-source` is written by `/sync-gbrain` to pin this worktree to a gbrain indexed source.
It is machine-specific. Add it to `.gitignore` if you see it untracked. See LESSONS.md §"2026-05-16: `.gbrain-source` is machine-local".

---

## Skill 10 — External Agent Integration (Gemini · Codex · OpenClaw)

orama-system exposes `POST /ultrathink` at port 8001. Any external agent (Gemini, Codex, OpenClaw,
LangGraph, etc.) can drive orama as a black-box reasoning endpoint.

### Direct HTTP (any agent)

```bash
curl http://localhost:8001/ultrathink \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Analyse the failing test and propose a fix",
    "session_id": "gemini-sess-001",
    "task_type": "code",
    "optimize_for": "reliability"
  }'
# Response includes: status, result, session_id, nodes_visited, retry_count
```

### Gemini CLI (gemini-mcp-tool)

Install once:
```bash
npm i -g @ahoylabs/gemini-mcp-tool   # or: pip install gemini-mcp-tool
```

Register orama's MCP server:
```bash
# In ~/.gemini/settings.json → mcpServers block:
"orama": {
  "command": "python",
  "args": ["-m", "bin.mcp_servers.ultrathink_orchestration_server"],
  "cwd": "/path/to/orama-system"
}
```

Then from any Gemini session: `@orama run_ultrathink task="…"`.

### Codex / OpenCode harness

orama exposes a `.agents/skills/orama-system/` harness (Codex-compatible):

```bash
# From inside a Codex session, activate the skill:
skill .agents/skills/orama-system/SKILL.md

# Or call the endpoint directly from a Codex tool-use block:
curl http://localhost:8001/ultrathink -d '{"task_description":"…","session_id":"codex-001"}'
```

Codex harness path: `.agents/skills/orama-system/` (mirrored from `bin/orama-system/`).
Tool mapping: `.agents/skills/orama-system/agents/openai.yaml`.

### OpenClaw plugin

OpenClaw can route tasks to orama via the `orama_bridge` plugin:

```bash
openclaw run --plugin orama_bridge --task "your task here"
# or via the bridge:
python bin/mcp_servers/openclaw_bridge.py
```

Codex harness docs: https://docs.openclaw.ai/plugins/codex-harness

Register the MCP server with Claude Code:
```bash
claude mcp add --transport stdio orama-ultrathink \
  -- python -m bin.mcp_servers.ultrathink_orchestration_server
```

### Simultaneous multi-agent pattern

Run Gemini and Codex concurrently against orama:

```bash
# Terminal 1 — Gemini reviews (--yolo auto-approves tool calls; required for non-interactive)
gemini --yolo "Review the diff in $(pwd) and call @orama for deep analysis"

# Terminal 2 — Codex implements
codex "Fix the failing test using the orama API at localhost:8001 for reasoning"
```

Key rule: **never load more than one model on the Windows GPU simultaneously** — check
`docs/swarm_state.md` for `GPU: BUSY` before dispatching Windows-tier tasks.

### qwen3.5-9b-mlx — Mac thinking model

`qwen3.5-9b-mlx` is active at `localhost:1234` (LM Studio Mac, `mac_only` tier).
It is a **thinking model** — use `max_tokens ≥ 500` or content will be truncated.
Extract `choices[0].message.content`, not `reasoning_content`, in any HTTP client.

→ See `docs/LESSONS.md` entry: *qwen3.5-9b-mlx is a thinking model (2026-05-01)*

### Optional xAI fallback provider

- If `XAI_API_KEY` is set, `openclaw_bootstrap.py` injects an `xai` provider into
  `~/.openclaw/openclaw.json` with `grok-4.1-fast` and `grok-code-fast`.
- Intended scope: finance / market / M&A / factcheck fallback when primary
  providers are unavailable.

---

## Skill 11 — Codex MCP Config Postmortem Rule

**Trigger:** Any Codex MCP config error, especially `invalid transport`, GitHub MCP, OAuth/PAT confusion,
or `bearer_token_env_var`.

**Pattern:** classify transport before editing auth.

```toml
[mcp_servers.github]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]

[mcp_servers.github.env]
GITHUB_PERSONAL_ACCESS_TOKEN = "${CODEX_GITHUB_PERSONAL_ACCESS_TOKEN}"
```

**Never treat this as the whole GitHub stdio fix:**

```toml
[mcp_servers.github]
bearer_token_env_var = "CODEX_GITHUB_PERSONAL_ACCESS_TOKEN"
```

That field belongs to HTTP MCP config. For stdio servers, pass credentials through
`[mcp_servers.<name>.env]`.

Verify every MCP config fix with:

```bash
codex mcp list
```

`Auth: Unsupported` is expected for stdio and is not the failure.

**Why this rule exists:** Codex previously failed by treating the GitHub warning as a missing-token
problem. Claude fixed it by running `codex mcp list`, recognizing `invalid transport` as a schema
failure, and switching to transport-specific config. Preserve the nuance: `bearer_token_env_var` is
valid for GitHub's remote HTTP MCP endpoint, but wrong for the local npm stdio server.

→ [docs/wiki/11-codex-github-mcp-config.md](docs/wiki/11-codex-github-mcp-config.md)
