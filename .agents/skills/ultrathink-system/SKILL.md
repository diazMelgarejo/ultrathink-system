```markdown
# ultrathink-system Development Patterns

> Auto-generated skill from repository analysis

## Overview

The `ultrathink-system` repository provides a modular framework for developing, packaging, and distributing "skills"—self-contained functional units—for the Claude/Ultrathink ecosystem. This codebase emphasizes maintainability, reusability, and multi-agent compatibility, with a focus on clear documentation, structured configuration, and repeatable workflows for skill creation and synchronization.

## Coding Conventions

### File Naming

- Use **camelCase** for Python files and scripts.
  - Example: `captureLesson.py`, `verifyBeforeDone.py`

### Import Style

- Use **relative imports** within modules.
  - Example:
    ```python
    from .utils import parseConfig
    ```

### Export Style

- Use **named exports** (explicitly listing what is exported).
  - Example:
    ```python
    def createTaskPlan(...):
        ...

    __all__ = ["createTaskPlan"]
    ```

### Commit Patterns

- Commit messages are **mixed type**, commonly using prefixes like `feat` and `refactor`.
- Average commit message length: ~74 characters.
  - Example:  
    ```
    feat: add captureLesson.py script for lesson logging automation
    refactor: unify config loading across skill modules
    ```

## Workflows

### Add New Skill Package

**Trigger:** When you want to add or distill a new Claude skill as a self-contained, installable package.  
**Command:** `/new-skill-package`

1. **Create installation files** in `skill-package/`:
    - `INSTALL.md` (instructions)
    - `install.sh` (setup script)
2. **Add documentation**:
    - `SKILL.md` in the main and submodule directories (e.g., `afrp/SKILL.md`, `cidf/SKILL.md`)
3. **Add configuration files**:
    - `config/agent_registry.json`
    - `config/routing_rules.json`
4. **Add reference documentation**:
    - Place supporting docs in `references/` (e.g., `amplifier-principle.md`)
5. **Add scripts**:
    - Place scripts in `scripts/` (e.g., `captureLesson.py`, `verifyBeforeDone.py`)
6. **Add templates**:
    - Place templates in `templates/` (e.g., `lessons-log.md`, `task-plan.md`)
7. Review and commit your changes with a descriptive message.

**Example Directory Structure:**
```
skill-package/
  INSTALL.md
  install.sh
  ultrathink/
    SKILL.md
    afrp/
      SKILL.md
    cidf/
      SKILL.md
    config/
      agent_registry.json
      routing_rules.json
    references/
      amplifier-principle.md
    scripts/
      captureLesson.py
    templates/
      lessons-log.md
```

---

### Sync Skill Package to Multi-Location

**Trigger:** When you want to propagate or refactor a skill package across multiple agent/skill locations, or deduplicate content.  
**Command:** `/sync-skill-package`

1. **Copy or merge** the following into each target directory:
    - `SKILL.md`
    - `config/`
    - `references/`
    - `scripts/`
    - `templates/`
2. **Target directories** include:
    - `.agents/skills/ultrathink-system/`
    - `.claude/skills/ultrathink-system-skill/`
    - `.claude/skills/ultrathink-system/`
    - `single_agent/`
    - `multi_agent/`
3. **Unify or deduplicate install scripts**:
    - Ensure only one version of `install.sh`, `install-single-agent.sh` as needed.
4. **Update or add supporting files**:
    - `README.md`, `DESIGN.md`, etc. in each location.
5. **Verify** all config and reference files are present and up-to-date in each agent/skill directory.
6. Commit with a message like:
    ```
    refactor: sync ultrathink-system skill package across agent directories
    ```

---

## Testing Patterns

- **Framework:** Jest (JavaScript/TypeScript)
- **Test file pattern:** `*.test.ts`
- **Location:** Place test files alongside or near the code they test.
- **Example:**
    ```typescript
    // captureLesson.test.ts
    import { captureLesson } from './captureLesson'

    test('should capture lesson log', () => {
      // ...test logic...
    })
    ```

## Commands

| Command              | Purpose                                                        |
|----------------------|----------------------------------------------------------------|
| /new-skill-package   | Scaffold a new Claude/Ultrathink skill package with docs, config, scripts, and templates. |
| /sync-skill-package  | Propagate or deduplicate a skill package across multi-agent directories.                   |

```