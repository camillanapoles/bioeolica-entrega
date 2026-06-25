"""Adaptive mesh — 3 níveis h-refinement + convergence study."""
from typing import Dict, List

LEVELS = {
    "coarse": {"h_factor": 1.0, "label": "L/10"},
    "medium": {"h_factor": 0.5, "label": "L/20"},
    "fine": {"h_factor": 0.25, "label": "L/40"},
}


class AdaptiveMesh:
    """3 níveis de malha para VVV com h-refinement adaptativo."""

    def __init__(self, base_size_mm: float = 10.0):
        self.base_size_mm = base_size_mm

    def generate(self, level: str, geometry: Dict = None) -> Dict:
        if level not in LEVELS:
            raise ValueError(f"Unknown level: {level}. Use coarse/medium/fine")
        factor = LEVELS[level]["h_factor"]
        return {
            "level": level,
            "element_size_mm": round(self.base_size_mm * factor, 2),
            "elements_estimated": int(10000 / factor),
            "status": "ready",
        }

    def convergence_study(self, results: List[float]) -> Dict:
        if len(results) < 2:
            return {"converged": False, "error_pct": 100.0, "results": results}
        errors = [abs(results[i] - results[-1]) / abs(results[-1]) * 100
                  for i in range(len(results) - 1)]
        return {
            "converged": max(errors) < 5.0,
            "max_error_pct": round(max(errors), 2),
            "results": results,
        }
