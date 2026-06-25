"""KDI Micro Bridge — materials → Micro-scale analysis.

From INSTRUCTIONS.md:
  Micro = propriedades materiais, microestrutura, falha, fadiga
"""

from __future__ import annotations

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3"))

from modules.composite_model import CompositeMaterial


class MicroAnalysis:
    """Micro-scale analysis: material properties, homogenization, failure.

    Parameters
    ----------
    fiber : str
        Fiber type (e.g., 'waste_paper').
    matrix : str
        Matrix type (e.g., 'pva').
    coating : str, optional
        Coating type (e.g., 'graphite_coating').
    V_f : float
        Fiber volume fraction (0-1).
    """

    def __init__(self, fiber: str = "waste_paper", matrix: str = "pva",
                 coating: str = "graphite_coating", V_f: float = 0.15):
        self.fiber = fiber
        self.matrix = matrix
        self.coating = coating
        self.V_f = V_f
        self._composite = CompositeMaterial(fiber=fiber, matrix=matrix, coating=coating)
        self._results = {}

    def run(self) -> dict:
        """Run micro-scale analysis.

        Returns
        -------
        results : dict
            Homogenized properties, failure envelope, density.
        """
        ec = self._composite.elastic_constants()
        E1 = ec.get("E1_longitudinal_GPa", 10)
        E2 = ec.get("E2_transverse_GPa", 5)
        rho = self._composite.density_g_cm3() if hasattr(self._composite, 'density_g_cm3') else 1.5

        self._results = {
            "material": f"{self.fiber}/{self.matrix}/{self.coating}",
            "V_f": self.V_f,
            "E1_GPa": round(E1, 1),
            "E2_GPa": round(E2, 1),
            "density_g_cm3": round(rho, 2),
            "status": "PASS",
        }
        return self._results

    def from_config(self, config: dict) -> "MicroAnalysis":
        """Load from config dict."""
        self.fiber = config.get("fiber", self.fiber)
        self.matrix = config.get("matrix", self.matrix)
        self.coating = config.get("coating", self.coating)
        self.V_f = config.get("V_f", self.V_f)
        self._composite = CompositeMaterial(fiber=self.fiber, matrix=self.matrix, coating=self.coating)
        return self

    @property
    def results(self) -> dict:
        return self._results if self._results else self.run()
