## v0.9.9.1 — Harness Alignment, AFRP Gate, CIDF Sub-Skill, api_server, ECC Bundle

**Tests**: 116 passed, 0 failed | **Files**: 329 | **Reviewer**: manual review before merge

### New Files
- `.claude/skills/ultrathink-system/SKILL.md` — ECC-generated conventions skill
- `.claude/commands/ecc-sync.md` + `feature-development.md`
- `.claude/ecc-tools.json`, `.claude/identity.json`, `.claude/lessons/LESSONS.md`
- `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`
- `.codex/config.toml` + `AGENTS.md` + `agents/*.toml`
- `.github/workflows/ci.yml`
- `.claude/agents/ultrathink-*.md` (Claude Code native subagent runtime path)

### Updated
- `CLAUDE.md` — continuous-learning, AFRP gate, stateless API, companion repo refs
- `single_agent/SKILL.md` — version 0.9.9.1, AFRP gate as first router step
- `CHANGELOG.md` — v0.9.9.1 entry

### Checklist
- [x] 116/116 tests passing
- [x] verify-package.sh passes
- [x] ECC bundle committed
- [x] Clean rebase (linear history) — Do not squash
Ultrathink system v0.9.9.1