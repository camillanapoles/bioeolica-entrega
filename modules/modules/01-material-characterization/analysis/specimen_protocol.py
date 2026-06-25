#!/usr/bin/env python3
"""
T024 — Specimen Production Protocol Definition.

Defines the standardised protocol dataclass for composite material specimen
production, including baseline (paper mache) and composite (paper mache +
graphite coating) variants. Provides validation logic and printable summaries.

References:
    - quickstart.md section 2.1 for protocol parameters
    - contracts/schema-entities.sql for material_specimens constraint rules
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_project_root: str = __file__
for _ in range(4):
    _project_root = _project_root.rpartition("/")[0]
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


DOGBONE_DIMENSIONS: dict = {
    "length": 165,
    "width": 19,
    "thickness": 4,
}


@dataclass(frozen=True)
class SpecimenProtocol:
    """Immutable record of specimen production parameters.

    Every field maps to a column in the ``material_specimens`` table. Optional
    fields (graphite-related) are ``None`` for baseline specimens and required
    for composite specimens per the schema CHECK constraint
    ``ck_composite_requires_graphite``.

    Attributes:
        paper_type:  fibre source, e.g. ``"newspaper"``.
        binder_type: adhesive chemistry, e.g. ``"PVA"``.
        binder_ratio: glue-to-water ratio as a string, e.g. ``"1:3"``.
        curing_time_hours: duration at curing temperature.
        curing_temp_c: ambient or oven temperature during cure.
        graphite_grade: e.g. ``"flake_industrial"`` (composite only).
        graphite_particle_size_um: mean particle diameter (composite only).
        blasting_pressure_bar: pneumatic blasting pressure (composite only).
        standoff_distance_mm: nozzle-to-surface distance (composite only).
        coating_thickness_mm: nominal graphite layer thickness (composite only).
        geometry_type: specimen shape, e.g. ``"dogbone"``.
        geometry_dimensions: ``dict`` with keys length / width / thickness (mm).
        production_notes: free-text process observations.
        storage_conditions: e.g. ``"25 deg C, 50% RH"``.
    """

    paper_type: str
    binder_type: str
    binder_ratio: str
    curing_time_hours: float
    curing_temp_c: float

    graphite_grade: Optional[str] = None
    graphite_particle_size_um: Optional[float] = None
    blasting_pressure_bar: Optional[float] = None
    standoff_distance_mm: Optional[float] = None
    coating_thickness_mm: Optional[float] = None

    geometry_type: str = "dogbone"
    geometry_dimensions: dict = field(default_factory=lambda: dict(DOGBONE_DIMENSIONS))
    production_notes: Optional[str] = None
    storage_conditions: Optional[str] = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def geometry_dimensions_json(self) -> str:
        """Return geometry_dimensions as a JSON string for DB insertion."""
        return json.dumps(self.geometry_dimensions, separators=(",", ":"))

    def summary(self, indent: int = 0) -> str:
        """Human-readable, multi-line summary of the protocol."""
        pad = " " * indent
        lines = [
            f"{pad}Paper type           : {self.paper_type}",
            f"{pad}Binder               : {self.binder_type}  ({self.binder_ratio})",
            f"{pad}Curing               : {self.curing_time_hours}h @ {self.curing_temp_c} deg C",
            f"{pad}Geometry             : {self.geometry_type}  "
            f"{self.geometry_dimensions_json()}",
        ]
        if self.graphite_grade is not None:
            lines.append(
                f"{pad}Graphite grade        : {self.graphite_grade}  "
                f"({self.graphite_particle_size_um} um)"
            )
            lines.append(
                f"{pad}Blasting              : {self.blasting_pressure_bar} bar  "
                f"@ {self.standoff_distance_mm} mm"
            )
            lines.append(f"{pad}Coating thickness     : {self.coating_thickness_mm} mm")
        if self.production_notes:
            lines.append(f"{pad}Notes                 : {self.production_notes}")
        if self.storage_conditions:
            lines.append(f"{pad}Storage               : {self.storage_conditions}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Pre-defined protocol instances matching quickstart.md section 2.1
# ------------------------------------------------------------------

BASELINE_PROTOCOL = SpecimenProtocol(
    paper_type="newspaper",
    binder_type="PVA",
    binder_ratio="1:3",
    curing_time_hours=24.0,
    curing_temp_c=25.0,
    production_notes="Baseline paper mache — no graphite coating applied.",
    storage_conditions="25 deg C, 50% RH",
)

COMPOSITE_PROTOCOL = SpecimenProtocol(
    paper_type="newspaper",
    binder_type="PVA",
    binder_ratio="1:3",
    curing_time_hours=24.0,
    curing_temp_c=25.0,
    graphite_grade="flake_industrial",
    graphite_particle_size_um=100.0,
    blasting_pressure_bar=4.0,
    standoff_distance_mm=150.0,
    coating_thickness_mm=0.5,
    production_notes="Graphite-coated via pneumatic blasting after curing.",
    storage_conditions="25 deg C, 50% RH",
)

VALID_SPECIMEN_TYPES: frozenset = frozenset({"baseline", "composite"})


def validate_protocol(protocol: SpecimenProtocol,
                      specimen_type: str = "composite") -> list[str]:
    """Check required fields for a given specimen type.

    Args:
        protocol: The protocol instance to validate.
        specimen_type: ``"baseline"`` or ``"composite"``.

    Returns:
        A list of error messages (empty if valid).
    """
    errors: list[str] = []

    if specimen_type not in VALID_SPECIMEN_TYPES:
        errors.append(f"Unknown specimen_type '{specimen_type}'.")
        return errors

    # --- Fields required for both types ---
    if not protocol.paper_type:
        errors.append("paper_type is required.")
    if not protocol.binder_type:
        errors.append("binder_type is required.")
    if not protocol.binder_ratio:
        errors.append("binder_ratio is required.")
    if protocol.curing_time_hours <= 0:
        errors.append("curing_time_hours must be > 0.")
    if not (-50 < protocol.curing_temp_c < 200):
        errors.append("curing_temp_c outside valid range (-50 .. 200).")
    if not protocol.geometry_type:
        errors.append("geometry_type is required.")
    if not protocol.geometry_dimensions:
        errors.append("geometry_dimensions is required.")

    # --- Composite-only fields ---
    if specimen_type == "composite":
        composite_fields: dict[str, object] = {
            "graphite_grade": protocol.graphite_grade,
            "graphite_particle_size_um": protocol.graphite_particle_size_um,
            "blasting_pressure_bar": protocol.blasting_pressure_bar,
            "standoff_distance_mm": protocol.standoff_distance_mm,
            "coating_thickness_mm": protocol.coating_thickness_mm,
        }
        for field_name, value in composite_fields.items():
            if value is None:
                errors.append(f"{field_name} is required for composite specimens.")

        # Sub-range checks per schema constraints
        if protocol.blasting_pressure_bar is not None and \
                not (1.0 <= protocol.blasting_pressure_bar <= 10.0):
            errors.append("blasting_pressure_bar must be between 1 and 10 bar.")
        if protocol.standoff_distance_mm is not None and \
                not (10.0 <= protocol.standoff_distance_mm <= 500.0):
            errors.append("standoff_distance_mm must be between 10 and 500 mm.")
        if protocol.coating_thickness_mm is not None and \
                protocol.coating_thickness_mm > 2.0:
            errors.append("coating_thickness_mm must be <= 2.0 mm.")

    return errors


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _main() -> None:
    import textwrap

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}  SPECIMEN PRODUCTION PROTOCOLS{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    for label, protocol, stype in [
        ("BASELINE (paper mache only)", BASELINE_PROTOCOL, "baseline"),
        ("COMPOSITE (paper mache + graphite)", COMPOSITE_PROTOCOL, "composite"),
    ]:
        print(f"\n{GREEN}>>> {label}{RESET}")
        print(protocol.summary(indent=2))

        errs = validate_protocol(protocol, stype)
        if errs:
            print(f"  {GREEN}[WARN]{RESET} Validation issues:")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"  {GREEN}[OK]{RESET} Protocol is valid.")

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"  Dataclass fields: {len([f for f in SpecimenProtocol.__dataclass_fields__])}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    _main()
