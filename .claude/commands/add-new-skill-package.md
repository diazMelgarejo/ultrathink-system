---
name: add-new-skill-package
description: Workflow command scaffold for add-new-skill-package in ultrathink-system.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-new-skill-package

Use this workflow when working on **add-new-skill-package** in `ultrathink-system`.

## Goal

Creates a new, installable skill package for the Claude/Ultrathink system, including documentation, configuration, scripts, templates, and references.

## Common Files

- `skill-package/INSTALL.md`
- `skill-package/install.sh`
- `skill-package/ultrathink/SKILL.md`
- `skill-package/ultrathink/afrp/SKILL.md`
- `skill-package/ultrathink/cidf/SKILL.md`
- `skill-package/ultrathink/config/agent_registry.json`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create INSTALL.md and install.sh in skill-package/
- Add SKILL.md and submodule SKILL.md files (e.g., afrp/SKILL.md, cidf/SKILL.md)
- Add config files (agent_registry.json, routing_rules.json)
- Add reference documentation (e.g., amplifier-principle.md, content-insertion-framework.md, etc.)
- Add scripts (e.g., capture_lesson.py, create_task_plan.sh, verify_before_done.py)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.