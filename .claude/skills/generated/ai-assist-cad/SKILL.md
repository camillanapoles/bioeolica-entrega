---
name: ai-assist-cad
description: "Skill for the Ai_assist_cad area of Lab-builder. 20 symbols across 3 files."
---

# Ai_assist_cad

20 symbols | 3 files | Cohesion: 100%

## When to Use

- Working with code in `ai_assist_cad/`
- Understanding how extract_all_numbers_with_units, parse_geometric_description, parse_project_parameters work
- Modifying ai_assist_cad-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ai_assist_cad/knowledge_engine.py` | get_material, dimension_shaft, dimension_pipe_diameter, dimension_stator_outer, estimate_mass (+4) |
| `ai_assist_cad/layer_designer.py` | save, to_dict, load, from_dict, __init__ (+1) |
| `ai_assist_cad/nlp_parser.py` | extract_all_numbers_with_units, _extract_text_around_keyword, parse_geometric_description, _parse_specific_patterns, parse_project_parameters |

## Entry Points

Start here when exploring this area:

- **`extract_all_numbers_with_units`** (Function) — `ai_assist_cad/nlp_parser.py:74`
- **`parse_geometric_description`** (Function) — `ai_assist_cad/nlp_parser.py:109`
- **`parse_project_parameters`** (Function) — `ai_assist_cad/nlp_parser.py:237`
- **`get_material`** (Method) — `ai_assist_cad/knowledge_engine.py:29`
- **`dimension_shaft`** (Method) — `ai_assist_cad/knowledge_engine.py:37`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `extract_all_numbers_with_units` | Function | `ai_assist_cad/nlp_parser.py` | 74 |
| `parse_geometric_description` | Function | `ai_assist_cad/nlp_parser.py` | 109 |
| `parse_project_parameters` | Function | `ai_assist_cad/nlp_parser.py` | 237 |
| `get_material` | Method | `ai_assist_cad/knowledge_engine.py` | 29 |
| `dimension_shaft` | Method | `ai_assist_cad/knowledge_engine.py` | 37 |
| `dimension_pipe_diameter` | Method | `ai_assist_cad/knowledge_engine.py` | 56 |
| `dimension_stator_outer` | Method | `ai_assist_cad/knowledge_engine.py` | 85 |
| `estimate_mass` | Method | `ai_assist_cad/knowledge_engine.py` | 100 |
| `dimension_bolt` | Method | `ai_assist_cad/knowledge_engine.py` | 112 |
| `dimension_all` | Method | `ai_assist_cad/knowledge_engine.py` | 158 |
| `save` | Method | `ai_assist_cad/layer_designer.py` | 18 |
| `to_dict` | Method | `ai_assist_cad/layer_designer.py` | 27 |
| `load` | Method | `ai_assist_cad/layer_designer.py` | 23 |
| `from_dict` | Method | `ai_assist_cad/layer_designer.py` | 33 |
| `_extract_text_around_keyword` | Function | `ai_assist_cad/nlp_parser.py` | 96 |
| `_parse_specific_patterns` | Function | `ai_assist_cad/nlp_parser.py` | 171 |
| `__init__` | Method | `ai_assist_cad/knowledge_engine.py` | 18 |
| `_load` | Method | `ai_assist_cad/knowledge_engine.py` | 23 |
| `__init__` | Method | `ai_assist_cad/layer_designer.py` | 41 |
| `_compute_properties` | Method | `ai_assist_cad/layer_designer.py` | 46 |

## How to Explore

1. `context({name: "extract_all_numbers_with_units"})` — see callers and callees
2. `query({search_query: "ai_assist_cad"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
