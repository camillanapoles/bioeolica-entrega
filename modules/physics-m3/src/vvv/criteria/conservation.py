"""Criterion 3/6: Conservation — massa/energia com erro < 1%.

Verification step: balanço de massa e energia no sistema acoplado.
"""
from typing import Dict, Optional

from physics_m3.vvv.certificate import VVVCriterion


class ConservationCriterion:
    """Evaluate mass and energy conservation."""

    def __init__(self, tolerance_pct: float = 1.0):
        self.tolerance_pct = tolerance_pct

    def evaluate(self, mass_balance_error_pct: float = 0.0,
                 energy_balance_error_pct: float = 0.0,
                 additional_balances: Optional[Dict[str, float]] = None) -> VVVCriterion:
        max_error = max(mass_balance_error_pct, energy_balance_error_pct)
        if additional_balances:
            max_error = max(max_error, max(additional_balances.values()))

        passed = max_error < self.tolerance_pct

        details_parts = []
        if mass_balance_error_pct >= self.tolerance_pct:
            details_parts.append(f"mass error {mass_balance_error_pct:.3f}%")
        if energy_balance_error_pct >= self.tolerance_pct:
            details_parts.append(f"energy error {energy_balance_error_pct:.3f}%")
        if additional_balances:
            for name, err in additional_balances.items():
                if err >= self.tolerance_pct:
                    details_parts.append(f"{name} error {err:.3f}%")

        return VVVCriterion(
            name="conservation",
            passed=passed,
            metric_value=max_error,
            tolerance=self.tolerance_pct,
            details="; ".join(details_parts) if details_parts else f"conserved ({max_error:.3f}%)",
        )
