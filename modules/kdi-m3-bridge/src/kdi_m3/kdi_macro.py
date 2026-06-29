"""KDI Macro Bridge — CAD geometry → Macro-scale M³ analysis.

Maps parametric CAD models and environmental conditions to the
KDI Macro-scale analysis (system-level loads, BCs, environment).

From INSTRUCTIONS.md:
  Macro = fronteiras externas, BCs globais, ambiente, cargas de vento
"""

from __future__ import annotations

import math
import sys
import os
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from pathlib import Path

# Import physics-m3 modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3", "src"))

from m3_analysis import MacroScale

# P$1: rotear constantes pelo schema unificado
_CORE = Path(__file__).resolve()
while not (_CORE / "workspace").exists() and _CORE.parent != _CORE:
    _CORE = _CORE.parent
_CORE = _CORE / "workspace" / "lab1-material-papel-mache-grafite"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from core.constants import get


@dataclass
class MacroEnvironment:
    """Environmental conditions at the macro scale.

    Parameters
    ----------
    altitude_m : float
        Site altitude in meters.
    wind_class : str, optional
        Terrain category ('I','II','III','IV','V') per NBR 6123 / IEC 61400.
    wind_speed_ref_ms : float, optional
        Reference wind speed at 10m height (m/s).
    exposure : str, optional
        'rural', 'urban', 'offshore'.
    safety_class : str, optional
        'CC1', 'CC2', 'CC3' per structural standard.
    """
    altitude_m: float = 100.0
    wind_class: str = "II"
    wind_speed_ref_ms: float = 30.0
    exposure: str = "rural"
    safety_class: str = "CC2"

    def terrain_roughness(self) -> float:
        """Terrain roughness length z0 (m) per wind class."""
        z0_map = get("modules.kdi_m3_bridge.wind_class_z0")
        return z0_map.get(self.wind_class, 0.05)

    def gust_factor(self) -> float:
        """Gust factor for peak wind loading."""
        gust_map = get("modules.kdi_m3_bridge.gust_factor_map")
        return gust_map.get(self.exposure, 1.40)

    def wind_pressure_kPa(self, height_m: float) -> float:
        """Dynamic wind pressure at a given height (kPa).

        q(z) = 0.5 * rho * V(z)^2
        V(z) = V_ref * (z/10)^alpha  (power law wind profile)
        """
        rho = get("modules.kdi_m3_bridge.rho_air_ref")
        alpha_map = get("modules.kdi_m3_bridge.terrain_alpha_map")
        alpha = alpha_map.get(self.wind_class, 0.15)
        vz = self.wind_speed_ref_ms * max((height_m / 10) ** alpha, 0.5)
        gust = self.gust_factor()
        return 0.5 * rho * (vz * gust) ** 2 / 1000


