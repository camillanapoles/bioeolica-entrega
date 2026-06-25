---
name: crslr
description: "Skill for the Crslr area of Lab-builder. 9 symbols across 3 files."
---

# Crslr

9 symbols | 3 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how create_report, add_uncertainty, add_m9_compliance work
- Modifying crslr-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/modules/crslr/engine.py` | create_report, add_uncertainty, add_m9_compliance, render_report, parse_args (+1) |
| `src/modules/crslr/render.py` | render_pdf, render_markdown_to_pdf |
| `src/modules/crslr/schema.py` | load_and_validate |

## Entry Points

Start here when exploring this area:

- **`create_report`** (Function) — `src/modules/crslr/engine.py:21`
- **`add_uncertainty`** (Function) — `src/modules/crslr/engine.py:51`
- **`add_m9_compliance`** (Function) — `src/modules/crslr/engine.py:63`
- **`render_report`** (Function) — `src/modules/crslr/engine.py:73`
- **`parse_args`** (Function) — `src/modules/crslr/engine.py:90`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_report` | Function | `src/modules/crslr/engine.py` | 21 |
| `add_uncertainty` | Function | `src/modules/crslr/engine.py` | 51 |
| `add_m9_compliance` | Function | `src/modules/crslr/engine.py` | 63 |
| `render_report` | Function | `src/modules/crslr/engine.py` | 73 |
| `parse_args` | Function | `src/modules/crslr/engine.py` | 90 |
| `main` | Function | `src/modules/crslr/engine.py` | 103 |
| `render_pdf` | Function | `src/modules/crslr/render.py` | 9 |
| `render_markdown_to_pdf` | Function | `src/modules/crslr/render.py` | 31 |
| `load_and_validate` | Function | `src/modules/crslr/schema.py` | 32 |

## How to Explore

1. `context({name: "create_report"})` — see callers and callees
2. `query({search_query: "crslr"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
