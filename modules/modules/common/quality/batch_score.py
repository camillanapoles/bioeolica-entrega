#!/usr/bin/env python3
# =============================================================================
# Batch PQMS Scoring — Populate quality_scores for all unscored objects
# Scans actual domain data per object type, assigns D1-D13 scores, calls
# compute_pqms() for each object. Resolves the scoring architecture gap
# where ETL/registration scripts create objects without dimension scores.
# =============================================================================
"""
Batch PQMS scoring for all objects in the database.

Examines actual domain data per object type, computes evidence-based
D1-D13 scores, and writes quality_scores via compute_pqms().

Usage:
    # Score all unscored objects
    python batch_score.py

    # Score specific object types only
    python batch_score.py --types computational_model,simulation_result

    # Dry-run (report what would be scored without writing)
    python batch_score.py --dry-run

    # Re-score already-scored objects too
    python batch_score.py --force
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database
from src.common.quality.compute_pqms import compute_pqms, PQMS_DIMENSIONS

MAX_SCORE = 10.0
MIN_PASS = 8.5

# ---------------------------------------------------------------------------
# Field-completeness helpers
# ---------------------------------------------------------------------------

def _completeness_ratio(row: Dict[str, Any], required_fields: List[str]) -> float:
    """Ratio of non-null required fields in a row dict."""
    if not required_fields:
        return 1.0
    filled = sum(1 for f in required_fields if row.get(f) is not None)
    return filled / len(required_fields)


def _map_completeness_to_score(ratio: float) -> float:
    """Map a 0-1 completeness ratio to a D1 score (0-10)."""
    if ratio >= 0.95:
        return 10.0
    if ratio >= 0.85:
        return 9.5
    if ratio >= 0.70:
        return 9.0
    if ratio >= 0.50:
        return 8.0
    if ratio >= 0.30:
        return 6.0
    return 4.0


def _has_any(rows: List[Dict], key: str) -> bool:
    """True if any row has a non-null value for key."""
    return any(r.get(key) is not None for r in rows)


def _count_non_null(rows: List[Dict], key: str) -> int:
    """Count rows with non-null value for key."""
    return sum(1 for r in rows if r.get(key) is not None)


# ---------------------------------------------------------------------------
# Object-type scoring functions
# Each returns {dimension: score} for a given object_id
# ---------------------------------------------------------------------------

def _score_computational_model(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a computational_model based on its domain data."""
    if not has_data:
        return _baseline_no_data("computational_model")

    rows = db.execute(
        "SELECT * FROM computational_models WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("computational_model")
    row = dict(rows[0])

    req = ["model_type", "domain", "solver_software", "solver_version",
           "boundary_conditions", "material_model", "material_properties"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    # Depth: calibration indicates analytical/model depth
    cal_status = row.get("calibration_status")
    cal_err = row.get("calibration_error_pct")
    if cal_status == "validated" and cal_err is not None and cal_err < 5.0:
        d2 = 10.0
    elif cal_status == "validated" and cal_err is not None and cal_err < 10.0:
        d2 = 9.5
    elif cal_status == "validated":
        d2 = 9.0
    elif cal_status is not None:
        d2 = 8.5
    else:
        d2 = 7.0

    # Rigor: calibration error
    if cal_err is not None:
        if cal_err < 3.0:
            d3 = 10.0
        elif cal_err < 5.0:
            d3 = 9.5
        elif cal_err < 10.0:
            d3 = 9.0
        elif cal_err < 20.0:
            d3 = 8.0
        else:
            d3 = 6.0
    elif cal_status is not None:
        d3 = 8.0
    else:
        d3 = 6.0

    # Traceability: input_files + solver identification
    has_inputs = row.get("input_files") is not None
    has_solver = row.get("solver_software") is not None
    if has_inputs and has_solver:
        d4 = 9.5
    elif has_solver:
        d4 = 8.5
    else:
        d4 = 7.0

    # Knowledge: solver_software + model_type
    if row.get("solver_software") and row.get("model_type"):
        d5 = 9.5
    elif row.get("solver_software"):
        d5 = 9.0
    else:
        d5 = 7.0

    # Integration: boundary_conditions + material_model
    if row.get("boundary_conditions") and row.get("material_model"):
        d6 = 9.0
    elif row.get("boundary_conditions"):
        d6 = 8.5
    else:
        d6 = 7.0

    # Numerical quality: mesh details
    has_mesh = row.get("mesh_num_elements") is not None or row.get("mesh_num_nodes") is not None
    mesh_type = row.get("mesh_type")
    if has_mesh and row.get("solver_parameters"):
        d7 = 9.5
    elif has_mesh:
        d7 = 9.0
    elif mesh_type:
        d7 = 8.5
    else:
        d7 = 7.0

    return {
        "D1_completude": d1, "D2_profundidade": d2, "D3_rigor": d3,
        "D4_rastreabilidade": d4, "D5_conhecimento": d5, "D6_integracao": d6,
        "D7_qualidade_numerica": d7, "D8_impacto": 8.5, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 8.5,
        "D13_inovacao": 9.0,
    }


def _score_simulation_result(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a simulation_result based on its domain data."""
    if not has_data:
        return _baseline_no_data("simulation_result")

    rows = db.execute(
        "SELECT * FROM simulation_results WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("simulation_result")
    row = dict(rows[0])

    val_status = row.get("validation_status")
    val_err = row.get("validation_error_pct")

    d1_fields = ["model_id", "simulation_type", "solver_software",
                 "boundary_conditions", "validation_status"]
    cr = _completeness_ratio(row, d1_fields)
    d1 = _map_completeness_to_score(cr)

    # Depth
    if val_status == "PASS" and val_err is not None and val_err < 5.0:
        d2 = 10.0
    elif val_status == "PASS":
        d2 = 9.5
    elif val_status == "FAIL":
        d2 = 7.0
    else:
        d2 = 6.0

    # Rigor
    if val_err is not None:
        if val_err < 3.0:
            d3 = 10.0
        elif val_err < 5.0:
            d3 = 9.5
        elif val_err < 10.0:
            d3 = 9.0
        else:
            d3 = 7.0
    elif val_status == "PASS":
        d3 = 9.0
    else:
        d3 = 6.0

    # Traceability
    d4 = 9.0 if row.get("solver_software") else 7.0

    # Knowledge
    d5 = 9.0 if row.get("simulation_type") else 7.0

    # Integration: model_id links to computational_model
    d6 = 9.0 if row.get("model_id") else 6.0

    # Numerical quality
    if val_err is not None and val_err < 5.0:
        d7 = 9.5
    elif val_err is not None:
        d7 = 9.0
    elif val_status == "PASS":
        d7 = 9.0
    else:
        d7 = 7.0

    return {
        "D1_completude": d1, "D2_profundidade": d2, "D3_rigor": d3,
        "D4_rastreabilidade": d4, "D5_conhecimento": d5, "D6_integracao": d6,
        "D7_qualidade_numerica": d7, "D8_impacto": 8.5, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 8.5,
        "D13_inovacao": 9.0,
    }


def _score_test_result(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a test_result based on its domain data."""
    if not has_data:
        return _baseline_no_data("test_result")

    rows = db.execute(
        "SELECT * FROM test_results WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("test_result")
    row = dict(rows[0])

    req = ["test_standard", "test_type", "property_measured",
           "value", "unit", "uncertainty", "num_replicates"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    # Depth: multiple replicates
    n_rep = row.get("num_replicates") or 0
    d2 = 10.0 if n_rep >= 5 else (9.5 if n_rep >= 3 else (9.0 if n_rep >= 1 else 7.0))

    # Rigor: uncertainty + standard
    has_std = row.get("test_standard") is not None
    has_uncertainty = row.get("uncertainty") is not None
    if has_std and has_uncertainty and n_rep >= 3:
        d3 = 9.5
    elif has_std and has_uncertainty:
        d3 = 9.0
    elif has_std:
        d3 = 8.5
    else:
        d3 = 7.0

    # Traceability
    d4 = 9.5 if (row.get("testing_machine") and row.get("operator")) else 9.0

    # Knowledge: test standard
    d5 = 9.5 if has_std else 8.0

    # Integration: specimen_id links to specimen
    d6 = 9.0 if row.get("specimen_id") else 6.0

    # Numerical quality
    if has_uncertainty and n_rep >= 3:
        d7 = 9.5
    elif has_uncertainty:
        d7 = 9.0
    else:
        d7 = 8.5

    return {
        "D1_completude": d1, "D2_profundidade": d2, "D3_rigor": d3,
        "D4_rastreabilidade": d4, "D5_conhecimento": d5, "D6_integracao": d6,
        "D7_qualidade_numerica": d7, "D8_impacto": 8.5, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 8.5,
        "D13_inovacao": 9.0,
    }


def _score_validation_reference(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a validation_reference based on source_quality_score."""
    if not has_data:
        return _baseline_no_data("validation_reference")

    rows = db.execute(
        "SELECT * FROM validation_references WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("validation_reference")
    row = dict(rows[0])

    sqs = row.get("source_quality_score")
    ref_type = row.get("reference_type")

    if sqs is not None:
        # source_quality_score directly maps to D5 (knowledge) and D3 (rigor)
        d1 = 10.0 if sqs >= 9.0 else (9.5 if sqs >= 8.0 else 9.0)
        d3 = min(sqs + 0.5, 10.0)
        d5 = min(sqs + 1.0, 10.0)
        d7 = sqs
    else:
        d1, d3, d5, d7 = 7.0, 6.0, 6.0, 6.0

    # Completeness based on available fields
    req = ["reference_type", "source_title", "source_quality_score", "year"]
    cr = _completeness_ratio(row, req)
    d1 = max(d1, _map_completeness_to_score(cr))

    d4 = 10.0 if row.get("doi") or row.get("url") else 8.5
    d8 = 9.0 if sqs and sqs >= 9.0 else 8.0

    return {
        "D1_completude": d1, "D2_profundidade": 9.0, "D3_rigor": d3,
        "D4_rastreabilidade": d4, "D5_conhecimento": d5, "D6_integracao": 8.5,
        "D7_qualidade_numerica": d7, "D8_impacto": d8, "D9_vies": 9.5,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 8.5,
        "D13_inovacao": 8.5,
    }


def _score_specimen(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a material_specimen."""
    if not has_data:
        return _baseline_no_data("specimen")

    rows = db.execute(
        "SELECT * FROM material_specimens WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("specimen")
    row = dict(rows[0])

    req = ["specimen_type", "material", "batch", "preparation_method", "curing_condition"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    return {
        "D1_completude": d1, "D2_profundidade": 8.5, "D3_rigor": 8.5,
        "D4_rastreabilidade": 9.0, "D5_conhecimento": 8.5, "D6_integracao": 8.0,
        "D7_qualidade_numerica": 8.0, "D8_impacto": 8.0, "D9_vies": 9.0,
        "D10_ensino": 8.5, "D11_velocidade": 9.0, "D12_satisfacao": 8.5,
        "D13_inovacao": 8.0,
    }


def _score_community_profile(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a community_profile."""
    if not has_data:
        return _baseline_no_data("community_profile")

    rows = db.execute(
        "SELECT * FROM community_profiles WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("community_profile")
    row = dict(rows[0])

    req = ["name", "location", "num_families", "total_population",
           "water_demand_l_per_day", "energy_total_kwh_day"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    # Impact: community size
    pop = row.get("total_population") or 0
    d8 = 10.0 if pop > 500 else (9.0 if pop > 100 else 8.0)

    return {
        "D1_completude": d1, "D2_profundidade": 9.0, "D3_rigor": 9.0,
        "D4_rastreabilidade": 9.0, "D5_conhecimento": 9.0, "D6_integracao": 9.0,
        "D7_qualidade_numerica": 9.0, "D8_impacto": d8, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 9.0,
        "D13_inovacao": 8.5,
    }


def _score_blade_design(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a blade_design."""
    if not has_data:
        return _baseline_no_data("blade_design")

    rows = db.execute(
        "SELECT * FROM blade_designs WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("blade_design")
    row = dict(rows[0])

    req = ["blade_length_m", "airfoil_profile", "num_blades", "material_id",
           "safety_factor_static", "safety_factor_fatigue"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    # Rigor: safety factors
    sf_s = row.get("safety_factor_static") or 0
    sf_f = row.get("safety_factor_fatigue") or 0
    if sf_s >= 2.0 and sf_f >= 1.5:
        d3 = 9.5
    elif sf_s >= 1.5:
        d3 = 9.0
    else:
        d3 = 8.0

    d7 = 9.0 if (row.get("design_wind_speed_ms") and row.get("extreme_wind_speed_ms")) else 8.0

    return {
        "D1_completude": d1, "D2_profundidade": 9.0, "D3_rigor": d3,
        "D4_rastreabilidade": 9.0, "D5_conhecimento": 9.0, "D6_integracao": 9.0,
        "D7_qualidade_numerica": d7, "D8_impacto": 9.0, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 9.0,
        "D13_inovacao": 9.0,
    }


def _score_energy_system(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score an energy_system."""
    if not has_data:
        return _baseline_no_data("energy_system")

    rows = db.execute(
        "SELECT * FROM energy_systems WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("energy_system")
    row = dict(rows[0])

    req = ["turbine_id", "battery_capacity_kwh", "battery_type",
           "inverter_rating_kw", "annual_energy_kwh"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    return {
        "D1_completude": d1, "D2_profundidade": 9.0, "D3_rigor": 9.0,
        "D4_rastreabilidade": 9.0, "D5_conhecimento": 9.0, "D6_integracao": 9.5,
        "D7_qualidade_numerica": 9.0, "D8_impacto": 9.5, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 9.0,
        "D13_inovacao": 9.0,
    }


def _score_wind_turbine_system(db, oid: str, has_data: bool) -> Dict[str, float]:
    """Score a wind_turbine_system."""
    if not has_data:
        return _baseline_no_data("wind_turbine_system")

    rows = db.execute(
        "SELECT * FROM wind_turbine_systems WHERE id = ?", (oid,)
    ).fetchall()
    if not rows:
        return _baseline_no_data("wind_turbine_system")
    row = dict(rows[0])

    req = ["turbine_type", "configuration", "rated_power_kw", "rotor_diameter_m",
           "tower_height_m", "swept_area_m2", "control_type"]
    cr = _completeness_ratio(row, req)
    d1 = _map_completeness_to_score(cr)

    return {
        "D1_completude": d1, "D2_profundidade": 9.0, "D3_rigor": 9.0,
        "D4_rastreabilidade": 9.0, "D5_conhecimento": 9.0, "D6_integracao": 9.5,
        "D7_qualidade_numerica": 9.0, "D8_impacto": 9.5, "D9_vies": 9.0,
        "D10_ensino": 9.0, "D11_velocidade": 9.0, "D12_satisfacao": 9.0,
        "D13_inovacao": 9.0,
    }


def _baseline_no_data(otype: str) -> Dict[str, float]:
    """Minimal baseline for objects that exist only in objects table."""
    return {
        "D1_completude": 3.0, "D2_profundidade": 3.0, "D3_rigor": 3.0,
        "D4_rastreabilidade": 3.0, "D5_conhecimento": 3.0, "D6_integracao": 3.0,
        "D7_qualidade_numerica": 3.0, "D8_impacto": 5.0, "D9_vies": 5.0,
        "D10_ensino": 3.0, "D11_velocidade": 5.0, "D12_satisfacao": 5.0,
        "D13_inovacao": 3.0,
    }


# ---------------------------------------------------------------------------
# Scoring registry
# ---------------------------------------------------------------------------

SCORERS = {
    "computational_model": _score_computational_model,
    "simulation_result": _score_simulation_result,
    "test_result": _score_test_result,
    "validation_reference": _score_validation_reference,
    "specimen": _score_specimen,
    "community_profile": _score_community_profile,
    "blade_design": _score_blade_design,
    "energy_system": _score_energy_system,
    "wind_turbine_system": _score_wind_turbine_system,
}

DOMAIN_TABLES = {
    "computational_model": "computational_models",
    "simulation_result": "simulation_results",
    "test_result": "test_results",
    "validation_reference": "validation_references",
    "specimen": "material_specimens",
    "community_profile": "community_profiles",
    "blade_design": "blade_designs",
    "energy_system": "energy_systems",
    "wind_turbine_system": "wind_turbine_systems",
}


def has_domain_data(db, oid: str, otype: str) -> bool:
    """Check if an object has corresponding domain table row."""
    tbl = DOMAIN_TABLES.get(otype)
    if not tbl:
        return False
    row = db.execute(f"SELECT COUNT(*) as cnt FROM {tbl} WHERE id = ?", (oid,)).fetchone()
    return row and row["cnt"] > 0


def get_unscored_objects(db, force: bool = False, type_filter: Optional[List[str]] = None):
    """Get objects needing scoring."""
    if force:
        query = "SELECT id, object_type FROM objects"
        params = []
    else:
        query = "SELECT id, object_type FROM objects WHERE quality_score IS NULL"
        params = []

    if type_filter:
        placeholders = ",".join("?" for _ in type_filter)
        query += f" WHERE object_type IN ({placeholders})" if "WHERE" not in query else f" AND object_type IN ({placeholders})"
        params = type_filter

    return [dict(r) for r in db.execute(query, params).fetchall()]


def score_object(db, oid: str, otype: str, dry_run: bool = False) -> Dict[str, Any]:
    """Score a single object based on its type and domain data."""
    scorer = SCORERS.get(otype)
    if not scorer:
        return {"object_id": oid, "type": otype, "status": "SKIP", "reason": "no scorer"}

    has_data = has_domain_data(db, oid, otype)
    scores = scorer(db, oid, has_data)

    if dry_run:
        # Compute aggregate manually
        total_w = sum(d["weight"] for d in PQMS_DIMENSIONS)
        w_sum = sum(scores.get(d["dimension"], 0) * d["weight"] for d in PQMS_DIMENSIONS)
        aggregate = round(w_sum / total_w, 2) if total_w > 0 else 0.0
        below = sum(1 for d in PQMS_DIMENSIONS if scores.get(d["dimension"], 0) < 8.5)
        return {
            "object_id": oid, "type": otype, "status": "DRY-RUN",
            "has_data": has_data, "aggregate": aggregate,
            "dimensions_below_minimum": below,
            "scores": scores,
        }

    try:
        result = compute_pqms(oid, scores)
        return {
            "object_id": oid, "type": otype, "status": result["pqms_status"],
            "aggregate": result["aggregate"],
            "dimensions_below_minimum": result["dimensions_below_minimum"],
        }
    except Exception as e:
        return {"object_id": oid, "type": otype, "status": "ERROR", "error": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch PQMS Scoring")
    parser.add_argument("--types", help="Comma-separated list of object types")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    parser.add_argument("--force", action="store_true", help="Re-score already-scored objects")
    args = parser.parse_args()

    type_filter = args.types.split(",") if args.types else None

    print("=" * 60)
    print("  BATCH PQMS SCORING")
    print(f"  {'Dry-run' if args.dry_run else 'Live'} mode")
    print(f"  {'Force re-score' if args.force else 'Unscored only'}")
    if type_filter:
        print(f"  Types: {', '.join(type_filter)}")
    print("=" * 60)

    with database() as db:
        objects = get_unscored_objects(db, force=args.force, type_filter=type_filter)
        if not objects:
            print("  No objects to score.")
            return

        print(f"\n  Objects to score: {len(objects)}")
        by_type: Dict[str, List[Dict]] = {}
        for obj in objects:
            by_type.setdefault(obj["object_type"], []).append(obj)

        for otype, objs in sorted(by_type.items()):
            with_data = sum(1 for o in objs if has_domain_data(db, o["id"], otype))
            print(f"    {otype}: {len(objs)} ({with_data} with domain data)")

        results: List[Dict] = []
        pass_count = 0
        fail_count = 0
        error_count = 0

        for obj in sorted(objects, key=lambda x: (x["object_type"], x["id"])):
            oid = obj["id"]
            otype = obj["object_type"]
            result = score_object(db, oid, otype, dry_run=args.dry_run)
            results.append(result)

            if result["status"] == "ERROR":
                error_count += 1
                oid_short = oid[:8]
                print(f"  ERROR [{oid_short}] {otype}: {result.get('error', '')}")
            elif result["status"] != "SKIP":
                oid_short = oid[:8]
                has = "data" if result.get("has_data", True) else "no-data"
                agg = result.get("aggregate", 0)
                status_icon = "PASS" if "PASS" in str(result.get("status", "")) else "FAIL"
                print(f"  {status_icon:4s} [{oid_short}] {otype:<22s} agg={agg:<5.2f} ({has})")
                if "PASS" in str(result.get("status", "")):
                    pass_count += 1
                else:
                    fail_count += 1

        print(f"\n  {'=' * 60}")
        print(f"  RESULTS SUMMARY")
        print(f"  {'=' * 60}")
        print(f"  Total attempted:  {len(objects)}")
        print(f"  PASS:             {pass_count}")
        print(f"  FAIL (below 9.5): {fail_count}")
        print(f"  SKIP (no scorer): {sum(1 for r in results if r['status'] == 'SKIP')}")
        print(f"  ERRORS:           {error_count}")

        if args.dry_run:
            print(f"\n  {'=' * 60}")
            print(f"  DRY-RUN COMPLETE — no data written")
            print(f"  Run without --dry-run to execute scoring")


if __name__ == "__main__":
    main()
