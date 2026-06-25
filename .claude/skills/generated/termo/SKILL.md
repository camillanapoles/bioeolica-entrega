---
name: termo
description: "Skill for the Termo area of Lab-builder. 12 symbols across 5 files."
---

# Termo

12 symbols | 5 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how parse_bc_string, parse_args, main work
- Modifying termo-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/modules/termo/solver.py` | _node_id, _build_connectivity, _hex8_conductivity_matrix, solve, compute_gradient (+2) |
| `src/modules/termo/materials.py` | _is_material_registered, register_materials |
| `src/modules/termo/bc.py` | parse_bc_string |
| `src/modules/termo/coupling.py` | thermal_to_structural_loads |
| `src/modules/termo/stress.py` | thermal_stress |

## Entry Points

Start here when exploring this area:

- **`parse_bc_string`** (Function) — `src/modules/termo/bc.py:26`
- **`parse_args`** (Function) — `src/modules/termo/solver.py:164`
- **`main`** (Function) — `src/modules/termo/solver.py:177`
- **`thermal_to_structural_loads`** (Function) — `src/modules/termo/coupling.py:12`
- **`thermal_stress`** (Function) — `src/modules/termo/stress.py:9`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `parse_bc_string` | Function | `src/modules/termo/bc.py` | 26 |
| `parse_args` | Function | `src/modules/termo/solver.py` | 164 |
| `main` | Function | `src/modules/termo/solver.py` | 177 |
| `thermal_to_structural_loads` | Function | `src/modules/termo/coupling.py` | 12 |
| `thermal_stress` | Function | `src/modules/termo/stress.py` | 9 |
| `register_materials` | Function | `src/modules/termo/materials.py` | 78 |
| `solve` | Method | `src/modules/termo/solver.py` | 85 |
| `compute_gradient` | Method | `src/modules/termo/solver.py` | 154 |
| `_is_material_registered` | Function | `src/modules/termo/materials.py` | 63 |
| `_node_id` | Method | `src/modules/termo/solver.py` | 44 |
| `_build_connectivity` | Method | `src/modules/termo/solver.py` | 48 |
| `_hex8_conductivity_matrix` | Method | `src/modules/termo/solver.py` | 69 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _node_id` | intra_community | 4 |
| `Main → _hex8_conductivity_matrix` | intra_community | 3 |
| `Compute_gradient → _node_id` | intra_community | 3 |

## How to Explore

1. `context({name: "parse_bc_string"})` — see callers and callees
2. `query({search_query: "termo"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
