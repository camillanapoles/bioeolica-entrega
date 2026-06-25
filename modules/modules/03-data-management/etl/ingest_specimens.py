#!/usr/bin/env python3
"""
Material Specimen ETL Ingestion — Composite Biomaterial for Wind Energy.

Registers material specimens (baseline or composite) in the universal registry
(objects table) and inserts corresponding records in material_specimens with
full constraint validation at the application layer.

Usage:
    from src.03-data-management.etl.ingest_specimens import ingest_specimen

    obj = ingest_specimen(
        specimen_type="composite",
        paper_type="newspaper",
        binder_type="PVA",
        binder_ratio="1:3",
        curing_time_hours=24,
        curing_temp_c=25,
        geometry_type="dogbone",
        geometry_dimensions={"length": 165, "width": 19, "thickness": 4},
        production_date="2026-06-01",
        graphite_grade="flake_industrial",
        graphite_particle_size_um=100,
        blasting_pressure_bar=4.0,
        standoff_distance_mm=150,
        coating_thickness_mm=0.5,
    )
"""
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, get_object, ValidationError


class SpecimenIngestionError(ValueError):
    """Raised on invalid specimen data."""
    pass


# Valid specimen types
VALID_SPECIMEN_TYPES = {"baseline", "composite"}
VALID_PAPER_TYPES = {"newspaper", "office_paper", "mixed", "cardboard", "kraft"}
VALID_BINDER_TYPES = {"PVA", "starch", "latex", "acrylic"}
VALID_GEOMETRY_TYPES = {"dogbone", "rectangular", "circular", "custom"}


def _validate_specimen_data(data: Dict[str, Any]) -> None:
    """Validate specimen data against application-layer constraints.

    Raises SpecimenIngestionError on first violation.
    """
    errors = []

    # Required field checks
    required = ["specimen_type", "paper_type", "binder_type", "binder_ratio",
                "curing_time_hours", "curing_temp_c", "geometry_type",
                "geometry_dimensions", "production_date"]
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        raise SpecimenIngestionError("; ".join(errors))

    st = data["specimen_type"]
    if st not in VALID_SPECIMEN_TYPES:
        raise SpecimenIngestionError(
            f"Invalid specimen_type '{st}'. Must be one of: {sorted(VALID_SPECIMEN_TYPES)}"
        )
    if data["paper_type"] not in VALID_PAPER_TYPES:
        raise SpecimenIngestionError(
            f"Invalid paper_type '{data['paper_type']}'. Must be one of: {sorted(VALID_PAPER_TYPES)}"
        )
    if data["binder_type"] not in VALID_BINDER_TYPES:
        raise SpecimenIngestionError(
            f"Invalid binder_type '{data['binder_type']}'. Must be one of: {sorted(VALID_BINDER_TYPES)}"
        )
    if data["geometry_type"] not in VALID_GEOMETRY_TYPES:
        raise SpecimenIngestionError(
            f"Invalid geometry_type '{data['geometry_type']}'. Must be one of: {sorted(VALID_GEOMETRY_TYPES)}"
        )

    # Validation: curing parameters positive
    if data["curing_time_hours"] <= 0:
        errors.append("curing_time_hours must be > 0")
    if not (-50 < data["curing_temp_c"] < 200):
        errors.append("curing_temp_c must be between -50 and 200")

    # Validation: composite requires graphite fields
    if st == "composite":
        graphite_fields = {
            "graphite_grade": data.get("graphite_grade"),
            "blasting_pressure_bar": data.get("blasting_pressure_bar"),
            "coating_thickness_mm": data.get("coating_thickness_mm"),
        }
        missing = [k for k, v in graphite_fields.items() if v is None]
        if missing:
            errors.append(
                f"Composite specimens require graphite fields: {', '.join(missing)}"
            )

        # Validation: coating thickness <= 2.0mm
        ct = data.get("coating_thickness_mm")
        if ct is not None and ct > 2.0:
            errors.append(f"coating_thickness_mm must be <= 2.0, got {ct}")

        # Validation: blasting pressure 1-10 bar
        bp = data.get("blasting_pressure_bar")
        if bp is not None and not (1 <= bp <= 10):
            errors.append(f"blasting_pressure_bar must be between 1 and 10, got {bp}")

        # Validation: standoff distance 10-500mm
        sd = data.get("standoff_distance_mm")
        if sd is not None and not (10 <= sd <= 500):
            errors.append(f"standoff_distance_mm must be between 10 and 500, got {sd}")

        # Validation: particle size > 0
        ps = data.get("graphite_particle_size_um")
        if ps is not None and ps <= 0:
            errors.append("graphite_particle_size_um must be > 0")

    if errors:
        raise SpecimenIngestionError("; ".join(errors))


