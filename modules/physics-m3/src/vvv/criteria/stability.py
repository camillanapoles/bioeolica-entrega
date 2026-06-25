"""Criterion 2/6: Temporal Stability — residual < 1e-4 com redução de Δt.

Verification step: redução de Δt até estabilização do resíduo.
"""
from typing import List, Optional

from physics_m3.vvv.certificate import VVVCriterion


class TemporalStabilityCriterion:
    """Evaluate temporal stability from residual convergence history."""

    def __init__(self, residual_tolerance: float = 1e-4):
        self.residual_tolerance = residual_tolerance

    def evaluate(self, residuals: List[float],
                 deltas: Optional[List[float]] = None) -> VVVCriterion:
        if not residuals:
            return VVVCriterion(
                name="temporal_stability",
                passed=False,
                metric_value=-1,
                tolerance=self.residual_tolerance,
                details="no residual data provided",
            )

        final_residual = residuals[-1]
        passed = final_residual < self.residual_tolerance

        details_parts = []
        if not passed:
            details_parts.append(f"residual {final_residual:.2e} >= {self.residual_tolerance:.0e}")

        sz = len(residuals)
        if sz >= 3:
            decreasing = all(residuals[i] > residuals[i + 1] for i in range(sz - 1))
            if not decreasing:
                details_parts.append("residual not monotonic")

        return VVVCriterion(
            name="temporal_stability",
            passed=passed,
            metric_value=final_residual,
            tolerance=self.residual_tolerance,
            details="; ".join(details_parts) if details_parts else f"stable at {final_residual:.2e}",
        )
