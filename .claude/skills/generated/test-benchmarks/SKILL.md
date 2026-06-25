---
name: test-benchmarks
description: "Skill for the Test_benchmarks area of Lab-builder. 20 symbols across 3 files."
---

# Test_benchmarks

20 symbols | 3 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how dynamic_pressure, cp_rectangular_windward, cp_rectangular_leeward work
- Modifying test_benchmarks-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/tests/test_benchmarks/test_wind_pressure.py` | dynamic_pressure, cp_rectangular_windward, cp_rectangular_leeward, test_dynamic_pressure, test_cp_rectangular_windward (+7) |
| `src/tests/test_benchmarks/test_cantilever_beam.py` | analytical_cantilever, test_cantilever_analytical_value, test_cantilever_beam_scale_invariance, test_cantilever_linearity |
| `src/tests/test_benchmarks/test_plate_hole_kt.py` | analytical_kirsch_stress, test_kirsch_exact_at_hole_boundary, test_kirsch_decay_with_distance, test_kirsch_hoop_stress_vs_angle |

## Entry Points

Start here when exploring this area:

- **`dynamic_pressure`** (Function) — `src/tests/test_benchmarks/test_wind_pressure.py:14`
- **`cp_rectangular_windward`** (Function) — `src/tests/test_benchmarks/test_wind_pressure.py:19`
- **`cp_rectangular_leeward`** (Function) — `src/tests/test_benchmarks/test_wind_pressure.py:24`
- **`test_dynamic_pressure`** (Function) — `src/tests/test_benchmarks/test_wind_pressure.py:54`
- **`test_cp_rectangular_windward`** (Function) — `src/tests/test_benchmarks/test_wind_pressure.py:60`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `dynamic_pressure` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 14 |
| `cp_rectangular_windward` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 19 |
| `cp_rectangular_leeward` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 24 |
| `test_dynamic_pressure` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 54 |
| `test_cp_rectangular_windward` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 60 |
| `test_cp_rectangular_leeward` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 72 |
| `test_wind_force_calculation` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 84 |
| `test_nbr6123_coherence` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 110 |
| `analytical_cantilever` | Function | `src/tests/test_benchmarks/test_cantilever_beam.py` | 18 |
| `test_cantilever_analytical_value` | Function | `src/tests/test_benchmarks/test_cantilever_beam.py` | 35 |
| `test_cantilever_beam_scale_invariance` | Function | `src/tests/test_benchmarks/test_cantilever_beam.py` | 62 |
| `test_cantilever_linearity` | Function | `src/tests/test_benchmarks/test_cantilever_beam.py` | 70 |
| `analytical_kirsch_stress` | Function | `src/tests/test_benchmarks/test_plate_hole_kt.py` | 19 |
| `test_kirsch_exact_at_hole_boundary` | Function | `src/tests/test_benchmarks/test_plate_hole_kt.py` | 52 |
| `test_kirsch_decay_with_distance` | Function | `src/tests/test_benchmarks/test_plate_hole_kt.py` | 66 |
| `test_kirsch_hoop_stress_vs_angle` | Function | `src/tests/test_benchmarks/test_plate_hole_kt.py` | 81 |
| `cp_rectangular_sidewall` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 34 |
| `test_cp_sidewall` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 79 |
| `cp_cylindrical` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 39 |
| `test_cylindrical_cp_reynolds_dependence` | Function | `src/tests/test_benchmarks/test_wind_pressure.py` | 98 |

## How to Explore

1. `context({name: "dynamic_pressure"})` — see callers and callees
2. `query({search_query: "test_benchmarks"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
