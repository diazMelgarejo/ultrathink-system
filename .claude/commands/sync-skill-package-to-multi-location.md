---
name: sync-skill-package-to-multi-location
description: Workflow command scaffold for sync-skill-package-to-multi-location in ultrathink-system.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /sync-skill-package-to-multi-location

Use this workflow when working on **sync-skill-package-to-multi-location** in `ultrathink-system`.

## Goal

Copies or merges a skill package's contents into multiple agent/skill directories (e.g., .agents/skills, .claude/skills, single_agent/, multi_agent/), deduplicating and unifying install/config/scripts/templates.

## Common Files

- `.agents/skills/ultrathink-system/*`
- `.claude/skills/ultrathink-system-skill/*`
- `.claude/skills/ultrathink-system/*`
- `single_agent/*`
- `multi_agent/*`
- `skill-package/ultrathink/*`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Copy or merge SKILL.md, config, references, scripts, and templates into .agents/skills/ultrathink-system/, .claude/skills/ultrathink-system-skill/, single_agent/, and multi_agent/ directories
- Unify or deduplicate install scripts (install.sh, install-single-agent.sh)
- Update or add supporting files (README.md, DESIGN.md, etc.) in each location
- Ensure all config and reference files are present in each agent/skill directory

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.