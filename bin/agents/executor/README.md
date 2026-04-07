# executor agent

Stage 4 — Masterful Execution: implements designs with TDD, up to 5 parallel.

## Usage

Spawned by the ultrathink orchestrator via OpenClaw gateway (127.0.0.1:18789)
or directly as a Claude Code subagent from `.claude/agents/`.

## Files

- `agent.md` — Agent identity, boundaries, and CIDF integration
- `SOUL.md` — OpenClaw identity file (if applicable)
- `*.py` — Tool implementations

## References

- Skill framework: `bin/skills/SKILL.md`
- CIDF: `bin/skills/cidf/FRAMEWORK.md`
- Config: `bin/config/agent_registry.json`
