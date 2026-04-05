# ultrathink-system — Claude Code Mandatory Rules

> Loaded by Claude Code at the start of every session.
> All rules below are **non-negotiable** for every agent (ECC, AutoResearcher, Claude).

---

## 1. Continuous Learning — Always On

Every session **must** use [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).

- **Read first**: Load `.claude/lessons/LESSONS.md` at session start.
- **Write back**: Append meaningful discoveries to `.claude/lessons/LESSONS.md` before ending.
- **Instinct path**: `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`

## 2. ECC Post-Merge Workflow (Mandatory)

After **any** ECC Tools PR is merged:

```bash
git pull origin main
/instinct-import .claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml
/instinct-status
git add -A && git commit -m "chore(ecc): post-merge instinct import sync"
git push origin main
```

Or use `/ecc-sync` (`.claude/commands/ecc-sync.md`).

## 3. Shared Lessons Path

Canonical path: `.claude/lessons/LESSONS.md` — same relative path in PT and ultrathink-system.
Readable + writable by ECC agents, AutoResearcher agents, and Claude sessions.

## 4. Mother Skill — Always Load

Before any significant change:

```
/skill single_agent/SKILL.md
```

- Run **AFRP gate** (`single_agent/afrp/SKILL.md`) before non-trivial output
- Apply **CIDF `decide()`** before any content insertion
- Use **`@field_validator`** (Pydantic V2), never deprecated `@validator`
- Keep ultrathink API **stateless** (no Redis dependency)

## 5. Repository Identity

- **Role**: Multi-agent execution engine (Repo #2) — `POST /ultrathink` on port 8001
- **Companion repo**: [Perplexity-Tools](https://github.com/diazMelgarejo/Perplexity-Tools) (Repo #1)
- **ECC skill**: `.claude/skills/ultrathink-system/SKILL.md`
- **Mother skill**: `single_agent/SKILL.md` (v0.9.9.1)

## 6. Harness Path Map

| Source | Runtime | Harness |
|--------|---------|---------|
| `single_agent/SKILL.md` | `.claude/skills/ultrathink-system/SKILL.md` | Claude Code (project) |
| `single_agent/SKILL.md` | `~/.claude/skills/ultrathink-system-skill/` | Claude Code (global) |
| `single_agent/SKILL.md` | `.agents/skills/ultrathink-system/SKILL.md` | Codex/OpenCode |
| `multi_agent/agents/*/` | `.claude/agents/ultrathink-*.md` | Claude Code subagents |
