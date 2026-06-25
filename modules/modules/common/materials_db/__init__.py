# =============================================================================
# Materials Property Database — Composite Biomaterial for Wind Energy
# Part of T011 — Phase 2 Foundational
# Reference: knowledge/materials/README.md, data-model.md
# =============================================================================
"""
Materials property database and loading utilities.

Provides:
  - MaterialProperty dataclass for structured property representation
  - load_material_properties() for CSV/JSON loading into objects
  - MATERIAL_SCHEMAS: canonical property definitions per material type

Usage:
    from src.common.materials_db import load_material_properties

    props = load_material_properties("baseline", source="data/specimens/...")
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MaterialProperty:
    """A single measured or referenced material property.

    Attributes:
        name: Property name (e.g. 'tensile_strength', 'elastic_modulus')
        value: Numeric value in SI units (Pa, Pa, dimensionless, etc.)
        unit: SI unit string (e.g. 'MPa', 'GPa', 'kg/m3')
        uncertainty: Measurement uncertainty (same unit as value, ±)
        source: Reference or specimen_id this value originates from
    """
    name: str
    value: float
    unit: str
    uncertainty: float = 0.0
    source: str = ""


@dataclass
class MaterialRecord:
    """Complete material definition with all known properties.

    Attributes:
        material_id: UUID v4 referencing objects.id
        material_type: 'baseline' | 'composite'
        paper_type: e.g. 'newspaper', 'office_paper', 'mixed'
        binder_type: e.g. 'PVA'
        binder_ratio: e.g. '1:3'
        properties: Dict mapping property name → MaterialProperty
        graphite_fields: Dict with graphite-specific fields (None for baseline)
    """
    material_id: str
    material_type: str
    paper_type: str
    binder_type: str
    binder_ratio: str
    properties: Dict[str, MaterialProperty] = field(default_factory=dict)
    graphite_fields: Optional[Dict] = None


# ---------------------------------------------------------------------------
# Canonical property schemas (which properties each material type must define)
# ---------------------------------------------------------------------------

BASELINE_PROPERTIES = {
    "density": {"unit": "kg/m3", "description": "Mass density"},
    "tensile_strength": {"unit": "MPa", "description": "Ultimate tensile strength (ASTM D638)"},
    "elastic_modulus": {"unit": "GPa", "description": "Young's modulus (ASTM D638)"},
    "flexural_strength": {"unit": "MPa", "description": "Flexural strength (ASTM D790)"},
    "flexural_modulus": {"unit": "GPa", "description": "Flexural modulus (ASTM D790)"},
    "compressive_strength": {"unit": "MPa", "description": "Compressive strength (ASTM D695)"},
    "hardness": {"unit": "Shore D", "description": "Surface hardness (ASTM D2240)"},
    "fatigue_strength": {"unit": "MPa", "description": "Fatigue strength at 1e6 cycles (ASTM D7774)"},
}

COMPOSITE_PROPERTIES = {
    **BASELINE_PROPERTIES,
    "coating_adhesion": {"unit": "MPa", "description": "Graphite coating pull-off adhesion"},
    "surface_roughness": {"unit": "um", "description": "Surface roughness Ra after blasting"},
    "coating_thickness": {"unit": "mm", "description": "Graphite coating thickness"},
}

MATERIAL_SCHEMAS = {
    "baseline": {"properties": BASELINE_PROPERTIES, "required_fields": ["paper_type", "binder_type", "binder_ratio"]},
    "composite": {"properties": COMPOSITE_PROPERTIES, "required_fields": ["paper_type", "binder_type", "binder_ratio", "graphite_grade", "blasting_pressure_bar", "coating_thickness_mm"]},
}


def validate_material_record(record: MaterialRecord) -> List[str]:
    """Validate a MaterialRecord against the canonical schema.

    Args:
        record: MaterialRecord to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors = []
    schema = MATERIAL_SCHEMAS.get(record.material_type)
    if schema is None:
        errors.append(f"Unknown material_type: {record.material_type}")
        return errors

    required_props = schema["properties"]
    for prop_name in required_props:
        if prop_name not in record.properties:
            errors.append(f"Missing property: {prop_name}")

    return errors


# ---------------------------------------------------------------------------
# CSV / JSON load helpers (stubs — populated when experimental data exists)
# ---------------------------------------------------------------------------

def load_material_properties(
    material_type: str,
    source: str,
) -> MaterialRecord:
    """Load material properties from a data source file.

    Args:
        material_type: 'baseline' or 'composite'
        source: Path to CSV or JSON file with property data.

    Returns:
        MaterialRecord with loaded properties.

    Raises:
        FileNotFoundError: If source does not exist.
        ValueError: If file format is not supported.
    """
    import json

    if not os.path.exists(source):
        raise FileNotFoundError(f"Material data source not found: {source}")

    if source.endswith(".json"):
        with open(source) as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported file format: {source}. Use .json files.")

    return MaterialRecord(
        material_id=data.get("id", ""),
        material_type=material_type,
        paper_type=data.get("paper_type", ""),
        binder_type=data.get("binder_type", ""),
        binder_ratio=data.get("binder_ratio", ""),
        properties={
            k: MaterialProperty(**v) for k, v in data.get("properties", {}).items()
        },
        graphite_fields=data.get("graphite_fields"),
    )


import os  # noqa: E402 (needed for load_material_properties)
