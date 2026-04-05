---
name: feature-development
description: Workflow command scaffold for feature-development in ultrathink-system.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-development

Use this workflow when working on **feature-development** in `ultrathink-system`.

## Goal

Standard feature implementation workflow following the ultrathink 5-stage methodology.

## Mother Skill

Always load `single_agent/SKILL.md` (v0.9.9.1) first for the full ultrathink methodology, AFRP gate, CIDF rules, and 6 directives.

## Common Files

- `single_agent/**/*.py`, `multi_agent/**/*.py`
- `tests/*.py`
- `CHANGELOG.md`, `docs/`

## Suggested Sequence

1. Load `single_agent/SKILL.md` — understand the ultrathink methodology before editing.
2. Run AFRP gate — classify query (A/B/C/D), declare scope, calibrate abstraction level.
3. Make the smallest coherent change that satisfies the workflow goal.
4. Use CIDF `decide()` before any content insertion.
5. Run the most relevant verification: `python scripts/verify_before_done.py`
6. Summarize what changed and what still needs review.

## Typical Commit Signals

- `feat(component): Add feature implementation`
- `fix(component): Fix edge case in feature`
- `docs(component): Update documentation for feature`

## Commit Style

Use conventional commits with scope: `feat(x):`, `fix(x):`, `sec(x):`, `docs(x):`, `arch:`, `chore(x):`

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Write `tasks/todo.md` before implementing any task with 3+ steps.
- Never mark complete without running `scripts/verify_before_done.py`.
- Update the command if the workflow evolves materially.
