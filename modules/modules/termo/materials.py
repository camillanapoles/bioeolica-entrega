"""
Thermal material properties database.
"""

from __future__ import annotations

from dataclasses import dataclass

# Registry integration – best-effort registration
try:
    from src.common.registry import create_object, list_objects
    from src.common.database import DatabaseError
except ImportError:
    # Registry not available (e.g. during initial setup or tests without dep)
    create_object = None
    list_objects = None
    DatabaseError = Exception


@dataclass
class ThermalMaterial:
    """Material thermal properties."""

    name: str
    k: float      # Thermal conductivity (W/mK)
    alpha: float  # Coefficient of thermal expansion (1/K)
    cp: float     # Specific heat (J/kgK)
    rho: float    # Density (kg/m³)
    E: float = 200e9   # Young's modulus (Pa) for thermal stress
    nu: float = 0.3    # Poisson ratio

    def __post_init__(self) -> None:
        """Validate positive physical properties."""
        if self.k <= 0:
            raise ValueError(f"Thermal conductivity k must be positive, got {self.k}")
        if self.alpha <= 0:
            raise ValueError(f"CTE alpha must be positive, got {self.alpha}")
        if self.cp <= 0:
            raise ValueError(f"Specific heat cp must be positive, got {self.cp}")
        if self.rho <= 0:
            raise ValueError(f"Density rho must be positive, got {self.rho}")


# Default material database
MATERIALS: dict[str, ThermalMaterial] = {
    "steel": ThermalMaterial("steel", k=50.0, alpha=1.2e-5, cp=460, rho=7800),
    "aluminum": ThermalMaterial("aluminum", k=237.0, alpha=2.3e-5, cp=900, rho=2700),
    "copper": ThermalMaterial("copper", k=401.0, alpha=1.7e-5, cp=385, rho=8960),
    "titanium": ThermalMaterial("titanium", k=21.9, alpha=8.6e-6, cp=520, rho=4500),
    "ceramic": ThermalMaterial("ceramic", k=2.0, alpha=5.0e-6, cp=800, rho=3500),
    "generic": ThermalMaterial("generic", k=50.0, alpha=1.0e-5, cp=500, rho=2700),
}


def get_material(name: str) -> ThermalMaterial:
    """Look up material by name, fall back to generic."""
    return MATERIALS.get(name.lower(), MATERIALS["generic"])


# ---------------------------------------------------------------------------
# Universal registry integration
# ---------------------------------------------------------------------------

def _is_material_registered(name: str) -> bool:
    """Check if a material with the given name already exists in the registry."""
    if list_objects is None:
        return False
    try:
        existing = list_objects(object_type="material")
        for obj in existing:
            meta = obj.get("metadata", {})
            if isinstance(meta, dict) and meta.get("name") == name:
                return True
    except Exception:
        pass
    return False


def register_materials() -> None:
    """Register all materials in the universal registry (objects table).

    Skips materials already registered (by matching name in metadata).
    This is called automatically on import, but can also be invoked manually.
    """
    if create_object is None:
        return  # Registry not available

    for name, mat in MATERIALS.items():
        if _is_material_registered(name):
            continue
        try:
            create_object(
                "material",
                tags=[name],
                metadata={
                    "name": name,
                    "k": mat.k,
                    "alpha": mat.alpha,
                    "cp": mat.cp,
                    "rho": mat.rho,
                    "E": mat.E,
                    "nu": mat.nu,
                },
            )
        except DatabaseError:
            # Database not available – skip silently
            pass


# Automatically register materials on import (best-effort)
try:
    register_materials()
except Exception:
    pass
