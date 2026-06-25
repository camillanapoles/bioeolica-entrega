#!/usr/bin/env python3
"""
Composite Material Model — Bio-based Composites for Wind Energy.

Models paper mache + PVA binder + graphite coating composites with:
  - Rule of mixtures for elastic properties
  - Hashin-Rosen micromechanics for strength
  - Process-structure-property correlation
  - Fabrication process simulation (shredding, mixing, molding, drying)

Usage:
    from composite_model import CompositeMaterial, FabricationProcess

    # Define a paper mache + PVA + graphite composite
    mat = CompositeMaterial(
        fiber="waste_paper", matrix="pva",
        fiber_volume_fraction=0.15, void_fraction=0.08
    )
    E, G, nu = mat.elastic_constants()
    strength = mat.estimate_strength()
"""

from dataclasses import dataclass
from typing import Dict, Optional


# ═══════════════════════════════════════════════════════════════
#  MATERIAL PROPERTIES DATABASE   (fallback – cfg override)
# ═══════════════════════════════════════════════════════════════

MATERIAL_DB = {
    # Fibers
    "waste_paper": {
        "type": "fiber",
        "E_GPa": 5.0, "nu": 0.3, "G_GPa": 1.92,
        "density_kgm3": 800, "tensile_MPa": 30, "cost_per_kg": 0.05,
        "description": "Recycled cellulose fiber (waste paper)",
    },
    "jute": {
        "type": "fiber", "E_GPa": 26.5, "nu": 0.33, "G_GPa": 10.0,
        "density_kgm3": 1460, "tensile_MPa": 400, "cost_per_kg": 0.50,
        "description": "Natural jute fiber",
    },
    "hemp": {
        "type": "fiber", "E_GPa": 35.0, "nu": 0.32, "G_GPa": 13.3,
        "density_kgm3": 1500, "tensile_MPa": 550, "cost_per_kg": 1.00,
        "description": "Industrial hemp fiber",
    },
    "fiberglass_e": {
        "type": "fiber", "E_GPa": 72.0, "nu": 0.22, "G_GPa": 29.5,
        "density_kgm3": 2540, "tensile_MPa": 2000, "cost_per_kg": 2.50,
        "description": "E-glass fiber (baseline comparison)",
    },
    # Matrices
    "pva": {
        "type": "matrix", "E_GPa": 2.0, "nu": 0.35, "G_GPa": 0.74,
        "density_kgm3": 1200, "tensile_MPa": 30, "cost_per_kg": 3.00,
        "description": "Polyvinyl acetate (white glue) binder",
    },
    "epoxy": {
        "type": "matrix", "E_GPa": 3.5, "nu": 0.35, "G_GPa": 1.30,
        "density_kgm3": 1160, "tensile_MPa": 60, "cost_per_kg": 8.00,
        "description": "Epoxy resin (baseline comparison)",
    },
    "starch": {
        "type": "matrix", "E_GPa": 1.5, "nu": 0.38, "G_GPa": 0.54,
        "density_kgm3": 1500, "tensile_MPa": 15, "cost_per_kg": 0.80,
        "description": "Biodegradable starch-based binder",
    },
    # Coatings
    "graphite_coating": {
        "type": "coating", "E_GPa": 8.0, "nu": 0.25, "G_GPa": 3.2,
        "density_kgm3": 2000, "tensile_MPa": 15, "cost_per_kg": 5.00,
        "thickness_mm": 0.5,
        "description": "Graphite powder + PVA protective coating",
    },
    "bio_epoxy_coating": {
        "type": "coating", "E_GPa": 3.0, "nu": 0.35, "G_GPa": 1.11,
        "density_kgm3": 1150, "tensile_MPa": 30, "cost_per_kg": 12.00,
        "thickness_mm": 0.3,
        "description": "Bio-based epoxy protective coating",
    },
}


# ═══════════════════════════════════════════════════════════════
#  FABRICATION PROCESS
# ═══════════════════════════════════════════════════════════════

@dataclass
class FabricationProcess:
    """Simulate the fabrication process and its effect on final properties."""
    shredding_time_min: float = 15       # Paper shredding time
    mixing_time_min: float = 10           # PVA + water + paper mixing
    molding_pressure_MPa: float = 0.5     # Molding pressure
    drying_temp_C: float = 60             # Drying temperature
    drying_time_h: float = 24             # Drying duration
    coating_layers: int = 2               # Graphite coating layers
    curing_temp_C: float = 25             # Curing temperature
    curing_time_h: float = 48             # Curing duration

    def water_content_kg(self, paper_mass_kg: float, ratio: float = 2.0) -> float:
        """Water needed for slurry (ratio = water:paper by mass)."""
        return paper_mass_kg * ratio

    def total_energy_kWh(self, paper_mass_kg: float) -> Dict:
        """Estimate total process energy."""
        E_shred = 0.05 * self.shredding_time_min * paper_mass_kg
        E_mix = 0.02 * self.mixing_time_min * paper_mass_kg
        E_dry = 1.2 * self.drying_time_h * (1 + paper_mass_kg * 2)
        E_cure = 0.8 * self.curing_time_h * paper_mass_kg
        return {
            "shredding_kWh": round(E_shred, 2),
            "mixing_kWh": round(E_mix, 2),
            "drying_kWh": round(E_dry, 2),
            "curing_kWh": round(E_cure, 2),
            "total_kWh": round(E_shred + E_mix + E_dry + E_cure, 2),
        }


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE MATERIAL
# ═══════════════════════════════════════════════════════════════