def ingest_specimen(
    specimen_type: str,
    paper_type: str,
    binder_type: str,
    binder_ratio: str,
    curing_time_hours: float,
    curing_temp_c: float,
    geometry_type: str,
    geometry_dimensions: Dict[str, float],
    production_date: str,
    graphite_grade: Optional[str] = None,
    graphite_particle_size_um: Optional[float] = None,
    blasting_pressure_bar: Optional[float] = None,
    standoff_distance_mm: Optional[float] = None,
    coating_thickness_mm: Optional[float] = None,
    production_notes: Optional[str] = None,
    storage_conditions: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register a material specimen in the universal registry and entity table.

    Args:
        specimen_type: 'baseline' or 'composite'.
        paper_type: e.g. 'newspaper', 'office_paper', 'mixed'.
        binder_type: e.g. 'PVA', 'starch'.
        binder_ratio: e.g. '1:3' (glue:water).
        curing_time_hours: Curing duration.
        curing_temp_c: Curing temperature in Celsius.
        geometry_type: e.g. 'dogbone', 'rectangular'.
        geometry_dimensions: Dict with length/width/thickness in mm.
        production_date: ISO 8601 date string.
        graphite_grade: Required for composite.
        graphite_particle_size_um: Mean particle size in microns.
        blasting_pressure_bar: Blasting pressure (1-10 bar).
        standoff_distance_mm: Nozzle standoff distance (10-500mm).
        coating_thickness_mm: Coating thickness (<= 2.0mm).
        production_notes: Optional free-text notes.
        storage_conditions: Optional storage condition description.
        tags: Optional list of search tags.
        metadata: Optional JSON-serializable metadata dict.

    Returns:
        Dict with 'object_id' (UUID), 'specimen_type', and 'status'.

    Raises:
        SpecimenIngestionError: On validation failure.
        ValidationError: On registry validation failure.
    """
    data = {k: v for k, v in locals().items() if k not in ("tags", "metadata")}
    _validate_specimen_data(data)

    dims_json = json.dumps(geometry_dimensions)

    # Register in universal registry
    object_id = create_object(
        object_type="specimen",
        tags=tags,
        metadata=metadata,
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with database() as db:
        db.execute(
            """INSERT INTO material_specimens
               (id, specimen_type, paper_type, binder_type, binder_ratio,
                curing_time_hours, curing_temp_c,
                graphite_grade, graphite_particle_size_um,
                blasting_pressure_bar, standoff_distance_mm, coating_thickness_mm,
                geometry_type, geometry_dimensions, production_date,
                production_notes, storage_conditions, quality_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                object_id, specimen_type, paper_type, binder_type, binder_ratio,
                curing_time_hours, curing_temp_c,
                graphite_grade, graphite_particle_size_um,
                blasting_pressure_bar, standoff_distance_mm, coating_thickness_mm,
                geometry_type, dims_json, production_date,
                production_notes, storage_conditions,
            ),
        )
        db.commit()

    return {
        "object_id": object_id,
        "specimen_type": specimen_type,
        "status": "registered",
    }


def list_specimens(specimen_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List registered material specimens.

    Args:
        specimen_type: Optional filter ('baseline' or 'composite').

    Returns:
        List of specimen dicts joined with objects data.
    """
    conditions = ["ms.id = o.id"]
    params = []
    if specimen_type:
        conditions.append("ms.specimen_type = ?")
        params.append(specimen_type)

    where = " AND ".join(conditions)
    with database() as db:
        rows = db.execute(
            f"""SELECT o.*, ms.specimen_type, ms.paper_type, ms.binder_type,
                       ms.binder_ratio, ms.graphite_grade, ms.coating_thickness_mm,
                       ms.geometry_type
                FROM material_specimens ms
                JOIN objects o ON {where}
                ORDER BY o.created_at DESC""",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def main() -> None:
    """CLI entry point for specimen ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest material specimen")
    parser.add_argument("--specimen-type", required=True, choices=["baseline", "composite"])
    parser.add_argument("--paper-type", required=True)
    parser.add_argument("--binder-type", required=True)
    parser.add_argument("--binder-ratio", required=True)
    parser.add_argument("--curing-time", type=float, required=True)
    parser.add_argument("--curing-temp", type=float, required=True)
    parser.add_argument("--geometry-type", required=True)
    parser.add_argument("--geometry-dimensions", required=True, help="JSON dict")
    parser.add_argument("--production-date", required=True)
    parser.add_argument("--graphite-grade")
    parser.add_argument("--particle-size-um", type=float)
    parser.add_argument("--blasting-pressure", type=float)
    parser.add_argument("--standoff-distance", type=float)
    parser.add_argument("--coating-thickness", type=float)
    parser.add_argument("--production-notes")
    parser.add_argument("--storage-conditions")
    parser.add_argument("--list", action="store_true", help="List registered specimens")

    args = parser.parse_args()

    if args.list:
        specimens = list_specimens()
        if specimens:
            print(f"Registered specimens ({len(specimens)}):")
            for s in specimens:
                print(f"  {s['id'][:8]}... [{s['specimen_type']}] paper={s['paper_type']}")
        else:
            print("No specimens registered.")
        return

    dims = json.loads(args.geometry_dimensions)

    result = ingest_specimen(
        specimen_type=args.specimen_type,
        paper_type=args.paper_type,
        binder_type=args.binder_type,
        binder_ratio=args.binder_ratio,
        curing_time_hours=args.curing_time,
        curing_temp_c=args.curing_temp,
        geometry_type=args.geometry_type,
        geometry_dimensions=dims,
        production_date=args.production_date,
        graphite_grade=args.graphite_grade,
        graphite_particle_size_um=args.particle_size_um,
        blasting_pressure_bar=args.blasting_pressure,
        standoff_distance_mm=args.standoff_distance,
        coating_thickness_mm=args.coating_thickness,
        production_notes=args.production_notes,
        storage_conditions=args.storage_conditions,
    )
    print(f"Specimen registered: {result['object_id']}")
    print(f"  Type: {result['specimen_type']}")


if __name__ == "__main__":
    main()
