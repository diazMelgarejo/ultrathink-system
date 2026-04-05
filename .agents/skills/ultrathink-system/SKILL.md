```markdown
# ultrathink-system Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the `ultrathink-system` Python codebase. You'll learn how to structure files, write imports/exports, follow commit message guidelines, and organize tests. These patterns help maintain code clarity, consistency, and collaboration across the project.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `dataProcessor.py`, `userManager.py`

### Import Style
- Use **relative imports** within the project.
  - Example:
    ```python
    from .utils import parseData
    from ..models.user import User
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['UserManager', 'processInput']
    ```

### Commit Messages
- Follow **conventional commit** format.
- Use the `feat` prefix for new features.
- Keep commit messages concise (average 74 characters).
  - Example:
    ```
    feat: add user authentication to login flow
    ```

## Workflows

### Feature Development
**Trigger:** When adding a new feature to the codebase  
**Command:** `/feature-development`

1. Create a new branch for your feature.
2. Use camelCase for new file names.
3. Use relative imports for any internal modules.
4. Explicitly define exports with `__all__`.
5. Write a commit message starting with `feat:`.
6. Open a pull request for review.

### Testing
**Trigger:** When writing or running tests  
**Command:** `/run-tests`

1. Place test files alongside source files, using the pattern `*.test.*`.
   - Example: `dataProcessor.test.py`
2. Use the project's preferred (unknown) testing framework.
3. Run tests before committing code.

## Testing Patterns

- Test files are named using the pattern: `*.test.*`
  - Example: `userManager.test.py`
- Place test files near the code they test.
- The specific testing framework is not detected; follow existing test file patterns.

## Commands
| Command              | Purpose                                   |
|----------------------|-------------------------------------------|
| /feature-development | Start a new feature with proper conventions|
| /run-tests           | Run all tests in the codebase             |
```
