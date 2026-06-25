"""KDI Meso Bridge — FEM results → Meso-scale interface analysis.

From INSTRUCTIONS.md:
  Meso = interfaces, juntas, acoplamentos, concentracao de tensao
"""

from __future__ import annotations

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3"))

from modules.structural_analysis import von_mises_stress, safety_factor


class MesoAnalysis:
    """Meso-scale analysis: stress concentrations, interfaces, joints.

    Parameters
    ----------
    config : dict, optional
        Meso parameters (load, geometry, Kt factors).
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._results = {}

    def run(self) -> dict:
        """Run meso-scale analysis.

        Returns
        -------
        results : dict
            Meso metrics: Kt, interface_stress, joint_safety, critical_locations.
        """
        nominal_stress = self.config.get("nominal_stress_MPa", 100)
        hole_diameter_mm = self.config.get("hole_diameter_mm", 5)
        plate_width_mm = self.config.get("plate_width_mm", 50)
        yield_mpa = self.config.get("yield_strength_MPa", 250)

        # Kirsch stress concentration: Kt = 3 for infinite plate
        d_w = hole_diameter_mm / plate_width_mm
        if d_w < 0.3:
            Kt = 3.0
        else:
            Kt = 3.0 - 3.0 * d_w + 3.0 * d_w**2  # finite-width correction

        peak_stress = nominal_stress * Kt
        vm = von_mises_stress(peak_stress, 0, 0)
        sf = safety_factor(yield_mpa, vm)

        self._results = {
            "Kt": round(Kt, 3),
            "nominal_stress_MPa": nominal_stress,
            "peak_stress_MPa": round(peak_stress, 2),
            "von_mises_MPa": round(vm, 2),
            "safety_factor": round(sf, 2),
            "critical_location": "hole_edge",
            "status": "PASS" if sf >= 1.5 else "FAIL",
        }
        return self._results

    def from_config(self, config: dict) -> "MesoAnalysis":
        """Load from config dict (from config.json parser)."""
        self.config = config
        return self

    @property
    def results(self) -> dict:
        return self._results if self._results else self.run()
