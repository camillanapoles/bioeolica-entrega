---
name: aerodynamics
description: "Skill for the Aerodynamics area of Lab-builder. 25 symbols across 2 files."
---

# Aerodynamics

25 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `02-wind-energy/`
- Understanding how main, main, mean_wind_at_height work
- Modifying aerodynamics-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `02-wind-energy/aerodynamics/wind_resource.py` | _get_wind_reference_height, mean_wind_at_height, scale_at_height, pdf, cdf (+8) |
| `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | mean_wind_at_height, scale_at_height, pdf, cdf, probability_bin (+7) |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `02-wind-energy/aerodynamics/wind_resource.py:281`
- **`main`** (Function) — `src/modules/wind_energy_v2/aerodynamics/wind_resource.py:262`
- **`mean_wind_at_height`** (Method) — `02-wind-energy/aerodynamics/wind_resource.py:107`
- **`scale_at_height`** (Method) — `02-wind-energy/aerodynamics/wind_resource.py:123`
- **`pdf`** (Method) — `02-wind-energy/aerodynamics/wind_resource.py:129`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `main` | Function | `02-wind-energy/aerodynamics/wind_resource.py` | 281 |
| `main` | Function | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 262 |
| `mean_wind_at_height` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 107 |
| `scale_at_height` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 123 |
| `pdf` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 129 |
| `cdf` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 148 |
| `probability_bin` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 155 |
| `mean_power_density` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 168 |
| `energy_pattern_factor` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 176 |
| `monthly_mean_winds` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 187 |
| `summary` | Method | `02-wind-energy/aerodynamics/wind_resource.py` | 241 |
| `mean_wind_at_height` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 91 |
| `scale_at_height` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 107 |
| `pdf` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 113 |
| `cdf` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 132 |
| `probability_bin` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 139 |
| `mean_power_density` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 152 |
| `energy_pattern_factor` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 160 |
| `monthly_mean_winds` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 171 |
| `summary` | Method | `src/modules/wind_energy_v2/aerodynamics/wind_resource.py` | 225 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Mean_wind_at_height` | intra_community | 5 |
| `Main → Mean_wind_at_height` | intra_community | 5 |
| `Probability_bin → Mean_wind_at_height` | intra_community | 4 |
| `Probability_bin → Mean_wind_at_height` | intra_community | 4 |
| `Main → Energy_pattern_factor` | intra_community | 3 |
| `Main → Energy_pattern_factor` | intra_community | 3 |
| `Pdf → Mean_wind_at_height` | intra_community | 3 |

## How to Explore

1. `context({name: "main"})` — see callers and callees
2. `query({search_query: "aerodynamics"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
