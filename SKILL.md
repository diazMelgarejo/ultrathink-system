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

Version registry: **current version is `0.9.9.7`**. Never bump without explicit user instruction. All canonical locations are listed in [docs/wiki/06-multi-agent-collab.md](docs/wiki/06-multi-agent-collab.md).

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