class MacroAnalysis:
    """Unified macro-scale analysis bridging CAD → M³ → FEM BCs.

    Parameters
    ----------
    cad_model : object, optional
        CadModel instance with bounding_box(), volume, mass.
    env : MacroEnvironment, optional
        Environmental conditions.
    structure_type : str, optional
        'beam', 'blade', 'tower', 'bracket', 'generic'.
    """

    def __init__(self, cad_model=None, env=None, structure_type: str = "generic"):
        self.cad = cad_model
        self.env = env or MacroEnvironment()
        self.structure_type = structure_type
        self._macro_scale = None
        self._results = {}

    def from_cad(self, cad_model) -> "MacroAnalysis":
        """Set CAD model and auto-extract macro parameters."""
        self.cad = cad_model
        return self

    def from_cadquery(self, cadquery_obj):
        """Import a CadQuery Workplane object (alternative to CadModel)."""
        bb = cadquery_obj.val().BoundingBox()
        vol = cadquery_obj.val().Volume()
        # Wrap as simple object
        class Wrap:
            pass
        w = Wrap()
        w.bb = lambda: {"x": bb.xmax - bb.xmin, "y": bb.ymax - bb.ymin,
                        "z": bb.zmax - bb.zmin}
        w.volume = vol
        w.mass = vol * 1e-6
        self.cad = w
        return self

    def run(self) -> dict:
        """Execute macro-scale analysis.

        Returns
        -------
        results : dict
            Macro-scale results with keys: dimensions, volume, mass,
            wind_pressure, forces, macro_scale, environment.
        """
        if self.cad is None:
            raise ValueError("No CAD model. Use from_cad() first.")

        # Extract geometry
        bb = self.cad.bounding_box() if hasattr(self.cad, 'bounding_box') else self.cad.bb()
        vol = self.cad.volume if hasattr(self.cad, 'volume') else 0
        mass = self.cad.mass if hasattr(self.cad, 'mass') else vol * 1e-6

        # Environmental loads
        height_ref = bb.get("z", bb.get("zmax", 1)) if isinstance(bb, dict) else 1.0
        wind_p = self.env.wind_pressure_kPa(max(height_ref, 1))
        total_wind_force_N = wind_p * bb.get("x", 1) * bb.get("y", 1) * 1000 if isinstance(bb, dict) else 0

        # MacroScale from physics-m3
        try:
            self._macro_scale = MacroScale(
                altitude_m=self.env.altitude_m,
                wind_speed_ms=self.env.wind_speed_ref_ms,
            )
            rho_air = self._macro_scale.density_air()
        except Exception:
            rho_air = get("modules.kdi_m3_bridge.rho_air_ref")

        self._results = {
            "dimensions_mm": bb,
            "volume_mm3": vol,
            "mass_kg": mass,
            "environment": {
                "altitude_m": self.env.altitude_m,
                "wind_class": self.env.wind_class,
                "wind_speed_ref_ms": self.env.wind_speed_ref_ms,
                "air_density_kgm3": rho_air,
                "gust_factor": self.env.gust_factor(),
                "wind_pressure_kPa": wind_p,
                "total_wind_force_N": total_wind_force_N,
            },
            "structure_type": self.structure_type,
            "macro_scale_summary": self._macro_scale.summary() if self._macro_scale else {},
            "status": "PASS",
        }
        return self._results

    def report(self) -> str:
        """Generate formatted macro-scale report."""
        if not self._results:
            self.run()
        r = self._results
        env = r["environment"]
        lines = [
            "=" * 60,
            f"KDI MACRO ANALYSIS - {r['structure_type'].upper()}",
            "=" * 60,
            "",
            "GEOMETRY:",
            f"  Dimensions (mm): {r['dimensions_mm']}",
            f"  Volume: {r['volume_mm3']:.0f} mm³",
            f"  Mass:   {r['mass_kg']:.3f} kg",
            "",
            "ENVIRONMENT:",
            f"  Altitude:  {env['altitude_m']} m",
            f"  Wind class: {env['wind_class']} (ref speed: {env['wind_speed_ref_ms']} m/s)",
            f"  Air density: {env['air_density_kgm3']:.3f} kg/m³",
            f"  Wind pressure: {env['wind_pressure_kPa']:.3f} kPa",
            f"  Total wind force: {env['total_wind_force_N']:.1f} N",
            "",
            "STATUS: " + r["status"],
        ]
        return "\n".join(lines)

    def to_fem_bcs(self) -> dict:
        """Export macro loads to CalculiX boundary conditions.

        Returns
        -------
        bcs : dict
            Boundary conditions dict compatible with FEMSolver.
        """
        if not self._results:
            self.run()
        env = self._results["environment"]
        force = env["total_wind_force_N"]
        return {
            "force": {"fx": force * 0.5, "fy": force * 0.3, "fz": force * 0.2},
            "pressure": env["wind_pressure_kPa"] * 1000,
        }

    @property
    def results(self) -> dict:
        return self._results if self._results else self.run()


def macro_from_cad_and_env(
    cad_model,
    altitude_m: float = 100,
    wind_speed_ref_ms: float = 30,
    wind_class: str = "II",
    structure_type: str = "generic",
) -> MacroAnalysis:
    """Convenience: create MacroAnalysis from CadModel + environment in one call."""
    env = MacroEnvironment(
        altitude_m=altitude_m,
        wind_speed_ref_ms=wind_speed_ref_ms,
        wind_class=wind_class,
    )
    return MacroAnalysis(cad_model=cad_model, env=env, structure_type=structure_type)
