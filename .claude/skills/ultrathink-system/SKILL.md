```markdown
# ultrathink-system Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `ultrathink-system` Python codebase. It covers file organization, code style, commit message standards, import/export practices, and testing patterns. By following these guidelines, contributors can ensure consistency, readability, and maintainability across the project.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `data_processor.py`, `user_profile_manager.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import calculate_score
    from ..models import User
    ```

### Export Style
- Use **named exports** (explicitly listing what is exported).
  - Example:
    ```python
    __all__ = ['process_data', 'DataModel']
    ```

### Commit Messages
- Follow the **Conventional Commits** specification.
- Use prefixes such as `docs:` for documentation changes.
- Keep commit messages concise (average 78 characters).
  - Example:
    ```
    docs: update README with new installation instructions
    ```

## Workflows

### Documentation Updates
**Trigger:** When updating or adding documentation files.
**Command:** `/update-docs`

1. Make changes to documentation files (e.g., `README.md`, `CONTRIBUTING.md`).
2. Stage your changes:
    ```
    git add README.md
    ```
3. Commit using the `docs:` prefix:
    ```
    git commit -m "docs: improve installation section in README"
    ```
4. Push your changes:
    ```
    git push origin <branch>
    ```

## Testing Patterns

- Test files follow the `*.test.*` naming pattern.
  - Example: `user_service.test.py`
- The specific testing framework is **unknown**, but standard Python testing practices apply.
- Place test files alongside the modules they test or in a dedicated `tests/` directory.
- Example test file structure:
    ```python
    # user_service.test.py

    from .user_service import get_user

    def test_get_user_returns_valid_user():
        user = get_user(1)
        assert user.name == "Alice"
    ```

## Commands
| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| /update-docs   | Standardize and commit documentation changes |
```
