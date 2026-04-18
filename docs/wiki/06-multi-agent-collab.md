# 06. Multi-Agent Collaboration — Version Registry, Scope Claims, Orphan Branches

**TL;DR:** Two agents working simultaneously on overlapping files will diverge. Use scope claims, additive-only changes, commit messages as communication, and the version registry to stay coordinated.

---

## What Broke (2026-04-12)

During a 48-hour window two agents worked simultaneously on overlapping files:

1. **Orphan branch / no common ancestor** — feature branch in UTS had no shared history with `origin/main`; `git rebase origin/main` produced add/add conflicts on every file
2. **Hardcoded LAN IP broke CI** — `/health` defaults changed to `192.168.254.103` (real LAN IP) in source code; broke `test_health_uses_plain_string_defaults` on all CI machines

---

## Version Registry

**Current version: `0.9.9.7`.** Do NOT bump without explicit user instruction.

All canonical locations that MUST be kept in sync:

| File | Field |
|------|-------|
| `pyproject.toml:7` | `version = "0.9.9.7"` |
| `bin/skills/SKILL.md:10` | `version: 0.9.9.7` |
| `bin/config/agent_registry.json:2` | `"version": "0.9.9.7"` |
| `portal_server.py:26` | `VERSION = "0.9.9.7"` |
| `bin/agents/*/agent.md:4` | `version: 0.9.9.7` |
| `CLAUDE.md` | `(v0.9.9.7)` |
| `docs/PERPLEXITY_BRIDGE.md:3` | `Version 0.9.9.7` |

---

## Multi-Agent Synchronization Protocol

1. **Read `docs/LESSONS.md` first** — mandatory on every session start
2. **Scope claim** — append `[IN PROGRESS: agent-name — file.py]` comment to LESSONS.md before touching files; remove when done
3. **Additive changes** — prefer appending over rewriting; no conflict risk when changes don't overlap
4. **Commit message as communication** — state which constants/APIs changed; this is the only async channel between agents sharing no session context
5. **Never hardcode ephemeral runtime values** — `127.0.0.1` as default in source code, real IP in `.env` only
6. **One canonical source per constant** — if two files both define the same IP string, they will diverge

---

## Orphan Branch Recovery

```bash
# Symptoms: git merge-base HEAD origin/main returns exit 1
# git rebase origin/main produces add/add conflicts on EVERY file

# Fix:
git fetch origin main
git reset --hard origin/main
# Then manually re-apply your 5-ish changed files from /tmp backup or git stash
```

**Prevention**: Always create feature branches from `origin/main`:
```bash
git checkout -b feature/xyz origin/main
```

---

## Rules

1. **Always branch from `origin/main`** — never from a detached HEAD or an agent-created branch
2. **Source code defaults must be loopback** — real IPs live in `.env` only
3. **One canonical source per constant** — if two files define the same value, they will diverge
4. **Test isolation requires `autouse` fixtures** that restore module-level state after `importlib.reload()`
5. **Commit body must name changed constants/APIs** — it's the only async communication channel between concurrent agents

---

## Pre-Commit Checklist (multi-agent sessions)

```bash
git fetch origin main
git log --oneline HEAD..origin/main          # changes by other agents
grep -rn "192\.168\." --include="*.py" | grep -v "test_\|\.env\|LESSONS"
python -m pytest -q
```

---

## Related

- [Session log 2026-04-12](../LESSONS.md#2026-04-12--claude--48-hour-multi-agent-sprint-collaboration-patterns--version-registry)
- Commit: `71a15f7` (PT) — fix(health): restore 127.0.0.1 loopback defaults
