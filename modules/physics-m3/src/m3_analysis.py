#!/usr/bin/env python3
"""
M³ (Macro-Meso-Micro) Analysis Framework — Computational Mechanics.

Three-scale analysis for composite material modeling:
  - Macro:   Environment, boundaries, external loads, global behavior
  - Meso:    Interface layers, ply stacking, interphase, boundary layers
  - Micro:   Microstructure, fiber/matrix distribution, defects, local stress

Per the KDI methodology (INSTRUCTIONS.md), every analysis spans all
three scales with documented interconnections.

Usage:
    from m3_analysis import M3Analysis, MacroScale, MesoScale, MicroScale

    analysis = M3Analysis(material="paper_mache_pva_graphite")
    analysis.macro.set_boundary(temp=298, humidity=0.65)
    analysis.meso.set_layers([...])
    analysis.micro.set_microstructure(fiber_volume=0.15)
    result = analysis.run()
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  MACRO SCALE — Environment & Boundaries
# ═══════════════════════════════════════════════════════════════

@dataclass
class MacroScale:
    """Macro-scale: external environment, global boundaries, service conditions."""
    temperature_K: float = 298.0          # Operating temperature (K)
    humidity_pct: float = 50.0            # Relative humidity (%)
    pressure_Pa: float = 101325.0         # Atmospheric pressure (Pa)
    wind_speed_ms: float = 0.0            # Wind speed (m/s)
    solar_irradiance_Wm2: float = 0.0     # Solar radiation (W/m²)
    corrosion_class: str = "C2"           # ISO 9223 corrosion class (C1-C5)
    uv_exposure: str = "moderate"         # UV exposure level
    altitude_m: float = 0.0              # Altitude (m)

    def density_air(self) -> float:
        """Air density at current altitude and temperature (kg/m³)."""
        p = self.pressure_Pa * np.exp(-self.altitude_m / 8430.0)
        return p / (287.058 * self.temperature_K)

    def summary(self) -> Dict:
        return {
            "temperature_K": self.temperature_K,
            "temperature_C": self.temperature_K - 273.15,
            "humidity_pct": self.humidity_pct,
            "pressure_Pa": self.pressure_Pa,
            "wind_speed_ms": self.wind_speed_ms,
            "air_density_kgm3": round(self.density_air(), 3),
            "corrosion_class": self.corrosion_class,
            "uv_exposure": self.uv_exposure,
        }


# ═══════════════════════════════════════════════════════════════
#  MESO SCALE — Interface Layers & Interphase
# ═══════════════════════════════════════════════════════════════

@dataclass
class PlyLayer:
    """Single ply in a composite laminate."""
    material: str              # Material name
    thickness_mm: float        # Layer thickness (mm)
    fiber_orientation_deg: float = 0.0  # Fiber orientation (degrees)
    volume_fraction: float = 1.0        # Volume fraction of this layer
    density_kgm3: float = 0.0           # Density (kg/m³)
    elastic_modulus_GPa: float = 0.0    # E (GPa)
    poisson_ratio: float = 0.3          # ν


@dataclass
class MesoScale:
    """Meso-scale: layer stacking, interphase, ply interfaces."""
    layers: List[PlyLayer] = field(default_factory=list)
    interface_bond_strength_MPa: float = 5.0  # Interlaminar bond strength

    def add_layer(self, layer: PlyLayer):
        self.layers.append(layer)

    def total_thickness_mm(self) -> float:
        return sum(l.thickness_mm * l.volume_fraction for l in self.layers)

    def stacking_sequence(self) -> List[str]:
        return [l.material for l in self.layers]

    def equivalent_modulus_GPa(self) -> float:
        """Rule of mixtures for equivalent elastic modulus."""
        if not self.layers:
            return 0.0
        total = sum(l.thickness_mm for l in self.layers)
        if total == 0:
            return 0.0
        return sum(l.elastic_modulus_GPa * l.thickness_mm / total for l in self.layers)

    def summary(self) -> Dict:
        return {
            "n_layers": len(self.layers),
            "total_thickness_mm": round(self.total_thickness_mm(), 3),
            "stacking": self.stacking_sequence(),
            "equivalent_modulus_GPa": round(self.equivalent_modulus_GPa(), 2),
            "interface_bond_MPa": self.interface_bond_strength_MPa,
        }


# ═══════════════════════════════════════════════════════════════
#  MICRO SCALE — Microstructure & Defects
# ═══════════════════════════════════════════════════════════════

@dataclass
class MicroScale:
    """Micro-scale: fiber/matrix distribution, voids, defects, grain structure."""
    fiber_volume_fraction: float = 0.0       # V_f — fiber volume fraction
    matrix_material: str = ""                 # Matrix material name
    fiber_material: str = ""                  # Fiber material name
    fiber_diameter_um: float = 10.0           # Fiber diameter (microns)
    fiber_length_mm: float = 3.0              # Fiber length (mm)
    void_fraction: float = 0.0                # Porosity / void content
    grain_size_um: float = 0.0               # Average grain size (μm)
    defect_density: float = 0.0               # Defects per mm³
    aspect_ratio: float = 1.0                 # Fiber aspect ratio (L/D)

    def fiber_spacing_um(self) -> float:
        """Estimate inter-fiber spacing from volume fraction."""
        if self.fiber_volume_fraction <= 0:
            return float('inf')
        return self.fiber_diameter_um * np.sqrt(np.pi / (4 * self.fiber_volume_fraction))

    def effective_modulus_GPa(self, Ef: float, Em: float) -> float:
        """Rule of mixtures: Ec = Vf*Ef + Vm*Em (axial)."""
        Vf = self.fiber_volume_fraction
        Vm = 1 - Vf - self.void_fraction
        return Vf * Ef + Vm * Em

    def transverse_modulus_GPa(self, Ef: float, Em: float) -> float:
        """Reuss model: 1/Ec = Vf/Ef + Vm/Em (transverse)."""
        Vf = self.fiber_volume_fraction
        Vm = 1 - Vf - self.void_fraction
        if Ef <= 0 or Em <= 0:
            return 0.0
        return 1.0 / (Vf / Ef + Vm / Em)

    def summary(self) -> Dict:
        return {
            "fiber_volume_fraction": self.fiber_volume_fraction,
            "matrix": self.matrix_material,
            "fiber": self.fiber_material,
            "void_fraction": self.void_fraction,
            "fiber_spacing_um": round(self.fiber_spacing_um(), 1),
            "defect_density": self.defect_density,
            "aspect_ratio": self.aspect_ratio,
        }


# ═══════════════════════════════════════════════════════════════
#  M³ ANALYSIS — Integrated Multi-Scale
# ═══════════════════════════════════════════════════════════════

class M3Analysis:
    """Integrated M³ analysis — Macro → Meso → Micro → Synthesis."""

    def __init__(self, material: str = ""):
        self.material = material
        self.macro = MacroScale()
        self.meso = MesoScale()
        self.micro = MicroScale()

    def run(self) -> Dict:
        """Run full M³ analysis and produce synthesis."""
        return {
            "material": self.material,
            "macro": self.macro.summary(),
            "meso": self.meso.summary(),
            "micro": self.micro.summary(),
            "synthesis": self._synthesize(),
        }

    def _synthesize(self) -> Dict:
        """Cross-scale synthesis — interconnections between M³ layers."""
        return {
            "macro_meso_coupling": {
                "environment_affects_interfaces": True,
                "temp_humidity_effect": "thermal_expansion + moisture_swelling",
            },
            "meso_micro_coupling": {
                "layers_affect_fiber_distribution": True,
                "interface_stress_transfer": "shear_lag_mechanism",
            },
            "overall_notes": (
                f"M³ analysis for '{self.material}': "
                f"{len(self.meso.layers)} layers, "
                f"Vf={self.micro.fiber_volume_fraction:.0%}, "
                f"voids={self.micro.void_fraction:.1%}"
            ),
        }
