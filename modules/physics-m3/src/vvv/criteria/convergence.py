"""Criterion 1/6: Mesh Convergence — erro < 5% entre 3 níveis de refinamento.

Verification step: convergência de malha com 3 níveis (grosseira/média/fina).
Usa VVVReport.verify_convergence() do vvv_protocol.
"""
from typing import Dict, List, Optional

from physics_m3.vvv.certificate import VVVCriterion


class MeshConvergenceCriterion:
    """Evaluate mesh convergence from error values across refinement levels."""

    def __init__(self, tolerance_pct: float = 5.0):
        self.tolerance_pct = tolerance_pct

    def evaluate(self, errors_pct: List[float],
                 h_values: List[float],
                 study_name: str = "") -> VVVCriterion:
        if len(errors_pct) < 2:
            return VVVCriterion(
                name="mesh_convergence",
                passed=False,
                metric_value=max(errors_pct) if errors_pct else -1,
                tolerance=self.tolerance_pct,
                details="INCONCLUSIVE: need at least 2 mesh levels",
            )

        decreasing = all(errors_pct[i] > errors_pct[i + 1] for i in range(len(errors_pct) - 1))
        converged = errors_pct[-1] < self.tolerance_pct
        passed = decreasing and converged

        details_parts = []
        if not decreasing:
            details_parts.append("error not monotonically decreasing")
        if not converged:
            details_parts.append(f"final error {errors_pct[-1]:.2f}% >= {self.tolerance_pct}%")

        return VVVCriterion(
            name="mesh_convergence",
            passed=passed,
            metric_value=errors_pct[-1],
            tolerance=self.tolerance_pct,
            details="; ".join(details_parts) if details_parts else "converged",
        )
