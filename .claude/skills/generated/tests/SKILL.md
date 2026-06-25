---
name: tests
description: "Skill for the Tests area of Lab-builder. 606 symbols across 75 files."
---

# Tests

606 symbols | 75 files | Cohesion: 89%

## When to Use

- Working with code in `src/`
- Understanding how create_default_config, macro_from_cad_and_env, carnot_efficiency work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/tests/test_topology_optimization.py` | _converging_opt, test_solve_density_shape, test_solve_density_bounds, test_solve_converges_with_default_tol, test_solve_respects_max_iter (+40) |
| `src/tests/test_fluid_dynamics.py` | test_basic_profile, test_terrain_open, test_terrain_suburban, test_terrain_urban, test_unknown_terrain_falls_back_to_alpha (+25) |
| `src/tests/test_validacao_experimental.py` | test_identical_data_all_metrics_zero, test_divergent_data_all_metrics_positive, test_known_mape_matches_expected, test_rmse_metric_explicit, test_invalid_metric_raises_value_error (+22) |
| `src/tests/test_electromechanical.py` | test_between_95_98, test_increases_with_power, test_full_load, test_no_load, test_returns_dict (+17) |
| `src/tests/test_thermodynamics.py` | test_carnot, test_zero_hot, test_ideal_cycle, test_basic, test_superheat_increases_efficiency (+15) |
| `src/tests/test_piezoelectric.py` | test_eform_stress_shape, test_dform_strain_shape, test_dform_d31_contribution, test_actuator_strain_returns_dict, test_actuator_strain_negative_thickness (+15) |
| `src/tests/test_fatigue.py` | test_cycles_to_failure, test_cycles_to_failure_higher_stress_shorter_life, test_damage_single_cycle, test_damage_exceeds_unity, test_damage_zero_ranges (+14) |
| `src/tests/test_creep.py` | test_strain_rate_positive, test_strain_rate_increases_with_stress, test_strain_rate_increases_with_temperature, test_creep_strain_increases, test_creep_strain_final_positive (+13) |
| `kdi-m3-bridge/tests/test_config_manager.py` | test_load_default, test_load_nonexistent_uses_defaults, test_create_default, test_from_dict, test_get_dot_path (+11) |
| `src/tests/test_digital_twin.py` | test_simulate_temperature, test_simulate_strain, test_simulate_vibration, test_unknown_sensor_raises, test_sensor_with_fault (+11) |

## Entry Points

Start here when exploring this area:

- **`create_default_config`** (Function) — `kdi-m3-bridge/modules/config_manager.py:169`
- **`macro_from_cad_and_env`** (Function) — `kdi-m3-bridge/modules/kdi_macro.py:211`
- **`carnot_efficiency`** (Function) — `src/modules/thermodynamics.py:86`
- **`rankine_cycle_efficiency`** (Function) — `src/modules/thermodynamics.py:93`
- **`exergy`** (Function) — `src/modules/thermodynamics.py:128`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `create_default_config` | Function | `kdi-m3-bridge/modules/config_manager.py` | 169 |
| `macro_from_cad_and_env` | Function | `kdi-m3-bridge/modules/kdi_macro.py` | 211 |
| `carnot_efficiency` | Function | `src/modules/thermodynamics.py` | 86 |
| `rankine_cycle_efficiency` | Function | `src/modules/thermodynamics.py` | 93 |
| `exergy` | Function | `src/modules/thermodynamics.py` | 128 |
| `test_carnot` | Function | `src/tests/test_lab2.py` | 55 |
| `inverter_efficiency` | Function | `src/modules/electromechanical.py` | 130 |
| `transformer_efficiency` | Function | `src/modules/electromechanical.py` | 135 |
| `power_conversion_chain` | Function | `src/modules/electromechanical.py` | 143 |
| `test_power_conversion` | Function | `src/tests/test_lab2.py` | 70 |
| `test_01_material` | Function | `kdi-m3-bridge/tests/test_e2e_complete.py` | 29 |
| `test_composite_defaults` | Function | `src/tests/test_lab1.py` | 19 |
| `test_void_effect` | Function | `src/tests/test_lab1.py` | 48 |
| `test_create_mesh` | Function | `src/tests/test_cfd_solver.py` | 3 |
| `test_solver_init` | Function | `src/tests/test_cfd_solver.py` | 7 |
| `test_navier_stokes` | Function | `src/tests/test_cfd_solver.py` | 12 |
| `wind_profile` | Function | `src/modules/fluid_dynamics.py` | 28 |
| `test_wind_profile` | Function | `src/tests/test_lab2.py` | 35 |
| `test_drying` | Function | `src/tests/test_lab2.py` | 50 |
| `test_context_validate_insufficient` | Function | `src/tests/test_context_engine.py` | 13 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Plot_heatmap_overlay → _naca_thickness` | cross_community | 4 |
| `Plot → Tsai_wu_failure` | cross_community | 3 |
| `Plot_supercell → Unit_cell_atoms` | cross_community | 3 |
| `Calibrate_model → _format_bounds` | cross_community | 3 |
| `Calibrate_model → _compute_goodness` | cross_community | 3 |
| `Step → _node_indices` | cross_community | 3 |
| `Step → _edof_from_nids` | cross_community | 3 |
| `Power_W → Speed_rads` | intra_community | 3 |
| `Results → Von_mises_stress` | cross_community | 3 |
| `Results → Safety_factor` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Modules | 20 calls |

## How to Explore

1. `context({name: "create_default_config"})` — see callers and callees
2. `query({search_query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
