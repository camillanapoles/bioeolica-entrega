"""Criterion 4/6: Benchmark Correlation — > 90% correlação com solução conhecida.

Validation step: comparação com benchmark analítico ou experimental.
Usa VVVReport.validate_analytical() or validate_experimental().
"""
from typing import List, Optional

from physics_m3.vvv.certificate import VVVCriterion


class BenchmarkCorrelationCriterion:
    """Evaluate correlation with known analytical/experimental benchmark."""

    def __init__(self, tolerance_pct: float = 10.0):
        self.tolerance_pct = tolerance_pct

    def evaluate_analytical(self, numerical: float,
                            analytical: float) -> VVVCriterion:
        """Compare numerical vs analytical solution."""
        if analytical == 0:
            return VVVCriterion(
                name="benchmark_correlation",
                passed=False,
                metric_value=-1,
                tolerance=self.tolerance_pct,
                details="analytical solution is zero (division by zero)",
            )

        error_pct = abs(numerical - analytical) / abs(analytical) * 100
        passed = error_pct < self.tolerance_pct

        return VVVCriterion(
            name="benchmark_correlation",
            passed=passed,
            metric_value=error_pct,
            tolerance=self.tolerance_pct,
            details=f"{'within' if passed else 'exceeded'} tolerance: {error_pct:.2f}% vs {self.tolerance_pct}%",
        )

    def evaluate_experimental(self, simulation: List[float],
                               experimental: List[float]) -> VVVCriterion:
        if len(simulation) != len(experimental):
            return VVVCriterion(
                name="benchmark_correlation",
                passed=False,
                metric_value=100.0,
                tolerance=self.tolerance_pct,
                details="mismatched array lengths",
            )

        errors = [abs(s - e) / abs(e) * 100 for s, e in zip(simulation, experimental) if e != 0]
        if not errors:
            return VVVCriterion(
                name="benchmark_correlation",
                passed=False,
                metric_value=100.0,
                tolerance=self.tolerance_pct,
                details="no valid experimental comparison points",
            )

        max_error = max(errors)
        passed = max_error < self.tolerance_pct

        return VVVCriterion(
            name="benchmark_correlation",
            passed=passed,
            metric_value=max_error,
            tolerance=self.tolerance_pct,
            details=f"max error {max_error:.2f}% vs tolerance {self.tolerance_pct}%",
        )