class CompositeMaterial:
    """Model a fiber-reinforced composite material with M³ integration."""

    def __init__(
        self,
        fiber: str = "waste_paper",
        matrix: str = "pva",
        coating: str = "graphite_coating",
        fiber_volume_fraction: float = 0.15,
        void_fraction: float = 0.05,
        cfg: Optional[object] = None,      # ConfigManager (optional)
    ):
        self.cfg = cfg
        self.fiber_name = fiber
        self.matrix_name = matrix
        self.coating_name = coating
        self.Vf = fiber_volume_fraction
        self.Vv = void_fraction

        # Resolver material properties: cfg primeiro, fallback MATERIAL_DB
        self.fiber = self._resolve_material(fiber, "fiber") or MATERIAL_DB.get(fiber, {})
        self.matrix_m = self._resolve_material(matrix, "matrix") or MATERIAL_DB.get(matrix, {})
        self.coating = self._resolve_material(coating, "coating") or MATERIAL_DB.get(coating, {})

        if not self.fiber:
            raise ValueError(f"Fiber '{fiber}' not found in config or MATERIAL_DB")
        if not self.matrix_m:
            raise ValueError(f"Unknown matrix: {matrix}")

    @property
    def Vm(self) -> float:
        """Matrix volume fraction."""
        return 1.0 - self.Vf - self.Vv

    def elastic_constants(self) -> Dict[str, float]:
        """Compute elastic constants via rule of mixtures and Halpin-Tsai."""
        Ef = self.fiber.get("E_GPa", 1)
        Em = self.matrix_m.get("E_GPa", 1)
        nuf = self.fiber.get("nu", 0.3)
        num = self.matrix_m.get("nu", 0.35)

        # Longitudinal modulus (Voigt)
        E1 = self.Vf * Ef + self.Vm * Em

        # Transverse modulus (Halpin-Tsai)
        xi = 2.0  # Circular fiber
        eta = (Ef / Em - 1) / (Ef / Em + xi)
        E2 = Em * (1 + xi * eta * self.Vf) / (1 - eta * self.Vf)

        # Poisson ratio (Voigt)
        nu12 = self.Vf * nuf + self.Vm * num

        # Shear modulus
        Gf = self.fiber.get("G_GPa", Ef / (2 * (1 + nuf)))
        Gm = self.matrix_m.get("G_GPa", Em / (2 * (1 + num)))
        eta_g = (Gf / Gm - 1) / (Gf / Gm + xi)
        G12 = Gm * (1 + xi * eta_g * self.Vf) / (1 - eta_g * self.Vf)

        # Density
        rhof = self.fiber.get("density_kgm3", 1000)
        rhom = self.matrix_m.get("density_kgm3", 1000)
        rho_c = self.Vf * rhof + self.Vm * rhom
        
        return {
            "E1_longitudinal_GPa": round(E1, 3),
            "E2_transverse_GPa": round(E2, 3),
            "nu12": round(nu12, 3),
            "G12_shear_GPa": round(G12, 3),
            "density_kgm3": round(rho_c, 1),
        }

    def estimate_strength(self) -> Dict[str, float]:
        """Estimate strength properties from constituent properties."""
        Ef = self.fiber.get("E_GPa", 1)
        Em = self.matrix_m.get("E_GPa", 1)
        s_f = self.fiber.get("tensile_MPa", 30)
        s_m = self.matrix_m.get("tensile_MPa", 30)

        # Longitudinal tensile strength (ROM)
        s_1t = s_f * self.Vf + s_m * self.Vm

        # Transverse tensile strength
        s_2t = s_m * (1 - 2 * np.sqrt(self.Vf / np.pi))

        # Compressive strength (approx)
        E1 = self.Vf * Ef + self.Vm * Em
        s_1c = 0.3 * E1  # Microbuckling estimate

        # Interlaminar shear strength (approx)
        s_12 = 0.5 * s_m

        # Account for voids
        void_factor = 1 - 2 * self.Vv

        return {
            "tensile_longitudinal_MPa": round(s_1t * void_factor, 1),
            "tensile_transverse_MPa": round(s_2t * void_factor, 1),
            "compressive_longitudinal_MPa": round(s_1c * void_factor, 1),
            "interlaminar_shear_MPa": round(s_12 * void_factor, 1),
        }

    def summary(self) -> Dict:
        """Complete material summary."""
        return {
            "name": f"{self.fiber_name}_{self.matrix_name}",
            "fiber": self.fiber.get("description", self.fiber_name),
            "matrix": self.matrix_m.get("description", self.matrix_name),
            "coating": self.coating.get("description", "none"),
            "Vf": self.Vf,
            "Vv": self.Vv,
            "elastic": self.elastic_constants(),
            "strength": self.estimate_strength(),
        }


    def _resolve_material(self, name: str, mat_type: str) -> Optional[dict]:
        """Try to read material from cfg; return None if not available."""
        if self.cfg is None:
            return None
        try:
            return self.cfg.get(f"material_db.{mat_type}.{name}", None)
        except Exception:
            return None
