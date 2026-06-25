#!/usr/bin/env python3
"""
T039 — Blade Design Registration into SQLite.

Registers the wind turbine blade design in the bioeolica.db database.
Creates an entry in the ``objects`` registry and a corresponding record
in the ``blade_designs`` table with all IEC 61400-2 parameters.

Usage:
    python src/02-wind-energy/structural/register_blade.py

References:
    - contracts/schema-entities.sql for blade_designs DDL
    - src/common/registry.py for create_object / get_object API
    - src/02-wind-energy/structural/blade_geometry.py for geometry
"""
from __future__ import annotations

import sys
from typing import Optional

_project_root: str = __file__
for _ in range(4):
    _project_root = _project_root.rpartition("/")[0]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError
from src.common.registry import create_object, get_object, ObjectNotFound
from src.common.provenance import record_edge

# ------------------------------------------------------------------
# Design parameters (from blade_geometry.py + US2 spec)
# ------------------------------------------------------------------

BLADE_LENGTH_M: float = 3.5
AIRFOIL_PROFILE: str = "NACA 0018"
NUM_BLADES: int = 3
MATERIAL_ID: str = ""       # Set at runtime via --material-id or env

# IEC 61400-2 design wind speeds
DESIGN_WIND_SPEED_MS: float = 8.0
EXTREME_WIND_SPEED_MS: float = 40.0

# Safety factors (initial PENDING, updated after FEM analysis)
SAFETY_FACTOR_STATIC: float = 2.5   # Target >= 2.0 per IEC 61400-2
SAFETY_FACTOR_FATIGUE: float = 2.0  # Target >= 2.0

# Geometry reference
GEOMETRY_FILE: str = "data/geometry/blade_3.5m.stp"

# Blade mass estimate (from T043 cost estimation)
BLADE_MASS_KG: float = 12.10

BLADE_DESIGN_COLS: list[str] = [
    "id", "blade_length_m", "airfoil_profile", "num_blades",
    "material_id", "structural_layup",
    "safety_factor_static", "safety_factor_fatigue",
    "design_wind_speed_ms", "extreme_wind_speed_ms",
    "mass_kg", "geometry_file", "created_at",
]


def register_blade_design(material_id: str) -> str:
    """Register the wind turbine blade design.

    Steps:
        1. Create an object in the registry with tags
           ``["blade_design", "naca_0018", "paper_mache_graphite"]``.
        2. Insert the corresponding row into ``blade_designs``.
        3. Record a provenance edge from material to blade.

    Args:
        material_id: UUID of the composite material specimen to link.

    Returns:
        The UUID v4 string assigned to the blade design.

    Raises:
        DatabaseError: If registration fails.
    """
    obj_id: str = create_object(
        "blade_design",
        tags=["blade_design", "naca_0018", "paper_mache_graphite"],
        metadata={
            "airfoil": AIRFOIL_PROFILE,
            "blade_length_m": BLADE_LENGTH_M,
            "num_blades": NUM_BLADES,
            "design_standard": "IEC 61400-2",
        },
    )

    with database() as db:
        db.execute(
            """INSERT INTO blade_designs
               (id, blade_length_m, airfoil_profile, num_blades,
                material_id, structural_layup,
                safety_factor_static, safety_factor_fatigue,
                design_wind_speed_ms, extreme_wind_speed_ms,
                mass_kg, geometry_file, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       datetime('now'))""",
            (
                obj_id,
                BLADE_LENGTH_M,
                AIRFOIL_PROFILE,
                NUM_BLADES,
                material_id,
                "Paper mache substrate + graphite coating; "
                "chord 0.35m(root)-0.12m(tip); twist 12 deg-2 deg",
                SAFETY_FACTOR_STATIC,
                SAFETY_FACTOR_FATIGUE,
                DESIGN_WIND_SPEED_MS,
                EXTREME_WIND_SPEED_MS,
                BLADE_MASS_KG,
                GEOMETRY_FILE,
            ),
        )
        db.commit()

    # Record provenance: material → blade design
    record_edge(
        source_id=material_id,
        target_id=obj_id,
        transformation="material_to_blade_design",
        parameters={"airfoil": AIRFOIL_PROFILE, "blade_length_m": BLADE_LENGTH_M},
    )

    return obj_id


def blade_design_exists(design_id: str) -> bool:
    """Check whether a blade design UUID exists in the registry.

    Args:
        design_id: UUID v4 string.

    Returns:
        ``True`` if a corresponding ``objects`` row exists.
    """
    try:
        get_object(design_id)
        return True
    except ObjectNotFound:
        return False


def print_design_summary(design_id: str) -> None:
    """Print a readable summary of a registered blade design."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    print(f"\n{CYAN}>>> Blade Design Summary{RESET}")
    print(f"  UUID : {design_id}")

    try:
        obj = get_object(design_id)
        print(f"  Tags : {', '.join(obj.get('tags', []))}")
    except ObjectNotFound:
        print(f"  Registry lookup: {GREEN}NOT FOUND{RESET}")

    with database() as db:
        row = db.execute(
            "SELECT blade_length_m, airfoil_profile, num_blades, "
            "       safety_factor_static, safety_factor_fatigue, "
            "       design_wind_speed_ms, extreme_wind_speed_ms, "
            "       mass_kg, geometry_file, created_at "
            "FROM blade_designs WHERE id = ?",
            (design_id,),
        ).fetchone()

    if row:
        d = dict(row)
        print(f"  Airfoil : {d['airfoil_profile']}")
        print(f"  Length  : {d['blade_length_m']} m  |  Blades: {d['num_blades']}")
        print(f"  Mass    : {d['mass_kg']} kg")
        print(f"  Design  : {d['design_wind_speed_ms']} m/s  |  "
              f"Extreme: {d['extreme_wind_speed_ms']} m/s")
        print(f"  SF stat : {d['safety_factor_static']:.1f}  |  "
              f"SF fatig: {d['safety_factor_fatigue']:.1f}")
        print(f"  Created : {d['created_at']}")
    else:
        print(f"  {GREEN}No blade_designs record found.{RESET}")


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Register blade design in SQLite"
    )
    parser.add_argument(
        "--material-id", required=True,
        help="UUID of the composite material specimen",
    )
    args = parser.parse_args()

    BLUE = "\033[94m"
    RESET = "\033[0m"

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}  BLADE DESIGN REGISTRATION{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    design_id = register_blade_design(args.material_id)
    print_design_summary(design_id)

    assert blade_design_exists(design_id), "Blade design should exist."
    print(f"\n  {BLUE}[OK]{RESET} Blade design verified in registry.")
    print(f"  Design ID : {design_id}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


if __name__ == "__main__":
    _main()
