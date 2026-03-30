---
name: ultrathink-system-conventions
description: Development conventions and patterns for ultrathink-system. Python multi-agent system with conventional commits and ultrathink 5-stage methodology.
---

# Ultrathink System Conventions

> Generated from [diazMelgarejo/ultrathink-system](https://github.com/diazMelgarejo/ultrathink-system) on 2026-03-29
> Mother skill: [`single_agent/SKILL.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/SKILL.md) (v0.9.8.0)

## Overview

This skill teaches Claude the development patterns and conventions used in ultrathink-system — a Python multi-agent system implementing the ultrathink 5-stage methodology with an AFRP pre-router gate, CIDF v1.2 content insertion framework, and a 7-agent execution network.

## Mother Skill

The canonical system skill lives at `single_agent/SKILL.md` (v0.9.8.0). Always load it when working on this repository for the full ultrathink methodology, AFRP gate, CIDF rules, and 6 directives.

Sub-skills (load on demand):
- `single_agent/afrp/SKILL.md` — Audience-First Response Protocol (mandatory pre-router gate)
- `single_agent/cidf/SKILL.md` — Content Insertion Decision Framework v1.2

## Tech Stack

- **Primary Language**: Python
- **Architecture**: dual-module (`single_agent/` + `multi_agent/`), API server (`api_server.py`)
- **Package Manager**: uv / hatchling
- **Validation**: Pydantic V2 (`@field_validator`)
- **Test Location**: `tests/`

## When to Use This Skill

Activate this skill when:
- Making changes to this repository
- Adding new features following established patterns
- Writing tests that match project conventions
- Creating commits with proper message format

## Commit Conventions

Follow these commit message conventions based on 51 analyzed commits.

### Commit Style: Conventional Commits (scoped)

### Prefixes Used

- `feat` — new features
- `fix` — bug fixes
- `refactor` — code restructuring
- `docs` — documentation only
- `sec` — security hardening
- `chore` — maintenance (deps, config)
- `arch` — architectural decisions
- `release` — version bumps

### Message Guidelines

- Average message length: ~50 characters
- Keep first line concise and descriptive
- Use imperative mood ("Add feature" not "Added feature")
- Include scope when relevant: `fix(api_server): ...`, `feat(afrp): ...`, `docs(v0.9.x.0): ...`
- Bare messages acceptable for simple one-line changes


*Commit message example*

```text
feat(api): add model_hint field to UltraThinkRequest (ADR-001, v0.9.9.0)
```

*Commit message example*

```text
sec(api_server): v0.9.8.0 security hardening - rate limiting, input validation, IP leak fix, timeout bounds
```

*Commit message example*

```text
fix(api_server): migrate task_description validator to Pydantic V2
```

*Commit message example*

```text
arch: enforce stateless ultrathink, defer Redis to PT-only v1.1+
```

*Commit message example*

```text
feat(afrp): add Audience-First Response Protocol as pre-router gate
```

*Commit message example*

```text
docs(v0.9.4.0): Add Perplexity-Tools integration bridge documentation
```

*Commit message example*

```text
refactor: rename packages to valid Python identifiers & v0.9.4.1 release
```

*Commit message example*

```text
fix(verify-package): correct install script filenames to use dashes
```

## Architecture

### Project Structure

```
ultrathink-system/
├── single_agent/          ← ultrathink single-agent methodology
│   ├── SKILL.md           ← master skill (mother skill, v0.9.8.0)
│   ├── afrp/              ← AFRP sub-skill (mandatory pre-router gate)
│   ├── cidf/              ← CIDF v1.2 sub-skill (content insertion)
│   ├── references/        ← foundational essays
│   ├── scripts/           ← task management scripts
│   └── templates/         ← task templates
├── multi_agent/           ← 7-agent execution network
│   ├── agents/            ← per-agent definitions
│   ├── config/            ← agent_registry.json, routing_rules.json
│   ├── mcp_servers/       ← ultrathink_orchestration_server.py
│   └── shared/            ← shared utilities
├── api_server.py          ← POST /ultrathink endpoint (port 8001)
├── tests/                 ← pytest test suite
├── .github/workflows/     ← ci.yml, release.yml, test.yml
└── docs/                  ← PERPLEXITY_BRIDGE.md, SYNC_ANALYSIS.md
```

### Configuration Files

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/test.yml`
- `multi_agent/config/agent_registry.json`
- `multi_agent/config/routing_rules.json`

### Guidelines

- This project uses dual-module organization (`single_agent/` + `multi_agent/`)
- The API server (`api_server.py`) exposes `POST /ultrathink` on port 8001
- ultrathink is stateless — no Redis dependency; durable state owned by Perplexity-Tools
- Follow CIDF `decide()` before any content insertion

## Code Style

### Language: Python

### Naming Conventions

| Element | Convention |
|---------|------------|
| Files | snake_case |
| Functions | snake_case |
| Classes | PascalCase |
| Constants | SCREAMING_SNAKE_CASE |

### Import Style: Relative Imports (within packages)

### Validation: Pydantic V2 — use `@field_validator`, not `@validator`


*Preferred import style*

```python
# Use relative imports within packages
from .core.content_insertion_framework import Task, Env, decide
from ..shared.utils import load_config
```

## Common Workflows

These workflows were detected from analyzing commit patterns.

### Feature Development

Standard feature implementation workflow following the ultrathink 5-stage process.

**Frequency**: ~12 times per month

**Steps**:
1. Load `single_agent/SKILL.md` for full methodology context
2. Run AFRP gate (classify query, scope declaration)
3. Add feature implementation
4. Add/update tests in `tests/`
5. Update documentation and `CHANGELOG.md`
6. Verify with `scripts/verify_before_done.py`

**Files typically involved**:
- `single_agent/**/*.py`, `multi_agent/**/*.py`
- `tests/*.py`
- `CHANGELOG.md`, `docs/`

**Example commit sequence**:
```
feat(afrp): add Audience-First Response Protocol as pre-router gate
feat(skill): bump to v0.9.8.0, add PT hardware/SKILL.md cross-link
docs(sync): mark all P2 OPT items RESOLVED in SYNC_ANALYSIS.md
```

### Security Hardening

**Steps**:
1. Identify vulnerability (input validation, timeouts, IP handling)
2. Apply fix with Pydantic V2 validators
3. Update version and `CHANGELOG.md`
4. Commit with `sec(component): ...` prefix

## Best Practices

Based on analysis of the codebase, follow these practices:

### Do

- Load `single_agent/SKILL.md` before any significant change to this repo
- Run AFRP gate before generating non-trivial output
- Use CIDF `decide()` before any content insertion (all modes, no exceptions)
- Write `tasks/todo.md` before implementing tasks with 3+ steps
- Use `@field_validator` (Pydantic V2), not deprecated `@validator`
- Keep ultrathink API stateless (no Redis dependency)
- Verify programmatically — never trust visual confirmation alone
- Use snake_case for file names

### Don't

- Don't skip the AFRP gate for complex or audience-dependent queries
- Don't hardcode secrets or credentials
- Don't mark tasks complete without running `scripts/verify_before_done.py`
- Don't deviate from established patterns without discussion

---

*This skill was auto-generated by [ECC Tools](https://ecc.tools). Review and customize as needed for your team.*
