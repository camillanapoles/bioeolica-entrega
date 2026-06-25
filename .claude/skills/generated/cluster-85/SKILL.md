---
name: cluster-85
description: "Skill for the Cluster_85 area of Lab-builder. 10 symbols across 1 files."
---

# Cluster_85

10 symbols | 1 files | Cohesion: 95%

## When to Use

- Working with code in `common/`
- Understanding how weibull_mean, weibull_std, weibull_median work
- Modifying cluster_85-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `common/wind_utils.py` | weibull_mean, weibull_std, weibull_median, weibull_mode, wind_at_height (+5) |

## Entry Points

Start here when exploring this area:

- **`weibull_mean`** (Function) — `common/wind_utils.py:48`
- **`weibull_std`** (Function) — `common/wind_utils.py:63`
- **`weibull_median`** (Function) — `common/wind_utils.py:80`
- **`weibull_mode`** (Function) — `common/wind_utils.py:95`
- **`wind_at_height`** (Function) — `common/wind_utils.py:168`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `weibull_mean` | Function | `common/wind_utils.py` | 48 |
| `weibull_std` | Function | `common/wind_utils.py` | 63 |
| `weibull_median` | Function | `common/wind_utils.py` | 80 |
| `weibull_mode` | Function | `common/wind_utils.py` | 95 |
| `wind_at_height` | Function | `common/wind_utils.py` | 168 |
| `mean_power_density` | Function | `common/wind_utils.py` | 232 |
| `energy_pattern_factor` | Function | `common/wind_utils.py` | 248 |
| `air_density` | Function | `common/wind_utils.py` | 271 |
| `swept_area` | Function | `common/wind_utils.py` | 418 |
| `_test` | Function | `common/wind_utils.py` | 476 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_86 | 1 calls |

## How to Explore

1. `context({name: "weibull_mean"})` — see callers and callees
2. `query({search_query: "cluster_85"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
