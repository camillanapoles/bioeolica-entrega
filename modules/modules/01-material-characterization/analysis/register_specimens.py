#!/usr/bin/env python3
"""
T025 — Specimen Registration into SQLite.

Registers baseline (paper mache) and composite (paper mache + graphite)
specimens in the bioeolica.db database. Each registration creates an entry
in the ``objects`` registry and a corresponding record in the
``material_specimens`` table.

Usage:
    python src/01-material-characterization/analysis/register_specimens.py

References:
    - quickstart.md section 2.1 for parameter values
    - contracts/schema-entities.sql for table & constraint DDL
    - src/common/registry.py for create_object / get_object API
"""
from __future__ import annotations

import json
import sys
import uuid
from typing import Optional

_project_root: str = __file__
for _ in range(4):
    _project_root = _project_root.rpartition("/")[0]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, get_object, ObjectNotFound

# ------------------------------------------------------------------
# Production parameters (quickstart.md section 2.1)
# ------------------------------------------------------------------

PRODUCTION_DATE: str = "2026-06-01"

BASELINE_PARAMS: dict = {
    "specimen_type": "baseline",
    "paper_type": "newspaper",
    "binder_type": "PVA",
    "binder_ratio": "1:3",
    "curing_time_hours": 24.0,
    "curing_temp_c": 25.0,
    "geometry_type": "dogbone",
    "geometry_dimensions": json.dumps(
        {"length": 165, "width": 19, "thickness": 4}, separators=(",", ":")
    ),
    "production_date": PRODUCTION_DATE,
    "production_notes": "Baseline paper mache specimen — no graphite coating.",
    "storage_conditions": "25 deg C, 50% RH",
}

COMPOSITE_PARAMS: dict = {
    "specimen_type": "composite",
    "paper_type": "newspaper",
    "binder_type": "PVA",
    "binder_ratio": "1:3",
    "curing_time_hours": 24.0,
    "curing_temp_c": 25.0,
    "graphite_grade": "flake_industrial",
    "graphite_particle_size_um": 100.0,
    "blasting_pressure_bar": 4.0,
    "standoff_distance_mm": 150.0,
    "coating_thickness_mm": 0.5,
    "geometry_type": "dogbone",
    "geometry_dimensions": json.dumps(
        {"length": 165, "width": 19, "thickness": 4}, separators=(",", ":")
    ),
    "production_date": PRODUCTION_DATE,
    "production_notes": "Composite specimen — graphite-coated via pneumatic blasting.",
    "storage_conditions": "25 deg C, 50% RH",
}

MATERIAL_SPECIMEN_COLS: list[str] = [
    "id", "specimen_type", "paper_type", "binder_type", "binder_ratio",
    "curing_time_hours", "curing_temp_c", "graphite_grade",
    "graphite_particle_size_um", "blasting_pressure_bar",
    "standoff_distance_mm", "coating_thickness_mm", "geometry_type",
    "geometry_dimensions", "production_date", "production_notes",
    "storage_conditions",
]


# ------------------------------------------------------------------
# Registration functions
# ------------------------------------------------------------------

