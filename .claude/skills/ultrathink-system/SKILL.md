```markdown
# ultrathink-system Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides guidance on contributing to the `ultrathink-system` Python codebase. It covers file naming conventions, import/export styles, commit patterns, and testing practices. The repository uses Python without a specific framework, and emphasizes clarity and consistency in its structure.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files and modules.
  - Example:  
    ```python
    # Correct
    my_module.py

    # Incorrect
    MyModule.py
    ```

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    # In file: utils/data_loader.py
    from .parser import parse_data
    ```

### Export Style
- Use **named exports** by defining `__all__` in modules.
  - Example:
    ```python
    # In utils/data_loader.py
    __all__ = ['load_data']

    def load_data(path):
        ...
    ```

### Commit Patterns
- Commits are mixed in type, with prefixes such as `release` and `chore`.
- Commit messages average 54 characters.
  - Example:
    ```
    chore: update dependencies for security patch
    release: v1.2.0 with new inference module
    ```

## Workflows

### Code Contribution
**Trigger:** When adding or updating code  
**Command:** `/contribute`

1. Create a new branch for your feature or fix.
2. Write code using snake_case file names and relative imports.
3. Update `__all__` for named exports in any new or modified modules.
4. Commit your changes using a descriptive message with a relevant prefix (`chore`, `release`, etc.).
5. Open a pull request for review.

### Testing
**Trigger:** When writing or updating tests  
**Command:** `/test`

1. Create test files using the pattern `*.test.ts` (TypeScript/Jest).
2. Write tests covering new or changed functionality.
3. Run the test suite to ensure all tests pass.
4. Address any test failures before committing.

## Testing Patterns

- **Framework:** Jest (with TypeScript)
- **File Pattern:** Test files are named with the `.test.ts` suffix.
  - Example:
    ```
    data_loader.test.ts
    ```
- **Test Example:**
    ```typescript
    // data_loader.test.ts
    import { loadData } from './data_loader';

    test('loads data correctly', () => {
      const data = loadData('test.csv');
      expect(data).toBeDefined();
    });
    ```

## Commands
| Command      | Purpose                                   |
|--------------|-------------------------------------------|
| /contribute  | Start the code contribution workflow      |
| /test        | Run or write tests for the codebase       |
```
