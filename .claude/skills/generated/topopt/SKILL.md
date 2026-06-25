---
name: topopt
description: "Skill for the Topopt area of Lab-builder. 8 symbols across 3 files."
---

# Topopt

8 symbols | 3 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how run_topopt, parse_args, main work
- Modifying topopt-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/modules/topopt/fem_component.py` | _element_stiffness, _node_ids, _build_index_map, __init__ |
| `src/modules/topopt/run_optimization.py` | run_topopt, parse_args, main |
| `src/modules/thermo/coupling.py` | get_degraded_E |

## Entry Points

Start here when exploring this area:

- **`run_topopt`** (Function) — `src/modules/topopt/run_optimization.py:32`
- **`parse_args`** (Function) — `src/modules/topopt/run_optimization.py:168`
- **`main`** (Function) — `src/modules/topopt/run_optimization.py:181`
- **`get_degraded_E`** (Method) — `src/modules/thermo/coupling.py:15`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `run_topopt` | Function | `src/modules/topopt/run_optimization.py` | 32 |
| `parse_args` | Function | `src/modules/topopt/run_optimization.py` | 168 |
| `main` | Function | `src/modules/topopt/run_optimization.py` | 181 |
| `get_degraded_E` | Method | `src/modules/thermo/coupling.py` | 15 |
| `_element_stiffness` | Function | `src/modules/topopt/fem_component.py` | 20 |
| `_node_ids` | Function | `src/modules/topopt/fem_component.py` | 80 |
| `_build_index_map` | Function | `src/modules/topopt/fem_component.py` | 91 |
| `__init__` | Method | `src/modules/topopt/fem_component.py` | 119 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Get_degraded_E` | intra_community | 3 |

## How to Explore

1. `context({name: "run_topopt"})` — see callers and callees
2. `query({search_query: "topopt"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
