---
name: feature-development
description: Workflow command scaffold for feature-development in ultrathink-system.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-development

Use this when working on **feature-development** in `ultrathink-system`.

## Mother Skill

Always load `single_agent/SKILL.md` (v0.9.9.2) first for the full ultrathink methodology, AFRP gate, CIDF rules, and 6 directives.

## Common Files

## Steps

1. Load `single_agent/SKILL.md` — understand ultrathink before editing.
2. Run AFRP gate — classify query (A/B/C/D), declare scope.
3. Make smallest coherent change satisfying the goal.
4. Use CIDF `decide()` before any content insertion.
5. Verify: `python single_agent/scripts/verify_before_done.py`
6. Summarize changes and open review items.

## Commit Style

`feat(x):`, `fix(x):`, `sec(x):`, `docs(x):`, `arch:`, `chore(x):`

## Notes

- Write `tasks/todo.md` before any 3+ step task.
- Never mark complete without running verify script.
