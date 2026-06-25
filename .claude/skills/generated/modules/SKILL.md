---
name: modules
description: "Skill for the Modules area of Lab-builder. 431 symbols across 79 files."
---

# Modules

431 symbols | 79 files | Cohesion: 93%

## When to Use

- Working with code in `src/`
- Understanding how test_heatmap_scatter, test_heatmap_surface, test_stress_field work
- Modifying modules-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/modules/cad_visualization.py` | _plot_filename, _maybe_register, _maybe_log, _set_interactive, plot_heatmap_overlay (+27) |
| `src/modules/topopt_manufacturing.py` | apply_min_feature, step, solve, _relative_change, _detect_overhang_2d (+13) |
| `src/modules/model_calibration.py` | _compute_goodness, calibrate, calibrate_monte_carlo, calibrate_bayesian, log_prior (+10) |
| `src/modules/simulation_comparison.py` | _get, _projected, rmse, mae, r2 (+9) |
| `src/modules/m3_analysis.py` | __post_init__, density_air, summary, total_thickness_mm, stacking_sequence (+7) |
| `src/modules/economico.py` | npv, profitability_index, annualized_return, sensitivity, monte_carlo (+7) |
| `src/modules/kinematic_machine.py` | solve_position, solve_velocity, joint_positions, coupler_curve, render_mechanism_3d (+7) |
| `src/tests/test_cad_viz.py` | test_heatmap_scatter, test_heatmap_surface, test_stress_field, test_boundary_layer, test_laminate (+6) |
| `src/modules/topopt_avancada.py` | _hex8_node_indices, _hex8_edof, _build_global_stiffness, _filter_sensitivities, _optimality_criteria_update (+6) |
| `src/modules/topopt_multiobj.py` | _compute_compliance, _compute_mass_fraction, _compute_cost_fraction, step, solve (+5) |

## Entry Points

Start here when exploring this area:

- **`test_heatmap_scatter`** (Function) — `src/tests/test_cad_viz.py:36`
- **`test_heatmap_surface`** (Function) — `src/tests/test_cad_viz.py:46`
- **`test_stress_field`** (Function) — `src/tests/test_cad_viz.py:71`
- **`test_boundary_layer`** (Function) — `src/tests/test_cad_viz.py:79`
- **`test_laminate`** (Function) — `src/tests/test_cad_viz.py:90`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TopOpt` | Class | `src/modules/topology_optimization.py` | 124 |
| `TopOptMultiObj` | Class | `src/modules/topopt_multiobj.py` | 62 |
| `test_heatmap_scatter` | Function | `src/tests/test_cad_viz.py` | 36 |
| `test_heatmap_surface` | Function | `src/tests/test_cad_viz.py` | 46 |
| `test_stress_field` | Function | `src/tests/test_cad_viz.py` | 71 |
| `test_boundary_layer` | Function | `src/tests/test_cad_viz.py` | 79 |
| `test_laminate` | Function | `src/tests/test_cad_viz.py` | 90 |
| `test_laminate_3d` | Function | `src/tests/test_cad_viz.py` | 96 |
| `test_wind_rose` | Function | `src/tests/test_cad_viz.py` | 102 |
| `test_wind_rose_plot` | Function | `src/tests/test_cad_viz.py` | 108 |
| `test_laminate_view` | Function | `src/tests/test_lab0.py` | 30 |
| `test_wind_rose` | Function | `src/tests/test_lab0.py` | 49 |
| `test_add_reference` | Function | `src/tests/test_scientific_writing.py` | 96 |
| `test_citation_format_ieee` | Function | `src/tests/test_scientific_writing.py` | 110 |
| `test_citation_format_abnt` | Function | `src/tests/test_scientific_writing.py` | 128 |
| `test_generate_bibtex` | Function | `src/tests/test_scientific_writing.py` | 144 |
| `test_full_report` | Function | `src/tests/test_scientific_writing.py` | 165 |
| `test_empty_report` | Function | `src/tests/test_scientific_writing.py` | 197 |
| `test_bibliography_list` | Function | `src/tests/test_scientific_writing.py` | 205 |
| `test_femodel` | Function | `src/tests/test_fem_solver.py` | 10 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Report → _get` | intra_community | 5 |
| `Plot_heatmap_overlay → _naca_thickness` | cross_community | 4 |
| `Calibrate_bayesian → _format_bounds` | intra_community | 4 |
| `Calibrate_bayesian → _compute_goodness` | intra_community | 4 |
| `Wrapper → To_dict` | intra_community | 4 |
| `Report → _imp` | intra_community | 4 |
| `Results → _imp` | intra_community | 4 |
| `Step → _overhang_interface_3d` | cross_community | 4 |
| `Step → _overhang_interface_2d` | cross_community | 4 |
| `Plot_heatmap_overlay → Section_chord` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 21 calls |

## How to Explore

1. `context({name: "test_heatmap_scatter"})` — see callers and callees
2. `query({search_query: "modules"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
