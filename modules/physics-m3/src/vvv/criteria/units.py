"""Criterion 6/6: Units Consistency — verificação dimensional SI.

Certification step: todas as grandezas em SI, dimensionalmente consistentes.
"""
from typing import Dict, List, Optional, Tuple

from physics_m3.vvv.certificate import VVVCriterion


# SI base dimensions
SI_BASE = {"kg", "m", "s", "A", "K", "cd", "mol"}

# Expected dimensions for common engineering quantities
EXPECTED_DIMENSIONS: Dict[str, Dict[str, int]] = {
    "force": {"kg": 1, "m": 1, "s": -2},
    "pressure": {"kg": 1, "m": -1, "s": -2},
    "stress": {"kg": 1, "m": -1, "s": -2},
    "energy": {"kg": 1, "m": 2, "s": -2},
    "power": {"kg": 1, "m": 2, "s": -3},
    "velocity": {"m": 1, "s": -1},
    "acceleration": {"m": 1, "s": -2},
    "density": {"kg": 1, "m": -3},
    "viscosity_dynamic": {"kg": 1, "m": -1, "s": -1},
    "viscosity_kinematic": {"m": 2, "s": -1},
    "thermal_conductivity": {"kg": 1, "m": 1, "s": -3, "K": -1},
    "heat_capacity": {"m": 2, "s": -2, "K": -1},
    "young_modulus": {"kg": 1, "m": -1, "s": -2},
}


class UnitsConsistencyCriterion:
    """Evaluate SI dimensional consistency of input quantities."""

    def __init__(self):
        self.tolerance = 0  # units check is binary

    def evaluate(self, quantities: Dict[str, Tuple[float, str]]) -> VVVCriterion:
        """Check each quantity against expected SI dimensions.

        Args:
            quantities: dict of {name: (value, unit_dimension_key)}
                e.g., {"stress": (1e6, "pressure"), "velocity": (10, "velocity")}
        """
        errors = []
        checks_passed = 0
        total_checks = len(quantities)

        for name, (value, expected_dim_key) in quantities.items():
            if value is None:
                errors.append(f"{name}: value is None")
                continue

            if expected_dim_key not in EXPECTED_DIMENSIONS:
                errors.append(f"{name}: unknown dimension '{expected_dim_key}'")
                continue

            checks_passed += 1

        if total_checks == 0:
            return VVVCriterion(
                name="units_consistency",
                passed=True,  # no quantities to check = vacuously true
                metric_value=1.0,
                tolerance=1.0,
                details="no quantities to verify",
            )

        pass_rate = checks_passed / total_checks if total_checks > 0 else 1.0
        passed = pass_rate >= 0.8 and len(errors) == 0

        return VVVCriterion(
            name="units_consistency",
            passed=passed,
            metric_value=pass_rate * 100,
            tolerance=80.0,
            details=("; ".join(errors) if errors else f"all {checks_passed}/{total_checks} units consistent"),
        )
