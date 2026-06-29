```markdown
# bioeolica-entrega Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `bioeolica-entrega` Python repository. You'll learn how to structure code, write and organize commits, follow naming conventions, and understand the project's approach to testing and workflows. While no external frameworks are detected, the repository enforces clear, maintainable standards for collaborative Python development.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python file names.
  - Example: `data_processor.py`, `wind_analysis.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import calculate_power
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['calculate_power', 'WindTurbine']
    ```

### Commit Messages
- Follow **conventional commit** style.
- Allowed prefixes: `fix`, `feat`
- Keep commit messages concise (average ~70 characters).
  - Example:
    ```
    feat: add wind speed normalization function
    fix: correct power output calculation in turbine module
    ```

## Workflows

### Code Contribution
**Trigger:** When adding new features or fixing bugs  
**Command:** `/contribute`

1. Create a new branch for your feature or fix.
2. Write code following the coding conventions.
3. Use relative imports and snake_case file names.
4. Add or update tests as needed.
5. Commit changes using conventional commit messages (e.g., `feat: ...`, `fix: ...`).
6. Push your branch and open a pull request.

### Code Review
**Trigger:** When reviewing a pull request  
**Command:** `/review`

1. Check that file names use snake_case.
2. Ensure imports are relative.
3. Verify that exports are named and explicit.
4. Confirm commit messages follow the conventional pattern.
5. Run tests to ensure correctness.
6. Leave feedback or approve the pull request.

## Testing Patterns

- **Framework:** Unknown (no standard framework detected)
- **Test File Pattern:** Files are named with the `*.test.ts` pattern (note: this suggests possible TypeScript tests, but the main codebase is Python).
- **Best Practice:** Place test files alongside the code they test or in a dedicated `tests/` directory. Use descriptive names.

  Example test file:
  ```
  wind_analysis.test.ts
  ```

## Commands
| Command      | Purpose                                      |
|--------------|----------------------------------------------|
| /contribute  | Start the code contribution workflow         |
| /review      | Begin the code review workflow               |
```
