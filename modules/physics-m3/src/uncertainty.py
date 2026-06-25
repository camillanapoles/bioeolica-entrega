#!/usr/bin/env python3
"""
Uncertainty Quantification Module — Monte Carlo & Sensitivity Analysis.

Conforme KDI D7: toda métrica numérica deve vir com incerteza quantificada.

Uso:
    from uncertainty import (
        MonteCarloSampler, SensitivityAnalysis,
        UncertainValue, confidence_interval
    )

    # Wrap analysis in Monte Carlo
    mc = MonteCarloSampler(n_samples=1000)
    result = mc.run(lambda E: flexure_test(E, ...),
                     distributions={"E": ("normal", 10, 1)})
    print(f"Result: {result.mean} ± {result.std}")
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
import json


@dataclass
class UncertainValue:
    """Value with uncertainty bounds."""
    nominal: float
    std: float = 0.0
    ci95_lower: float = 0.0
    ci95_upper: float = 0.0
    n_samples: int = 0

    def __str__(self) -> str:
        if self.std > 0:
            return f"{self.nominal:.2f} ± {self.std:.2f} [{self.ci95_lower:.2f}, {self.ci95_upper:.2f}]"
        return f"{self.nominal:.2f}"

    def to_dict(self) -> Dict:
        return {
            "nominal": self.nominal,
            "std": self.std,
            "ci95_lower": self.ci95_lower,
            "ci95_upper": self.ci95_upper,
            "n_samples": self.n_samples,
        }


def confidence_interval(values: np.ndarray, ci: float = 0.95) -> Tuple[float, float, float]:
    """Compute confidence interval from sample array."""
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    n = len(values)
    if n < 2:
        return mean, mean, 0.0
    z = 1.96 if ci == 0.95 else {0.90: 1.645, 0.99: 2.576}.get(ci, 1.96)
    ci_val = z * std / np.sqrt(n)
    return mean - ci_val, mean + ci_val, std


class MonteCarloSampler:
    """Monte Carlo uncertainty propagation."""

    def __init__(self, n_samples: int = 1000, seed: int = 42):
        self.n_samples = n_samples
        self.rng = np.random.default_rng(seed)
        self.results: List[float] = []

    def _sample_distribution(self, dist_type: str, *params) -> float:
        """Sample from a statistical distribution."""
        if dist_type == "normal":
            return self.rng.normal(params[0], params[1])
        elif dist_type == "uniform":
            return self.rng.uniform(params[0], params[1])
        elif dist_type == "lognormal":
            return self.rng.lognormal(params[0], params[1])
        elif dist_type == "triangular":
            return self.rng.triangular(params[0], params[1], params[2])
        return params[0]

    def run(self, func: Callable, distributions: Dict,
            **func_kwargs) -> UncertainValue:
        """Run Monte Carlo simulation.

        Args:
            func: Function to evaluate (returns float)
            distributions: Dict of {param_name: (dist_type, *params)}
            func_kwargs: Fixed keyword arguments for func

        Returns:
            UncertainValue with mean, std, confidence interval
        """
        self.results = []
        for _ in range(self.n_samples):
            kwargs = dict(func_kwargs)
            for param, dist in distributions.items():
                kwargs[param] = self._sample_distribution(*dist)
            try:
                val = func(**kwargs)
                self.results.append(float(val))
            except (ValueError, ZeroDivisionError):
                continue

        values = np.array(self.results)
        lo, hi, std = confidence_interval(values)

        return UncertainValue(
            nominal=float(np.mean(values)),
            std=std,
            ci95_lower=lo,
            ci95_upper=hi,
            n_samples=len(self.results),
        )

    def sensitivity(self, base_params: Dict, func: Callable,
                   perturbation: float = 0.1, **func_kwargs) -> Dict:
        """Simple sensitivity analysis by perturbing each parameter."""
        sensitivities = {}
        base_val = func(**{**func_kwargs, **base_params})

        for param, base in base_params.items():
            if isinstance(base, (int, float)):
                pert_val = base * (1 + perturbation)
                kwargs = {**base_params, **func_kwargs}
                kwargs[param] = pert_val
                new_val = func(**kwargs)
                sensitivities[param] = {
                    "base": base,
                    "perturbed": pert_val,
                    "base_result": float(base_val),
                    "perturbed_result": float(new_val),
                    "sensitivity": float((new_val - base_val) / base_val) / perturbation if base_val != 0 else 0,
                }

        return {
            "base_result": float(base_val),
            "sensitivities": sensitivities,
            "most_sensitive": max(sensitivities, key=lambda k: abs(sensitivities[k]["sensitivity"]))
                if sensitivities else None,
        }


def propagate_error(func: Callable, *args,
                    errors: List[float]) -> UncertainValue:
    """Simple error propagation (first-order)."""
    nominal = func(*args)
    std = np.sqrt(sum(e**2 for e in errors))
    return UncertainValue(nominal=nominal, std=std,
                          ci95_lower=nominal - 1.96 * std,
                          ci95_upper=nominal + 1.96 * std,
                          n_samples=len(errors))
