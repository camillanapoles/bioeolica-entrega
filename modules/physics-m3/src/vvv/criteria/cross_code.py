"""Criterion 5/6: Cross-Code — 2+ implementações independentes concordam.

Validation step: comparar resultados entre métodos numéricos distintos.
Usa VVVReport.CrossValidation.compare() do vvv_protocol.
"""
from typing import List, Optional

from physics_m3.vvv.certificate import VVVCriterion


class CrossCodeCriterion:
    """Evaluate agreement between independent implementations."""

    def __init__(self, tolerance_pct: float = 5.0):
        self.tolerance_pct = tolerance_pct

    def evaluate(self, method_a_values: List[float],
                 method_b_values: List[float],
                 method_a_name: str = "A",
                 method_b_name: str = "B") -> VVVCriterion:
        if len(method_a_values) != len(method_b_values):
            return VVVCriterion(
                name="cross_code",
                passed=False,
                metric_value=-1,
                tolerance=self.tolerance_pct,
                details=f"array length mismatch: {len(method_a_values)} vs {len(method_b_values)}",
            )

        if not method_a_values:
            return VVVCriterion(
                name="cross_code",
                passed=False,
                metric_value=-1,
                tolerance=self.tolerance_pct,
                details="no data provided",
            )

        errors = []
        for a, b in zip(method_a_values, method_b_values):
            if abs(a) > 0:
                errors.append(abs(a - b) / abs(a) * 100)

        if not errors:
            return VVVCriterion(
                name="cross_code",
                passed=False,
                metric_value=-1,
                tolerance=self.tolerance_pct,
                details="all reference values are zero",
            )

        max_error = max(errors)
        mean_error = sum(errors) / len(errors)
        passed = max_error < self.tolerance_pct

        details = f"{method_a_name} vs {method_b_name}: max Δ={max_error:.2f}%, mean Δ={mean_error:.2f}%"
        if not passed:
            details += f" exceeds {self.tolerance_pct}% tolerance"

        return VVVCriterion(
            name="cross_code",
            passed=passed,
            metric_value=max_error,
            tolerance=self.tolerance_pct,
            details=details,
        )
