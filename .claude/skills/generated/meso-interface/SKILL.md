---
name: meso-interface
description: "Skill for the Meso-interface area of Lab-builder. 12 symbols across 2 files."
---

# Meso-interface

12 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `01-material-characterization/`
- Understanding how compute_stress_transfer, estimate_adhesion_strength, interface_failure_criterion work
- Modifying meso-interface-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `01-material-characterization/meso-interface/coating_interface_model.py` | _shear_lag_beta, compute_stress_transfer, estimate_adhesion_strength, interface_failure_criterion, _format_header (+1) |
| `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | _shear_lag_beta, compute_stress_transfer, estimate_adhesion_strength, interface_failure_criterion, _format_header (+1) |

## Entry Points

Start here when exploring this area:

- **`compute_stress_transfer`** (Function) — `01-material-characterization/meso-interface/coating_interface_model.py:226`
- **`estimate_adhesion_strength`** (Function) — `01-material-characterization/meso-interface/coating_interface_model.py:348`
- **`interface_failure_criterion`** (Function) — `01-material-characterization/meso-interface/coating_interface_model.py:506`
- **`compute_stress_transfer`** (Function) — `src/modules/material_characterization_01/meso-interface/coating_interface_model.py:226`
- **`estimate_adhesion_strength`** (Function) — `src/modules/material_characterization_01/meso-interface/coating_interface_model.py:348`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `compute_stress_transfer` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 226 |
| `estimate_adhesion_strength` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 348 |
| `interface_failure_criterion` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 506 |
| `compute_stress_transfer` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 226 |
| `estimate_adhesion_strength` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 348 |
| `interface_failure_criterion` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 506 |
| `_shear_lag_beta` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 172 |
| `_format_header` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 622 |
| `_run_analysis` | Function | `01-material-characterization/meso-interface/coating_interface_model.py` | 628 |
| `_shear_lag_beta` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 172 |
| `_format_header` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 622 |
| `_run_analysis` | Function | `src/modules/material_characterization_01/meso-interface/coating_interface_model.py` | 628 |

## How to Explore

1. `context({name: "compute_stress_transfer"})` — see callers and callees
2. `query({search_query: "meso-interface"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
