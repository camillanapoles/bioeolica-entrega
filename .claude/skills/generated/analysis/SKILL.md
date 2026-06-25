---
name: analysis
description: "Skill for the Analysis area of Lab-builder. 77 symbols across 12 files."
---

# Analysis

77 symbols | 12 files | Cohesion: 97%

## When to Use

- Working with code in `01-material-characterization/`
- Understanding how define_parameters, define_metrics, run_sensitivity work
- Modifying analysis-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `01-material-characterization/analysis/sensitivity_analysis.py` | define_parameters, define_metrics, run_sensitivity, create_sensitivity_matrix, find_optimal_window (+4) |
| `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | define_parameters, define_metrics, run_sensitivity, create_sensitivity_matrix, find_optimal_window (+4) |
| `01-material-characterization/analysis/calibrate_model.py` | _get_hardness_baseline, _property_error_pct, calibrate_property, _find_target, _update_fem_values (+4) |
| `src/modules/material_characterization_01/analysis/calibrate_model.py` | define_targets, compute_overall_error, _print_calibration, main, _property_error_pct (+3) |
| `01-material-characterization/analysis/comparison_report.py` | get_comparison_data, generate_comparison_table, _status_marker, check_sc001_targets, generate_report_text (+1) |
| `01-material-characterization/analysis/register_specimens.py` | register_baseline_specimen, register_composite_specimen, register_specimens, specimen_exists, print_specimen_summary (+1) |
| `src/modules/material_characterization_01/analysis/comparison_report.py` | get_comparison_data, generate_comparison_table, _status_marker, check_sc001_targets, generate_report_text (+1) |
| `src/modules/material_characterization_01/analysis/register_specimens.py` | register_baseline_specimen, register_composite_specimen, register_specimens, specimen_exists, print_specimen_summary (+1) |
| `01-material-characterization/analysis/register_test_results.py` | register_test_result, register_composite_results, register_baseline_results, print_result_summary, _main |
| `src/modules/material_characterization_01/analysis/register_test_results.py` | register_test_result, register_composite_results, register_baseline_results, print_result_summary, _main |

## Entry Points

Start here when exploring this area:

- **`define_parameters`** (Function) — `01-material-characterization/analysis/sensitivity_analysis.py:90`
- **`define_metrics`** (Function) — `01-material-characterization/analysis/sensitivity_analysis.py:120`
- **`run_sensitivity`** (Function) — `01-material-characterization/analysis/sensitivity_analysis.py:280`
- **`create_sensitivity_matrix`** (Function) — `01-material-characterization/analysis/sensitivity_analysis.py:303`
- **`find_optimal_window`** (Function) — `01-material-characterization/analysis/sensitivity_analysis.py:331`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `define_parameters` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 90 |
| `define_metrics` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 120 |
| `run_sensitivity` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 280 |
| `create_sensitivity_matrix` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 303 |
| `find_optimal_window` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 331 |
| `print_sensitivity_table` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 441 |
| `main` | Function | `01-material-characterization/analysis/sensitivity_analysis.py` | 470 |
| `define_parameters` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 90 |
| `define_metrics` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 120 |
| `run_sensitivity` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 280 |
| `create_sensitivity_matrix` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 303 |
| `find_optimal_window` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 331 |
| `print_sensitivity_table` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 441 |
| `main` | Function | `src/modules/material_characterization_01/analysis/sensitivity_analysis.py` | 470 |
| `get_comparison_data` | Function | `01-material-characterization/analysis/comparison_report.py` | 64 |
| `generate_comparison_table` | Function | `01-material-characterization/analysis/comparison_report.py` | 106 |
| `check_sc001_targets` | Function | `01-material-characterization/analysis/comparison_report.py` | 145 |
| `generate_report_text` | Function | `01-material-characterization/analysis/comparison_report.py` | 218 |
| `main` | Function | `01-material-characterization/analysis/comparison_report.py` | 269 |
| `register_baseline_specimen` | Function | `01-material-characterization/analysis/register_specimens.py` | 90 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _get_hardness_baseline` | cross_community | 4 |
| `Main → _status_marker` | intra_community | 4 |
| `Main → _status_marker` | intra_community | 4 |
| `Main → Run_sensitivity` | intra_community | 3 |
| `Main → _fmt_table_row` | intra_community | 3 |
| `Main → Run_sensitivity` | intra_community | 3 |
| `Main → _fmt_table_row` | intra_community | 3 |
| `Main → _property_error_pct` | cross_community | 3 |
| `Main → _find_target` | cross_community | 3 |
| `Main → _property_error_pct` | cross_community | 3 |

## How to Explore

1. `context({name: "define_parameters"})` — see callers and callees
2. `query({search_query: "analysis"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
