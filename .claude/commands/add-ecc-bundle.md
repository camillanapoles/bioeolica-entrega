---
name: add-ecc-bundle
description: Workflow command scaffold for add-ecc-bundle in bioeolica-entrega.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-ecc-bundle

Use this workflow when working on **add-ecc-bundle** in `bioeolica-entrega`.

## Goal

Adds a new ECC bundle for a skill, including configuration, agent definitions, skill documentation, and instincts.

## Common Files

- `.claude/ecc-tools.json`
- `.claude/skills/<skill-name>/SKILL.md`
- `.agents/skills/<skill-name>/SKILL.md`
- `.agents/skills/<skill-name>/agents/openai.yaml`
- `.claude/identity.json`
- `.codex/config.toml`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update .claude/ecc-tools.json to register the ECC bundle.
- Add or update .claude/skills/<skill-name>/SKILL.md for Claude skill documentation.
- Add or update .agents/skills/<skill-name>/SKILL.md for agent skill documentation.
- Add or update .agents/skills/<skill-name>/agents/openai.yaml for agent configuration.
- Add or update .claude/identity.json for identity information.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.