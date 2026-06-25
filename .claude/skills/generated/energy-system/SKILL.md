---
name: energy-system
description: "Skill for the Energy-system area of Lab-builder. 152 symbols across 34 files."
---

# Energy-system

152 symbols | 34 files | Cohesion: 94%

## When to Use

- Working with code in `02-wind-energy/`
- Understanding how compute_bom, compute_bom, compute_battery_sizing work
- Modifying energy-system-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `02-wind-energy/energy-system/bom_cost_model.py` | _tower_mass, _blade_mass, _generator_mass, _magnet_mass, _copper_mass (+5) |
| `src/modules/wind_energy_v2/energy-system/bom_cost_model.py` | _tower_mass, _blade_mass, _generator_mass, _magnet_mass, _copper_mass (+5) |
| `02-wind-energy/energy-system/validate_sc010.py` | run_script, query_simulation_results, query_validation_references, extract_carbon_reduction, extract_biodegradable_pct (+4) |
| `src/modules/wind_energy_v2/energy-system/validate_sc010.py` | run_script, query_simulation_results, query_validation_references, extract_carbon_reduction, extract_biodegradable_pct (+4) |
| `02-wind-energy/energy-system/lca_end_of_life.py` | get_material_eol_data, get_fiberglass_eol_data, assess_eol_scenarios, register_eol_assessment, report (+1) |
| `02-wind-energy/energy-system/system_sizing.py` | weibull_mean, wind_at_height, power_in_wind, size_system, report (+1) |
| `src/modules/wind_energy_v2/energy-system/lca_end_of_life.py` | get_material_eol_data, get_fiberglass_eol_data, assess_eol_scenarios, register_eol_assessment, report (+1) |
| `src/modules/wind_energy_v2/energy-system/system_sizing.py` | weibull_mean, wind_at_height, power_in_wind, size_system, report (+1) |
| `02-wind-energy/energy-system/lca_inventory.py` | build_inventory, compute_aggregate, register_lca_inventory, report_inventory, main |
| `02-wind-energy/energy-system/lca_report.py` | compute_report, grid_intensity_kgco2e, register_lca_report, report, main |

## Entry Points

Start here when exploring this area:

- **`compute_bom`** (Function) — `02-wind-energy/energy-system/bom_cost_model.py:114`
- **`compute_bom`** (Function) — `src/modules/wind_energy_v2/energy-system/bom_cost_model.py:114`
- **`compute_battery_sizing`** (Function) — `02-wind-energy/energy-system/battery_sizing.py:42`
- **`compute_cost_breakdown`** (Function) — `02-wind-energy/energy-system/cost_breakdown.py:130`
- **`compute_lcoe`** (Function) — `02-wind-energy/energy-system/lcoe_model.py:48`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `compute_bom` | Function | `02-wind-energy/energy-system/bom_cost_model.py` | 114 |
| `compute_bom` | Function | `src/modules/wind_energy_v2/energy-system/bom_cost_model.py` | 114 |
| `compute_battery_sizing` | Function | `02-wind-energy/energy-system/battery_sizing.py` | 42 |
| `compute_cost_breakdown` | Function | `02-wind-energy/energy-system/cost_breakdown.py` | 130 |
| `compute_lcoe` | Function | `02-wind-energy/energy-system/lcoe_model.py` | 48 |
| `compute_scenario` | Function | `02-wind-energy/energy-system/sensitivity_cost.py` | 39 |
| `run_script` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 84 |
| `query_simulation_results` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 111 |
| `query_validation_references` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 136 |
| `extract_carbon_reduction` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 155 |
| `extract_biodegradable_pct` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 185 |
| `extract_source_quality` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 199 |
| `validate_sc010` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 213 |
| `format_report` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 428 |
| `main` | Function | `02-wind-energy/energy-system/validate_sc010.py` | 463 |
| `compute_battery_sizing` | Function | `src/modules/wind_energy_v2/energy-system/battery_sizing.py` | 42 |
| `compute_cost_breakdown` | Function | `src/modules/wind_energy_v2/energy-system/cost_breakdown.py` | 130 |
| `compute_lcoe` | Function | `src/modules/wind_energy_v2/energy-system/lcoe_model.py` | 48 |
| `compute_scenario` | Function | `src/modules/wind_energy_v2/energy-system/sensitivity_cost.py` | 39 |
| `run_script` | Function | `src/modules/wind_energy_v2/energy-system/validate_sc010.py` | 84 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Weibull_mean` | cross_community | 3 |
| `Main → Wind_at_height` | cross_community | 3 |
| `Main → Power_in_wind` | cross_community | 3 |
| `Main → Weibull_mean` | cross_community | 3 |
| `Main → Wind_at_height` | cross_community | 3 |
| `Main → Power_in_wind` | cross_community | 3 |
| `Main → Get_material_eol_data` | intra_community | 3 |
| `Main → Get_fiberglass_eol_data` | intra_community | 3 |
| `Main → Grid_intensity_kgco2e` | intra_community | 3 |
| `Main → Check_sc_targets` | intra_community | 3 |

## How to Explore

1. `context({name: "compute_bom"})` — see callers and callees
2. `query({search_query: "energy-system"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
