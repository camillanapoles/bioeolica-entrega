---
name: cad
description: "Skill for the Cad area of Lab-builder. 27 symbols across 18 files."
---

# Cad

27 symbols | 18 files | Cohesion: 100%

## When to Use

- Working with code in `cad-cae-platform/`
- Understanding how build_shape, export_step, mesh_step work
- Modifying cad-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `cad-cae-platform/modules/cad/cad_generator.py` | build_shape, generate |
| `cad-cae-platform/modules/cad/pipeline.py` | parse_args, main |
| `cad/cad_generator.py` | build_shape, generate |
| `cad/pipeline.py` | parse_args, main |
| `src/modules/cad/cad_generator.py` | build_shape, generate |
| `src/modules/cad/pipeline.py` | parse_args, main |
| `cad-cae-platform/modules/cad/layer_designer.py` | __init__, _validate |
| `cad/layer_designer.py` | __init__, _validate |
| `src/modules/cad/layer_designer.py` | __init__, _validate |
| `cad-cae-platform/modules/cad/export.py` | export_step |

## Entry Points

Start here when exploring this area:

- **`build_shape`** (Function) — `cad-cae-platform/modules/cad/cad_generator.py:33`
- **`export_step`** (Function) — `cad-cae-platform/modules/cad/export.py:15`
- **`mesh_step`** (Function) — `cad-cae-platform/modules/cad/mesh.py:11`
- **`parse_parameters`** (Function) — `cad-cae-platform/modules/cad/parametric.py:58`
- **`parse_args`** (Function) — `cad-cae-platform/modules/cad/pipeline.py:18`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `build_shape` | Function | `cad-cae-platform/modules/cad/cad_generator.py` | 33 |
| `export_step` | Function | `cad-cae-platform/modules/cad/export.py` | 15 |
| `mesh_step` | Function | `cad-cae-platform/modules/cad/mesh.py` | 11 |
| `parse_parameters` | Function | `cad-cae-platform/modules/cad/parametric.py` | 58 |
| `parse_args` | Function | `cad-cae-platform/modules/cad/pipeline.py` | 18 |
| `main` | Function | `cad-cae-platform/modules/cad/pipeline.py` | 28 |
| `build_shape` | Function | `cad/cad_generator.py` | 33 |
| `export_step` | Function | `cad/export.py` | 15 |
| `mesh_step` | Function | `cad/mesh.py` | 11 |
| `parse_parameters` | Function | `cad/parametric.py` | 58 |
| `parse_args` | Function | `cad/pipeline.py` | 18 |
| `main` | Function | `cad/pipeline.py` | 28 |
| `build_shape` | Function | `src/modules/cad/cad_generator.py` | 33 |
| `export_step` | Function | `src/modules/cad/export.py` | 15 |
| `mesh_step` | Function | `src/modules/cad/mesh.py` | 11 |
| `parse_parameters` | Function | `src/modules/cad/parametric.py` | 58 |
| `parse_args` | Function | `src/modules/cad/pipeline.py` | 18 |
| `main` | Function | `src/modules/cad/pipeline.py` | 28 |
| `generate` | Method | `cad-cae-platform/modules/cad/cad_generator.py` | 58 |
| `generate` | Method | `cad/cad_generator.py` | 58 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Build_shape` | intra_community | 4 |
| `Main → Build_shape` | intra_community | 4 |
| `Main → Build_shape` | intra_community | 4 |

## How to Explore

1. `context({name: "build_shape"})` — see callers and callees
2. `query({search_query: "cad"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
