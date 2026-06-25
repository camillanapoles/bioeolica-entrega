#!/usr/bin/env python3
"""
Data Export Utility — Structured Queries for Composite Biomaterial for Wind Energy.

Supports filtering objects by object_type, timestamp range, quality_score range,
and validation_status. Exports to JSON or CSV format.

Usage:
    from src.03-data-management.etl.export_queries import export_objects

    data = export_objects(object_type="specimen", format="json")
    data = export_objects(quality_score_min=9.0, format="csv")
"""
import csv
import io
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database


def export_objects(
    object_type: Optional[str] = None,
    validation_status: Optional[str] = None,
    quality_score_min: Optional[float] = None,
    quality_score_max: Optional[float] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    tag_filter: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    format: str = "json",  # noqa: A002
    include_entity_data: bool = False,
) -> Any:
    """Query objects with filters and export to JSON or CSV.

    Args:
        object_type: Filter by object_type (e.g. 'specimen', 'test_result').
        validation_status: Filter by validation_status ('PENDING', 'PASS', 'FAIL').
        quality_score_min: Minimum quality_score (inclusive).
        quality_score_max: Maximum quality_score (inclusive).
        created_after: ISO 8601 start date (inclusive).
        created_before: ISO 8601 end date (inclusive).
        tag_filter: Search tag substring match.
        limit: Maximum results (default 1000).
        offset: Pagination offset.
        format: Output format — 'json' (default) or 'csv'.
        include_entity_data: If True, fetch entity-specific fields.

    Returns:
        For JSON: list of dicts. For CSV: CSV string.
    """
    conditions = ["1=1"]
    params = []

    if object_type:
        conditions.append("o.object_type = ?")
        params.append(object_type)
    if validation_status:
        conditions.append("o.validation_status = ?")
        params.append(validation_status)
    if quality_score_min is not None:
        conditions.append("o.quality_score >= ?")
        params.append(quality_score_min)
    if quality_score_max is not None:
        conditions.append("o.quality_score <= ?")
        params.append(quality_score_max)
    if created_after:
        conditions.append("o.created_at >= ?")
        params.append(created_after)
    if created_before:
        conditions.append("o.created_at <= ?")
        params.append(created_before)
    if tag_filter:
        conditions.append("o.tags LIKE ?")
        params.append(f"%{tag_filter}%")

    where = " AND ".join(conditions)

    with database() as db:
        rows = db.execute(
            f"""SELECT o.id, o.object_type, o.created_at, o.updated_at,
                       o.tags, o.metadata, o.quality_score, o.validation_status
                FROM objects o
                WHERE {where}
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()

    results = []
    for row in rows:
        obj = dict(row)
        # Parse JSON fields
        if isinstance(obj.get("tags"), str):
            try:
                obj["tags"] = json.loads(obj["tags"])
            except (json.JSONDecodeError, TypeError):
                pass
        if isinstance(obj.get("metadata"), str):
            try:
                obj["metadata"] = json.loads(obj["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(obj)

    if include_entity_data and results:
        results = _enrich_with_entity_data(results)

    if format == "csv":
        return _to_csv(results)
    return results


def _enrich_with_entity_data(objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich objects with entity-specific fields from child tables."""
    enriched = []
    with database() as db:
        for obj in objects:
            oid = obj["id"]
            otype = obj["object_type"]

            if otype == "specimen":
                row = db.execute(
                    "SELECT specimen_type, paper_type, binder_type, binder_ratio, "
                    "graphite_grade, coating_thickness_mm, geometry_type "
                    "FROM material_specimens WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "test_result":
                row = db.execute(
                    "SELECT test_type, test_standard, property_measured, value, unit, "
                    "uncertainty, specimen_id "
                    "FROM test_results WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "simulation_result":
                row = db.execute(
                    "SELECT model_id, convergence_metric, mesh_convergence_pct, "
                    "validation_status, validation_error_pct "
                    "FROM simulation_results WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "computational_model":
                row = db.execute(
                    "SELECT model_type, domain, solver_software, solver_version, "
                    "calibration_status, calibration_error_pct "
                    "FROM computational_models WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "blade_design":
                row = db.execute(
                    "SELECT blade_length_m, airfoil_profile, num_blades, "
                    "safety_factor_static, safety_factor_fatigue "
                    "FROM blade_designs WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "wind_turbine_system":
                row = db.execute(
                    "SELECT turbine_type, rated_power_kw, rotor_diameter_m, "
                    "cut_in_speed_ms, rated_wind_speed_ms "
                    "FROM wind_turbine_systems WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "energy_system":
                row = db.execute(
                    "SELECT battery_capacity_kwh, inverter_rating_kw, lcoe_usd_per_kwh, "
                    "capacity_factor_pct, autonomy_days "
                    "FROM energy_systems WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "community_profile":
                row = db.execute(
                    "SELECT name, num_families, energy_total_kwh_day, "
                    "irrigated_area_ha, growth_margin_pct "
                    "FROM community_profiles WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            elif otype == "validation_reference":
                row = db.execute(
                    "SELECT source_type, title, authors, year, source_quality_score "
                    "FROM validation_references WHERE id = ?",
                    (oid,),
                ).fetchone()
                if row:
                    obj["entity_data"] = dict(row)

            enriched.append(obj)
    return enriched


def _to_csv(objects: List[Dict[str, Any]]) -> str:
    """Convert list of dicts to CSV string."""
    if not objects:
        return ""

    output = io.StringIO()
    # Flatten nested data for CSV
    flat_rows = []
    for obj in objects:
        flat = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v
        flat_rows.append(flat)

    writer = csv.DictWriter(output, fieldnames=flat_rows[0].keys())
    writer.writeheader()
    writer.writerows(flat_rows)
    return output.getvalue()


def export_quality_scores(
    object_id: Optional[str] = None,
    dimension: Optional[str] = None,
    score_min: Optional[float] = None,
    format: str = "json",  # noqa: A002
) -> Any:
    """Export quality_scores with optional filters.

    Args:
        object_id: Filter by object UUID.
        dimension: Filter by dimension name.
        score_min: Minimum score filter.
        format: 'json' or 'csv'.

    Returns:
        Filtered quality score records.
    """
    conditions = ["1=1"]
    params = []

    if object_id:
        conditions.append("qs.object_id = ?")
        params.append(object_id)
    if dimension:
        conditions.append("qs.dimension = ?")
        params.append(dimension)
    if score_min is not None:
        conditions.append("qs.score >= ?")
        params.append(score_min)

    where = " AND ".join(conditions)
    with database() as db:
        rows = db.execute(
            f"""SELECT qs.*, dw.target, dw.measurement_method
                FROM quality_scores qs
                JOIN pqms_dimension_weights dw ON qs.dimension = dw.dimension
                WHERE {where}
                ORDER BY qs.object_id, qs.dimension""",
            params,
        ).fetchall()

    results = [dict(r) for r in rows]

    if format == "csv":
        return _to_csv(results)
    return results


def export_provenance_chain(
    object_id: str,
    direction: str = "both",
    format: str = "json",  # noqa: A002
) -> Any:
    """Export provenance chain for an object.

    Args:
        object_id: UUID of the object to trace.
        direction: 'upstream', 'downstream', or 'both'.
        format: 'json' or 'csv'.

    Returns:
        Provenance chain data.
    """
    from src.common.provenance import get_upstream, get_downstream

    result = {"object_id": object_id}

    if direction in ("upstream", "both"):
        result["upstream"] = get_upstream(object_id)
        result["upstream_count"] = len({e["source_id"] for e in result["upstream"]})

    if direction in ("downstream", "both"):
        result["downstream"] = get_downstream(object_id)
        result["downstream_count"] = len({e["target_id"] for e in result["downstream"]})

    if format == "csv":
        rows = []
        for key in ("upstream", "downstream"):
            for edge in result.get(key, []):
                edge["direction"] = key
                rows.append(edge)
        return _to_csv(rows)

    return result


def main() -> None:
    """CLI entry point for data export."""
    import argparse

    parser = argparse.ArgumentParser(description="Export data from bioeolica.db")
    parser.add_argument("--object-type", help="Filter by object type")
    parser.add_argument("--validation-status", choices=["PENDING", "PASS", "FAIL"])
    parser.add_argument("--quality-min", type=float, help="Minimum quality score")
    parser.add_argument("--quality-max", type=float, help="Maximum quality score")
    parser.add_argument("--created-after", help="ISO 8601 start date")
    parser.add_argument("--created-before", help="ISO 8601 end date")
    parser.add_argument("--tag", help="Tag substring filter")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--include-entity-data", action="store_true",
                        help="Include entity-specific fields")
    parser.add_argument("--export-scores", action="store_true",
                        help="Export quality scores instead of objects")
    parser.add_argument("--score-dimension", help="Filter scores by dimension")
    parser.add_argument("--score-min", type=float, help="Minimum score value")
    parser.add_argument("--provenance", help="Export provenance chain for object UUID")

    args = parser.parse_args()

    if args.provenance:
        data = export_provenance_chain(args.provenance, format=args.format)
        _output(data, args.format)
        return

    if args.export_scores:
        data = export_quality_scores(
            object_id=args.object_type,  # reuse as object_id filter
            dimension=args.score_dimension,
            score_min=args.score_min,
            format=args.format,
        )
        _output(data, args.format)
        return

    data = export_objects(
        object_type=args.object_type,
        validation_status=args.validation_status,
        quality_score_min=args.quality_min,
        quality_score_max=args.quality_max,
        created_after=args.created_after,
        created_before=args.created_before,
        tag_filter=args.tag,
        limit=args.limit,
        offset=args.offset,
        format=args.format,
        include_entity_data=args.include_entity_data,
    )
    _output(data, args.format)


def _output(data: Any, fmt: str) -> None:
    """Print data to stdout."""
    if fmt == "csv":
        print(data)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
