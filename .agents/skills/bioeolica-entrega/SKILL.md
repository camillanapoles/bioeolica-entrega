```markdown
# bioeolica-entrega Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill introduces the core development patterns and workflows used in the `bioeolica-entrega` TypeScript codebase. It covers coding conventions, file organization, commit practices, and the process for adding new ECC bundles (skills) to the system. This guide is intended to help contributors maintain consistency and efficiency when working on the project.

## Coding Conventions

### File Naming

- Use **camelCase** for file names.
  - Example: `windFarmModel.ts`, `energyOutputCalculator.ts`

### Import Style

- Use **relative imports** for modules within the project.
  - Example:
    ```typescript
    import { calculateEnergy } from './energyOutputCalculator';
    ```

### Export Style

- Use **named exports** to expose functions, classes, or constants.
  - Example:
    ```typescript
    // In windFarmModel.ts
    export function createWindFarm() { ... }
    export const DEFAULT_TURBINE_COUNT = 10;
    ```

### Commit Messages

- Follow **Conventional Commits** with the `feat` prefix for features.
  - Example:
    ```
    feat: add wind speed normalization utility
    ```

## Workflows

### Add ECC Bundle

**Trigger:** When introducing a new skill or capability as an ECC bundle to the system.  
**Command:** `/add-ecc-bundle`

1. **Register the ECC bundle:**
   - Edit or create `.claude/ecc-tools.json` to include the new bundle.
2. **Document the skill:**
   - Add or update `.claude/skills/<skill-name>/SKILL.md` for Claude skill documentation.
   - Add or update `.agents/skills/<skill-name>/SKILL.md` for agent skill documentation.
3. **Configure the agent:**
   - Add or update `.agents/skills/<skill-name>/agents/openai.yaml` for agent configuration.
4. **Update identity information:**
   - Edit `.claude/identity.json` as needed.
5. **Configure Codex:**
   - Update `.codex/config.toml` for Codex configuration.
6. **Document agents:**
   - Edit `.codex/AGENTS.md` to include new or updated agents.
   - Update or add `.codex/agents/<agent>.toml` for each relevant agent (e.g., `explorer`, `reviewer`, `docs-researcher`).
7. **Define instincts:**
   - Add or update `.claude/homunculus/instincts/inherited/<skill>-instincts.yaml` for skill-specific instincts.

**Example Directory Structure:**
```
.claude/
  ecc-tools.json
  skills/
    mySkill/
      SKILL.md
  identity.json
  homunculus/
    instincts/
      inherited/
        mySkill-instincts.yaml
.agents/
  skills/
    mySkill/
      SKILL.md
      agents/
        openai.yaml
.codex/
  config.toml
  AGENTS.md
  agents/
    explorer.toml
    reviewer.toml
    docs-researcher.toml
```

## Testing Patterns

- Test files use the pattern `*.test.*` (e.g., `energyOutputCalculator.test.ts`).
- The specific testing framework is not specified, but tests are colocated with source files or in dedicated test directories.
- Example test file:
  ```typescript
  // energyOutputCalculator.test.ts
  import { calculateEnergy } from './energyOutputCalculator';

  describe('calculateEnergy', () => {
    it('should return correct output for standard input', () => {
      expect(calculateEnergy(10, 5)).toBe(50);
    });
  });
  ```

## Commands

| Command           | Purpose                                                      |
|-------------------|--------------------------------------------------------------|
| /add-ecc-bundle   | Add a new ECC bundle (skill) with configuration and docs     |

```