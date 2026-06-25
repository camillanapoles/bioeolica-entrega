---
name: micro-particle
description: "Skill for the Micro-particle area of Lab-builder. 15 symbols across 2 files."
---

# Micro-particle

15 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `01-material-characterization/`
- Understanding how generate_particle_field, estimate_local_stress_concentration, compute_effective_properties work
- Modifying micro-particle-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `01-material-characterization/micro-particle/particle_distribution_model.py` | _get_lambda_0, generate_particle_field, _goodier_stress_concentration, estimate_local_stress_concentration, compute_effective_properties (+3) |
| `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | generate_particle_field, _goodier_stress_concentration, estimate_local_stress_concentration, compute_effective_properties, penetration_profile (+2) |

## Entry Points

Start here when exploring this area:

- **`generate_particle_field`** (Function) — `01-material-characterization/micro-particle/particle_distribution_model.py:175`
- **`estimate_local_stress_concentration`** (Function) — `01-material-characterization/micro-particle/particle_distribution_model.py:368`
- **`compute_effective_properties`** (Function) — `01-material-characterization/micro-particle/particle_distribution_model.py:505`
- **`penetration_profile`** (Function) — `01-material-characterization/micro-particle/particle_distribution_model.py:655`
- **`generate_particle_field`** (Function) — `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py:152`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `generate_particle_field` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 175 |
| `estimate_local_stress_concentration` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 368 |
| `compute_effective_properties` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 505 |
| `penetration_profile` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 655 |
| `generate_particle_field` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 152 |
| `estimate_local_stress_concentration` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 345 |
| `compute_effective_properties` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 482 |
| `penetration_profile` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 632 |
| `_get_lambda_0` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 58 |
| `_goodier_stress_concentration` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 304 |
| `_format_header` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 789 |
| `_run_analysis` | Function | `01-material-characterization/micro-particle/particle_distribution_model.py` | 795 |
| `_goodier_stress_concentration` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 281 |
| `_format_header` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 766 |
| `_run_analysis` | Function | `src/modules/material_characterization_01/micro-particle/particle_distribution_model.py` | 772 |

## How to Explore

1. `context({name: "generate_particle_field"})` — see callers and callees
2. `query({search_query: "micro-particle"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
