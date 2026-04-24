# context agent

Stage 1 — Context Immersion: scans codebase, git history, and lessons.

## Usage

Spawned by the ultrathink orchestrator via OpenClaw gateway (127.0.0.1:18789)
or directly as a Claude Code subagent from `.claude/agents/`.

## Files

- `agent.md` — Agent identity, boundaries, and CIDF integration
- `SOUL.md` — OpenClaw identity file (if applicable)
- `*.py` — Tool implementations

## References

- Skill framework: `bin/orama-system/SKILL.md`
- CIDF: `bin/orama-system/cidf/FRAMEWORK.md`
- Config: `bin/config/agent_registry.json`
