---
name: structural
description: "Skill for the Structural area of Lab-builder. 80 symbols across 10 files."
---

# Structural

80 symbols | 10 files | Cohesion: 92%

## When to Use

- Working with code in `02-wind-energy/`
- Understanding how estimate_stress, compute_safety_factors, find_blade_design_id work
- Modifying structural-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `02-wind-energy/structural/blade_geometry.py` | naca_0018_coordinates, thickness_y, __post_init__, _generate_stations, get_station (+6) |
| `src/modules/wind_energy_v2/structural/blade_geometry.py` | naca_0018_coordinates, thickness_y, __post_init__, _generate_stations, get_station (+6) |
| `02-wind-energy/structural/fatigue_analysis.py` | cdf, steady_stress_at_wind, turb_std_dev, alternating_stress_at_wind, _debug_self_check (+5) |
| `src/modules/wind_energy_v2/structural/fatigue_analysis.py` | cdf, steady_stress_at_wind, turb_std_dev, alternating_stress_at_wind, _debug_self_check (+5) |
| `02-wind-energy/structural/verify_safety_factors.py` | estimate_stress, summary, compute_safety_factors, find_blade_design_id, _register_beam_model (+4) |
| `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | estimate_stress, summary, compute_safety_factors, find_blade_design_id, _register_beam_model (+4) |
| `02-wind-energy/structural/blade_cost_estimate.py` | chord_at, _integrate_blade_mass, summary, estimate_blade_cost, estimate_rotor_cost (+1) |
| `src/modules/wind_energy_v2/structural/blade_cost_estimate.py` | chord_at, _integrate_blade_mass, summary, estimate_blade_cost, estimate_rotor_cost (+1) |
| `02-wind-energy/structural/register_blade.py` | register_blade_design, blade_design_exists, print_design_summary, _main |
| `src/modules/wind_energy_v2/structural/register_blade.py` | register_blade_design, blade_design_exists, print_design_summary, _main |

## Entry Points

Start here when exploring this area:

- **`estimate_stress`** (Function) — `02-wind-energy/structural/verify_safety_factors.py:89`
- **`compute_safety_factors`** (Function) — `02-wind-energy/structural/verify_safety_factors.py:189`
- **`find_blade_design_id`** (Function) — `02-wind-energy/structural/verify_safety_factors.py:244`
- **`register_validation_result`** (Function) — `02-wind-energy/structural/verify_safety_factors.py:311`
- **`check_v_safety_factor_view`** (Function) — `02-wind-energy/structural/verify_safety_factors.py:423`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `estimate_stress` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 89 |
| `compute_safety_factors` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 189 |
| `find_blade_design_id` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 244 |
| `register_validation_result` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 311 |
| `check_v_safety_factor_view` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 423 |
| `main` | Function | `02-wind-energy/structural/verify_safety_factors.py` | 462 |
| `estimate_stress` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 89 |
| `compute_safety_factors` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 189 |
| `find_blade_design_id` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 244 |
| `register_validation_result` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 311 |
| `check_v_safety_factor_view` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 423 |
| `main` | Function | `src/modules/wind_energy_v2/structural/verify_safety_factors.py` | 462 |
| `estimate_blade_cost` | Function | `02-wind-energy/structural/blade_cost_estimate.py` | 193 |
| `estimate_rotor_cost` | Function | `02-wind-energy/structural/blade_cost_estimate.py` | 245 |
| `main` | Function | `02-wind-energy/structural/blade_cost_estimate.py` | 280 |
| `estimate_blade_cost` | Function | `src/modules/wind_energy_v2/structural/blade_cost_estimate.py` | 193 |
| `estimate_rotor_cost` | Function | `src/modules/wind_energy_v2/structural/blade_cost_estimate.py` | 245 |
| `main` | Function | `src/modules/wind_energy_v2/structural/blade_cost_estimate.py` | 280 |
| `compute_fatigue_damage` | Function | `02-wind-energy/structural/fatigue_analysis.py` | 297 |
| `main` | Function | `02-wind-energy/structural/fatigue_analysis.py` | 384 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Chord_at` | intra_community | 5 |
| `Main → Chord_at` | intra_community | 5 |
| `Main → Cdf` | cross_community | 4 |
| `Main → Steady_stress_at_wind` | cross_community | 4 |
| `Main → Turb_std_dev` | cross_community | 4 |
| `Main → Cdf` | cross_community | 4 |
| `Main → Steady_stress_at_wind` | cross_community | 4 |
| `Main → Turb_std_dev` | cross_community | 4 |
| `Main → Cycles_to_failure` | cross_community | 3 |
| `Main → Cycles_to_failure` | cross_community | 3 |

## How to Explore

1. `context({name: "estimate_stress"})` — see callers and callees
2. `query({search_query: "structural"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
