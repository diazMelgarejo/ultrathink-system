# ultrathink-system — Claude Code Mandatory Rules

> This file is loaded by Claude Code at the start of every session.
> All rules below are **non-negotiable** for every agent (ECC, AutoResearcher, Claude).

---

## 1. Continuous Learning — Always On

Every session **must** use [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).

- **Read first**: Load `.claude/lessons/LESSONS.md` at session start — this is the shared knowledge base across all agents and sessions.
- **Write back**: Append meaningful discoveries, patterns, and decisions to `.claude/lessons/LESSONS.md` before ending a session.
- **Instinct path**: Repo instincts live at `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`.

## 2. ECC Post-Merge Workflow (Mandatory)

After **any** ECC Tools PR is merged into this repo, immediately run:

```bash
# 1. Pull latest
git pull origin main

# 2. Import instincts (run in Claude Code)
/instinct-import .claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml

# 3. Verify
/instinct-status

# 4. Commit any changes written by the import
git add -A && git commit -m "chore(ecc): post-merge instinct import sync"
git push origin main
```

Or use the `/ecc-sync` command (`.claude/commands/ecc-sync.md`).

## 3. Shared Lessons Path

The canonical lessons file is `.claude/lessons/LESSONS.md` — **same relative path in both PT and ultrathink-system**.

- ECC agents: read + write
- AutoResearcher agents: read + write
- Claude sessions: read at start, append before exit
- Auditable on GitHub at all times

## 4. AutoResearcher Integration

Primary mode: **uditgoenka/autoresearch Claude Code plugin** (runs anywhere).
Secondary mode: GPU runner via SSH for `ml-experiment` task types.

### Plugin install (one-time, idempotent)
```bash
claude plugin marketplace add uditgoenka/autoresearch
claude plugin install autoresearch@autoresearch
```

### Activation (per session)
```
/autoresearch          # research loop
/autoresearch:debug    # verbose reasoning trace
```

### Hardware guard — Windows sequential load rule
Never configure the system to load more than one model at a time on the
Windows GPU. Check `swarm_state.md` for `GPU: BUSY` before dispatching any
new experiment. This is enforced in the autoresearcher SOUL.md.

When running AutoResearcher swarms:
- Read `.claude/lessons/LESSONS.md` for prior experiment context
- Record new findings in `.claude/lessons/LESSONS.md` under a dated session entry
- Cross-reference Perplexity-Tools' `.claude/lessons/LESSONS.md` for joint context
- `AUTORESEARCH_REMOTE` env var selects the fork (default: uditgoenka/autoresearch)
- `AUTORESEARCH_BRANCH` env var selects the sync branch (default: main)

## 5. Mother Skill — Always Load

Before any significant change to this repo, load the mother skill:

```
/skill bin/skills/SKILL.md
```

- Run **AFRP gate** before generating non-trivial output
- Apply **CIDF `decide()`** before any content insertion
- Use **`@field_validator`** (Pydantic V2), never deprecated `@validator`
- Keep ultrathink API **stateless** (no Redis dependency)

## 6. Repository Identity

- **Role**: Multi-agent execution engine (Repo #2) — POST /ultrathink on port 8001
- **Companion repo**: [Perplexity-Tools](https://github.com/diazMelgarejo/Perplexity-Tools) (Repo #1, orchestrator)
- **Skill**: `.claude/skills/ultrathink-system/SKILL.md`
- **Mother skill**: `bin/skills/SKILL.md` (v0.9.9.7)

## 7. Harness Path Map

| Source | Runtime | Harness |
|--------|---------|---------|
| `bin/skills/SKILL.md` | `.claude/skills/ultrathink-system/SKILL.md` | Claude Code (project) |
| `bin/skills/SKILL.md` | `~/.claude/skills/ultrathink-system/` | Claude Code (global) |
| `bin/skills/SKILL.md` | `.agents/skills/ultrathink-system/SKILL.md` | Codex/OpenCode |
| `bin/agents/*/` | `.claude/agents/ultrathink-*.md` | Claude Code subagents |

> CIDF content (`bin/skills/cidf/`) is the canonical source. Install scripts copy it to
> `.claude/skills/ultrathink-system/cidf/` and `.agents/skills/ultrathink-system/cidf/`
> at runtime; checked idempotently on each run.