def register_baseline_specimen() -> str:
    """Register a baseline (paper mache) specimen.

    Steps:
        1. Create an object in the registry with tags ``["baseline", "paper_mache"]``.
        2. Insert the corresponding row into ``material_specimens``.

    Returns:
        The UUID v4 string assigned to the specimen.
    """
    obj_id: str = create_object(
        "specimen",
        tags=["baseline", "paper_mache"],
    )

    with database() as db:
        db.execute(
            """INSERT INTO material_specimens
               (id, specimen_type, paper_type, binder_type, binder_ratio,
                curing_time_hours, curing_temp_c,
                geometry_type, geometry_dimensions,
                production_date, production_notes, storage_conditions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj_id,
                BASELINE_PARAMS["specimen_type"],
                BASELINE_PARAMS["paper_type"],
                BASELINE_PARAMS["binder_type"],
                BASELINE_PARAMS["binder_ratio"],
                BASELINE_PARAMS["curing_time_hours"],
                BASELINE_PARAMS["curing_temp_c"],
                BASELINE_PARAMS["geometry_type"],
                BASELINE_PARAMS["geometry_dimensions"],
                BASELINE_PARAMS["production_date"],
                BASELINE_PARAMS["production_notes"],
                BASELINE_PARAMS["storage_conditions"],
            ),
        )
        db.commit()

    return obj_id


def register_composite_specimen() -> str:
    """Register a composite (paper mache + graphite) specimen.

    Steps:
        1. Create an object in the registry with
           tags ``["composite", "paper_mache", "graphite"]``.
        2. Insert the corresponding row into ``material_specimens`` with
           ALL fields, including graphite-related columns.

    Returns:
        The UUID v4 string assigned to the specimen.
    """
    obj_id: str = create_object(
        "specimen",
        tags=["composite", "paper_mache", "graphite"],
    )

    with database() as db:
        db.execute(
            """INSERT INTO material_specimens
               (id, specimen_type, paper_type, binder_type, binder_ratio,
                curing_time_hours, curing_temp_c,
                graphite_grade, graphite_particle_size_um,
                blasting_pressure_bar, standoff_distance_mm, coating_thickness_mm,
                geometry_type, geometry_dimensions,
                production_date, production_notes, storage_conditions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj_id,
                COMPOSITE_PARAMS["specimen_type"],
                COMPOSITE_PARAMS["paper_type"],
                COMPOSITE_PARAMS["binder_type"],
                COMPOSITE_PARAMS["binder_ratio"],
                COMPOSITE_PARAMS["curing_time_hours"],
                COMPOSITE_PARAMS["curing_temp_c"],
                COMPOSITE_PARAMS["graphite_grade"],
                COMPOSITE_PARAMS["graphite_particle_size_um"],
                COMPOSITE_PARAMS["blasting_pressure_bar"],
                COMPOSITE_PARAMS["standoff_distance_mm"],
                COMPOSITE_PARAMS["coating_thickness_mm"],
                COMPOSITE_PARAMS["geometry_type"],
                COMPOSITE_PARAMS["geometry_dimensions"],
                COMPOSITE_PARAMS["production_date"],
                COMPOSITE_PARAMS["production_notes"],
                COMPOSITE_PARAMS["storage_conditions"],
            ),
        )
        db.commit()

    return obj_id


def register_specimens() -> tuple[str, str]:
    """Register both baseline and composite specimens.

    Returns:
        A ``(baseline_uuid, composite_uuid)`` pair.
    """
    baseline_id: str = register_baseline_specimen()
    composite_id: str = register_composite_specimen()
    return baseline_id, composite_id


def specimen_exists(specimen_id: str) -> bool:
    """Check whether a specimen UUID exists in the registry.

    Args:
        specimen_id: UUID v4 string.

    Returns:
        ``True`` if a corresponding ``objects`` row exists.
    """
    try:
        get_object(specimen_id)
        return True
    except ObjectNotFound:
        return False


def print_specimen_summary(specimen_id: str, label: str) -> None:
    """Print a readable summary of a registered specimen."""
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    print(f"\n{CYAN}{label}{RESET}")
    print(f"  UUID : {specimen_id}")

    try:
        obj = get_object(specimen_id)
        print(f"  Tags : {', '.join(obj.get('tags', []))}")
    except ObjectNotFound:
        print(f"  Registry lookup: {GREEN}NOT FOUND{RESET}")

    with database() as db:
        row = db.execute(
            "SELECT specimen_type, paper_type, binder_type, binder_ratio, "
            "       curing_time_hours, curing_temp_c, graphite_grade, "
            "       coating_thickness_mm, geometry_type, production_date "
            "FROM material_specimens WHERE id = ?",
            (specimen_id,),
        ).fetchone()

    if row:
        d = dict(row)
        print(f"  Type  : {d['specimen_type']}")
        print(f"  Paper : {d['paper_type']}  |  Binder: {d['binder_type']} ({d['binder_ratio']})")
        print(f"  Cure  : {d['curing_time_hours']}h @ {d['curing_temp_c']} deg C")
        if d["graphite_grade"]:
            print(f"  Coating: {d['graphite_grade']}  ({d['coating_thickness_mm']} mm)")
        print(f"  Geometry: {d['geometry_type']}  |  Date: {d['production_date']}")
    else:
        print(f"  {GREEN}No material_specimens record found.{RESET}")


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _main() -> None:
    BLUE = "\033[94m"
    RESET = "\033[0m"

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}  SPECIMEN REGISTRATION{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    baseline_id, composite_id = register_specimens()
    print_specimen_summary(baseline_id, ">>> Baseline specimen")
    print_specimen_summary(composite_id, ">>> Composite specimen")

    # Quick existence check
    assert specimen_exists(baseline_id), "Baseline specimen should exist."
    assert specimen_exists(composite_id), "Composite specimen should exist."
    print(f"\n  {BLUE}[OK]{RESET} Both specimens verified in registry.")

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"  Baseline ID : {baseline_id}")
    print(f"  Composite ID: {composite_id}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    _main()
