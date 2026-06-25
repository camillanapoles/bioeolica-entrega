---
name: etl
description: "Skill for the Etl area of Lab-builder. 44 symbols across 10 files."
---

# Etl

44 symbols | 10 files | Cohesion: 100%

## When to Use

- Working with code in `03-data-management/`
- Understanding how export_objects, export_quality_scores, export_provenance_chain work
- Modifying etl-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `03-data-management/etl/export_queries.py` | export_objects, _enrich_with_entity_data, _to_csv, export_quality_scores, export_provenance_chain (+2) |
| `src/modules/data_management_03/etl/export_queries.py` | export_objects, _enrich_with_entity_data, _to_csv, export_quality_scores, export_provenance_chain (+2) |
| `03-data-management/etl/ingest_simulations.py` | _validate_simulation_data, ingest_simulation, list_simulations, main |
| `03-data-management/etl/ingest_specimens.py` | _validate_specimen_data, ingest_specimen, list_specimens, main |
| `03-data-management/etl/ingest_test_results.py` | _validate_test_result_data, ingest_test_result, list_test_results, main |
| `src/modules/data_management_03/etl/ingest_simulations.py` | _validate_simulation_data, ingest_simulation, list_simulations, main |
| `src/modules/data_management_03/etl/ingest_specimens.py` | _validate_specimen_data, ingest_specimen, list_specimens, main |
| `src/modules/data_management_03/etl/ingest_test_results.py` | _validate_test_result_data, ingest_test_result, list_test_results, main |
| `03-data-management/etl/ingest_validation_references.py` | register_validation_references, report, main |
| `src/modules/data_management_03/etl/ingest_validation_references.py` | register_validation_references, report, main |

## Entry Points

Start here when exploring this area:

- **`export_objects`** (Function) — `03-data-management/etl/export_queries.py:28`
- **`export_quality_scores`** (Function) — `03-data-management/etl/export_queries.py:245`
- **`export_provenance_chain`** (Function) — `03-data-management/etl/export_queries.py:293`
- **`main`** (Function) — `03-data-management/etl/export_queries.py:331`
- **`export_objects`** (Function) — `src/modules/data_management_03/etl/export_queries.py:28`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `export_objects` | Function | `03-data-management/etl/export_queries.py` | 28 |
| `export_quality_scores` | Function | `03-data-management/etl/export_queries.py` | 245 |
| `export_provenance_chain` | Function | `03-data-management/etl/export_queries.py` | 293 |
| `main` | Function | `03-data-management/etl/export_queries.py` | 331 |
| `export_objects` | Function | `src/modules/data_management_03/etl/export_queries.py` | 28 |
| `export_quality_scores` | Function | `src/modules/data_management_03/etl/export_queries.py` | 245 |
| `export_provenance_chain` | Function | `src/modules/data_management_03/etl/export_queries.py` | 293 |
| `main` | Function | `src/modules/data_management_03/etl/export_queries.py` | 331 |
| `ingest_simulation` | Function | `03-data-management/etl/ingest_simulations.py` | 75 |
| `list_simulations` | Function | `03-data-management/etl/ingest_simulations.py` | 152 |
| `main` | Function | `03-data-management/etl/ingest_simulations.py` | 188 |
| `ingest_specimen` | Function | `03-data-management/etl/ingest_specimens.py` | 133 |
| `list_specimens` | Function | `03-data-management/etl/ingest_specimens.py` | 224 |
| `main` | Function | `03-data-management/etl/ingest_specimens.py` | 253 |
| `ingest_test_result` | Function | `03-data-management/etl/ingest_test_results.py` | 109 |
| `list_test_results` | Function | `03-data-management/etl/ingest_test_results.py` | 199 |
| `main` | Function | `03-data-management/etl/ingest_test_results.py` | 235 |
| `ingest_simulation` | Function | `src/modules/data_management_03/etl/ingest_simulations.py` | 75 |
| `list_simulations` | Function | `src/modules/data_management_03/etl/ingest_simulations.py` | 152 |
| `main` | Function | `src/modules/data_management_03/etl/ingest_simulations.py` | 188 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _to_csv` | intra_community | 3 |
| `Main → _enrich_with_entity_data` | intra_community | 3 |
| `Main → _to_csv` | intra_community | 3 |
| `Main → _enrich_with_entity_data` | intra_community | 3 |
| `Main → _validate_simulation_data` | intra_community | 3 |
| `Main → _validate_specimen_data` | intra_community | 3 |
| `Main → _validate_test_result_data` | intra_community | 3 |
| `Main → _validate_simulation_data` | intra_community | 3 |
| `Main → _validate_specimen_data` | intra_community | 3 |
| `Main → _validate_test_result_data` | intra_community | 3 |

## How to Explore

1. `context({name: "export_objects"})` — see callers and callees
2. `query({search_query: "etl"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
