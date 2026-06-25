---
name: visualization
description: "Skill for the Visualization area of Lab-builder. 12 symbols across 4 files."
---

# Visualization

12 symbols | 4 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how generate_viewer_html, generate_cylinder_viewer, generate_stress_viewer work
- Modifying visualization-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/modules/visualization/threejs_viewer.py` | generate_viewer_html, generate_cylinder_viewer, generate_stress_viewer, generate_from_step |
| `src/modules/visualization/plot_pqms_radar.py` | get_dimension_scores_for_objects, plot_pqms_radar, main |
| `src/modules/visualization/plot_property_comparison.py` | get_property_comparison, plot_property_comparison, main |
| `src/modules/visualization/dashboard.py` | run_script, main |

## Entry Points

Start here when exploring this area:

- **`generate_viewer_html`** (Function) — `src/modules/visualization/threejs_viewer.py:24`
- **`generate_cylinder_viewer`** (Function) — `src/modules/visualization/threejs_viewer.py:53`
- **`generate_stress_viewer`** (Function) — `src/modules/visualization/threejs_viewer.py:73`
- **`generate_from_step`** (Function) — `src/modules/visualization/threejs_viewer.py:91`
- **`get_dimension_scores_for_objects`** (Function) — `src/modules/visualization/plot_pqms_radar.py:58`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `generate_viewer_html` | Function | `src/modules/visualization/threejs_viewer.py` | 24 |
| `generate_cylinder_viewer` | Function | `src/modules/visualization/threejs_viewer.py` | 53 |
| `generate_stress_viewer` | Function | `src/modules/visualization/threejs_viewer.py` | 73 |
| `generate_from_step` | Function | `src/modules/visualization/threejs_viewer.py` | 91 |
| `get_dimension_scores_for_objects` | Function | `src/modules/visualization/plot_pqms_radar.py` | 58 |
| `plot_pqms_radar` | Function | `src/modules/visualization/plot_pqms_radar.py` | 84 |
| `main` | Function | `src/modules/visualization/plot_pqms_radar.py` | 199 |
| `get_property_comparison` | Function | `src/modules/visualization/plot_property_comparison.py` | 32 |
| `plot_property_comparison` | Function | `src/modules/visualization/plot_property_comparison.py` | 44 |
| `main` | Function | `src/modules/visualization/plot_property_comparison.py` | 108 |
| `run_script` | Function | `src/modules/visualization/dashboard.py` | 22 |
| `main` | Function | `src/modules/visualization/dashboard.py` | 42 |

## How to Explore

1. `context({name: "generate_viewer_html"})` — see callers and callees
2. `query({search_query: "visualization"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
