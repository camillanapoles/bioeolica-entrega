---
name: quality
description: "Skill for the Quality area of Lab-builder. 60 symbols across 9 files."
---

# Quality

60 symbols | 9 files | Cohesion: 87%

## When to Use

- Working with code in `common/`
- Understanding how get_objects_with_scores, get_dimension_scores, get_dimension_weights work
- Modifying quality-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `common/quality/batch_score.py` | _completeness_ratio, _score_test_result, _score_community_profile, _score_wind_turbine_system, _map_completeness_to_score (+11) |
| `03-data-management/quality/pqms_report.py` | get_objects_with_scores, get_dimension_scores, get_dimension_weights, compute_weighted_avg, check_sc008_status (+3) |
| `src/modules/data_management_03/quality/pqms_report.py` | get_objects_with_scores, get_dimension_scores, get_dimension_weights, compute_weighted_avg, check_sc008_status (+3) |
| `03-data-management/quality/batch_quality_scorer.py` | get_objects_missing_scores, assign_quality_scores, batch_score_all, verify_coverage, main |
| `common/quality/batch_quality_scorer.py` | get_objects_missing_scores, assign_quality_scores, batch_score_all, verify_coverage, main |
| `common/quality/compute_pqms.py` | compute_pqms, get_pending_objects, check_sc008, print_report, main |
| `src/modules/data_management_03/quality/batch_quality_scorer.py` | get_objects_missing_scores, assign_quality_scores, batch_score_all, verify_coverage, main |
| `03-data-management/quality/pqms_pipeline.py` | _get_objects_with_scores, run_pipeline, generate_pqms_summary_report, main |
| `src/modules/data_management_03/quality/pqms_pipeline.py` | _get_objects_with_scores, run_pipeline, generate_pqms_summary_report, main |

## Entry Points

Start here when exploring this area:

- **`get_objects_with_scores`** (Function) — `03-data-management/quality/pqms_report.py:30`
- **`get_dimension_scores`** (Function) — `03-data-management/quality/pqms_report.py:43`
- **`get_dimension_weights`** (Function) — `03-data-management/quality/pqms_report.py:52`
- **`compute_weighted_avg`** (Function) — `03-data-management/quality/pqms_report.py:67`
- **`check_sc008_status`** (Function) — `03-data-management/quality/pqms_report.py:79`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `get_objects_with_scores` | Function | `03-data-management/quality/pqms_report.py` | 30 |
| `get_dimension_scores` | Function | `03-data-management/quality/pqms_report.py` | 43 |
| `get_dimension_weights` | Function | `03-data-management/quality/pqms_report.py` | 52 |
| `compute_weighted_avg` | Function | `03-data-management/quality/pqms_report.py` | 67 |
| `check_sc008_status` | Function | `03-data-management/quality/pqms_report.py` | 79 |
| `get_source_quality_stats` | Function | `03-data-management/quality/pqms_report.py` | 119 |
| `generate_report` | Function | `03-data-management/quality/pqms_report.py` | 135 |
| `main` | Function | `03-data-management/quality/pqms_report.py` | 225 |
| `get_objects_with_scores` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 30 |
| `get_dimension_scores` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 43 |
| `get_dimension_weights` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 52 |
| `compute_weighted_avg` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 67 |
| `check_sc008_status` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 79 |
| `get_source_quality_stats` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 119 |
| `generate_report` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 135 |
| `main` | Function | `src/modules/data_management_03/quality/pqms_report.py` | 225 |
| `get_objects_missing_scores` | Function | `03-data-management/quality/batch_quality_scorer.py` | 61 |
| `assign_quality_scores` | Function | `03-data-management/quality/batch_quality_scorer.py` | 74 |
| `batch_score_all` | Function | `03-data-management/quality/batch_quality_scorer.py` | 107 |
| `verify_coverage` | Function | `03-data-management/quality/batch_quality_scorer.py` | 137 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _get_objects_with_scores` | intra_community | 4 |
| `Main → Get_objects_with_scores` | intra_community | 4 |
| `Main → Get_dimension_weights` | intra_community | 4 |
| `Main → Get_dimension_scores` | intra_community | 4 |
| `Main → Compute_weighted_avg` | intra_community | 4 |
| `Main → _get_objects_with_scores` | intra_community | 4 |
| `Main → Get_objects_with_scores` | intra_community | 4 |
| `Main → Get_dimension_weights` | intra_community | 4 |
| `Main → Get_dimension_scores` | intra_community | 4 |
| `Main → Compute_weighted_avg` | intra_community | 4 |

## How to Explore

1. `context({name: "get_objects_with_scores"})` — see callers and callees
2. `query({search_query: "quality"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
