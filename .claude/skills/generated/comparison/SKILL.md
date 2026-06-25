---
name: comparison
description: "Skill for the Comparison area of Lab-builder. 8 symbols across 2 files."
---

# Comparison

8 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `02-wind-energy/`
- Understanding how compare, report, register_comparison work
- Modifying comparison-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `02-wind-energy/comparison/turbine_comparison.py` | compare, report, register_comparison, main |
| `src/modules/wind_energy_v2/comparison/turbine_comparison.py` | compare, report, register_comparison, main |

## Entry Points

Start here when exploring this area:

- **`compare`** (Function) — `02-wind-energy/comparison/turbine_comparison.py:83`
- **`report`** (Function) — `02-wind-energy/comparison/turbine_comparison.py:113`
- **`register_comparison`** (Function) — `02-wind-energy/comparison/turbine_comparison.py:154`
- **`main`** (Function) — `02-wind-energy/comparison/turbine_comparison.py:201`
- **`compare`** (Function) — `src/modules/wind_energy_v2/comparison/turbine_comparison.py:83`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `compare` | Function | `02-wind-energy/comparison/turbine_comparison.py` | 83 |
| `report` | Function | `02-wind-energy/comparison/turbine_comparison.py` | 113 |
| `register_comparison` | Function | `02-wind-energy/comparison/turbine_comparison.py` | 154 |
| `main` | Function | `02-wind-energy/comparison/turbine_comparison.py` | 201 |
| `compare` | Function | `src/modules/wind_energy_v2/comparison/turbine_comparison.py` | 83 |
| `report` | Function | `src/modules/wind_energy_v2/comparison/turbine_comparison.py` | 113 |
| `register_comparison` | Function | `src/modules/wind_energy_v2/comparison/turbine_comparison.py` | 154 |
| `main` | Function | `src/modules/wind_energy_v2/comparison/turbine_comparison.py` | 201 |

## How to Explore

1. `context({name: "compare"})` — see callers and callees
2. `query({search_query: "comparison"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
