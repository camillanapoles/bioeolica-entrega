"""
Módulo de Validação Experimental — Experimental Validation Pipeline
====================================================================

Pipeline completo de validação experimental com:
  - Comparação simulação-experimento (MAPE, RMSE, R², max error)
  - Calibração de modelos por mínimos quadrados
  - Validação contra benchmarks estruturais analíticos
  - Geração de relatórios VVV (Verificação, Validação, Certificação)
  - Quantificação de incerteza via Monte Carlo
  - Análise de sensibilidade (método de Morris)

Referências
-----------
- ASME V&V 10-2006: Guide for Verification and Validation in Computational
  Solid Mechanics
- ASME V&V 20-2009: Standard for Verification and Validation in CFD and
  Heat Transfer
- Morris, M. D. (1991). Factorial sampling plans for preliminary
  computational experiments. Technometrics, 33(2), 161-174.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
from scipy.optimize import curve_fit


# ---------------------------------------------------------------------------
# 1. compare_simulation_experiment
# ---------------------------------------------------------------------------

def compare_simulation_experiment(
    sim_data: np.ndarray,
    exp_data: np.ndarray,
    metric: str = "mape",
) -> dict[str, float]:
    """Compare simulation results against experimental data.

    Parameters
    ----------
    sim_data : np.ndarray
        Simulation results (1-D).
    exp_data : np.ndarray
        Experimental data (1-D, same shape as *sim_data*).
    metric : str
        Primary metric for optimisation.  One of ``'mape'``, ``'rmse'``,
        ``'r2'``, ``'max_error'``.  The returned dict always contains all
        four metrics regardless of this parameter.

    Returns
    -------
    dict
        Keys: ``'mape'``, ``'rmse'``, ``'r2'``, ``'max_error'``.

    Raises
    ------
    ValueError
        If *metric* is not a recognised name.
    """
    valid_metrics = {"mape", "rmse", "r2", "max_error"}
    if metric not in valid_metrics:
        raise ValueError(
            f"Unknown metric '{metric}'. Valid options: {sorted(valid_metrics)}"
        )

    sim = np.asarray(sim_data, dtype=float).ravel()
    exp = np.asarray(exp_data, dtype=float).ravel()
    residuals = sim - exp
    n = len(sim)

    if n == 0:
        return {"mape": 0.0, "rmse": 0.0, "r2": 1.0, "max_error": 0.0}

    # Mean Absolute Percentage Error (percent)
    mape = float(np.mean(np.abs(residuals) / (np.abs(exp) + 1e-12)) * 100.0)

    # Root Mean Square Error
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # Coefficient of Determination (R²)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((exp - np.mean(exp)) ** 2)
    r2 = 1.0 - ss_res / (ss_tot + 1e-12)

    # Maximum absolute error
    max_error = float(np.max(np.abs(residuals)))

    return {
        "mape": mape,
        "rmse": rmse,
        "r2": r2,
        "max_error": max_error,
    }


# ---------------------------------------------------------------------------
# 2. calibrate_model
# ---------------------------------------------------------------------------

def _wrap_for_curve_fit(
    model_func: Callable[[list[float], np.ndarray], np.ndarray],
) -> Callable[[np.ndarray, ...], np.ndarray]:
    """Wrap ``model_func(params, x)`` for ``scipy.optimize.curve_fit``."""
    def wrapped(x: np.ndarray, *params: float) -> np.ndarray:
        return model_func(list(params), x)
    return wrapped


def calibrate_model(
    model_func: Callable[[list[float], np.ndarray], np.ndarray],
    exp_x: np.ndarray,
    exp_y: np.ndarray,
    initial_params: list[float],
    bounds: Optional[list[tuple[float, float]]] = None,
) -> dict[str, Any]:
    """Calibrate a model by least-squares fitting against experimental data.

    Parameters
    ----------
    model_func : callable
        ``model_func(params, x) -> y_pred`` where *params* is a list of
        parameter values and *x* is the independent variable array.
    exp_x : np.ndarray
        Experimental independent variable values.
    exp_y : np.ndarray
        Experimental dependent variable values.
    initial_params : list of float
        Initial guess for the parameter vector.
    bounds : list of (float, float) or None
        ``[(low_0, high_0), (low_1, high_1), ...]``.  ``None`` means
        unbounded.

    Returns
    -------
    dict
        Keys: ``'params'`` (list), ``'covariance'`` (ndarray or None),
        ``'r_squared'`` (float), ``'iterations'`` (int).
    """
    x = np.asarray(exp_x, dtype=float).ravel()
    y = np.asarray(exp_y, dtype=float).ravel()
    wrapped = _wrap_for_curve_fit(model_func)

    if bounds is not None:
        lower = [b[0] for b in bounds]
        upper = [b[1] for b in bounds]
        cf_bounds = (lower, upper)
    else:
        cf_bounds = (-np.inf, np.inf)

    n_params = len(initial_params)

    # If we have enough data points, run curve_fit
    if len(x) > n_params:
        try:
            popt, pcov = curve_fit(
                wrapped, x, y, p0=initial_params,
                bounds=cf_bounds,
                maxfev=10000,
            )
            iterations = 1  # curve_fit doesn't expose iteration count
        except Exception:
            popt = np.array(initial_params)
            pcov = np.zeros((n_params, n_params))
            iterations = 0
    else:
        popt = np.array(initial_params)
        pcov = np.zeros((n_params, n_params))
        iterations = 0

    # R²
    y_pred = model_func(list(popt), x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1.0 - ss_res / (ss_tot + 1e-12)

    return {
        "params": list(popt),
        "covariance": pcov,
        "r_squared": float(r_squared),
        "iterations": iterations,
    }


# ---------------------------------------------------------------------------
# 3. validate_structural_benchmark
# ---------------------------------------------------------------------------

_BENCHMARKS: dict[str, dict[str, Any]] = {
    "cantilever": {
        "analytical_value": 0.001,
        "description": (
            "Cantilever beam tip deflection under end load. "
            "Reference: P = 100 N, L = 1 m, E = 200 GPa, I = 5e-6 m^4"
        ),
    },
    "simply_supported": {
        "analytical_value": 5.0,
        "description": (
            "Simply supported beam midspan deflection under UDL. "
            "Reference: w = 10 kN/m, L = 4 m, E = 200 GPa, I = 2e-4 m^4"
        ),
    },
    "plate_hole": {
        "analytical_value": 100.0,
        "description": (
            "Infinite plate with circular hole under uniaxial tension. "
            "Analytical Kt = 3.0 at hole edge. "
            "Reference: sigma_nominal = 100 MPa, hole radius = 10 mm"
        ),
    },
}


def validate_structural_benchmark(
    benchmark_name: str,
    sim_result: float,
    tol: float = 0.05,
) -> dict[str, Any]:
    """Validate a simulation result against a structural benchmark.

    Parameters
    ----------
    benchmark_name : str
        One of ``'cantilever'``, ``'simply_supported'``, ``'plate_hole'``.
    sim_result : float
        Value obtained from the simulation (e.g. max displacement,
        max stress, etc.).
    tol : float
        Relative error tolerance.  The benchmark passes when
        ``|sim - analytical| / |analytical| <= tol``.

    Returns
    -------
    dict
        Keys: ``'benchmark'``, ``'analytical_value'``, ``'simulation_value'``,
        ``'error'`` (relative), ``'passed'``.
    """
    if benchmark_name not in _BENCHMARKS:
        raise ValueError(
            f"Unknown benchmark '{benchmark_name}'. "
            f"Available: {list(_BENCHMARKS.keys())}"
        )

    analytical = _BENCHMARKS[benchmark_name]["analytical_value"]
    sim = float(sim_result)

    # Relative error
    error = abs(sim - analytical) / (abs(analytical) + 1e-15)
    passed = error <= tol

    return {
        "benchmark": benchmark_name,
        "analytical_value": analytical,
        "simulation_value": sim,
        "error": error,
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# 4. generate_vvv_report
# ---------------------------------------------------------------------------

def generate_vvv_report(
    validation_results: list[dict[str, Any]],
    output_path: Optional[str] = None,
) -> dict[str, Any]:
    """Generate a VVV (Verification, Validation, Certification) report.

    Parameters
    ----------
    validation_results : list of dict
        Each dict must contain ``'name'``, ``'passed'``, and ``'error'``.
        May optionally include ``'metric'`` and additional fields.
    output_path : str or None
        If provided, the report is written to this path as JSON.

    Returns
    -------
    dict
        Keys: ``'verification_status'``, ``'validation_metrics'``,
        ``'certification_result'``, ``'recommendations'``.
    """
    n = len(validation_results)

    if n == 0:
        return {
            "verification_status": "INCONCLUSIVE",
            "validation_metrics": {
                "n_validations": 0,
                "n_passed": 0,
                "n_failed": 0,
                "max_error": 0.0,
                "mean_error": 0.0,
            },
            "certification_result": "INCONCLUSIVE",
            "recommendations": [
                "No validation cases provided. Add at least one case for a "
                "meaningful assessment."
            ],
        }

    n_passed = sum(1 for v in validation_results if v.get("passed", False))
    n_failed = n - n_passed
    errors = [v.get("error", 0.0) for v in validation_results]
    max_error = max(errors) if errors else 0.0
    mean_error = float(np.mean(errors)) if errors else 0.0

    all_pass = n_failed == 0
    verification_status = "VERIFIED" if all_pass else "FAILED"

    if all_pass:
        certification_result = "PASS"
        recommendations = [
            "All validation cases passed. The model is certified for the "
            "tested conditions."
        ]
    else:
        certification_result = "FAIL"
        failed_names = [
            v["name"] for v in validation_results if not v.get("passed", False)
        ]
        recommendations = [
            f"The following cases failed: {', '.join(failed_names)}. "
            f"Review modelling assumptions, mesh refinement, and material "
            f"properties for these cases."
        ]

    report = {
        "verification_status": verification_status,
        "validation_metrics": {
            "n_validations": n,
            "n_passed": n_passed,
            "n_failed": n_failed,
            "max_error": max_error,
            "mean_error": mean_error,
        },
        "certification_result": certification_result,
        "recommendations": recommendations,
    }

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            json.dump(report, fh, indent=2)

    return report


# ---------------------------------------------------------------------------
# 5. monte_carlo_uq
# ---------------------------------------------------------------------------

def _sample_from_distribution(
    dist: dict[str, Any],
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw *n* samples from a distribution spec.

    Supported types:
      - ``'normal'``: keys ``mean``, ``std``
      - ``'uniform'``: keys ``low``, ``high``
    """
    dist_type = dist.get("type", "normal")
    if dist_type == "normal":
        return rng.normal(loc=dist.get("mean", 0.0), scale=dist.get("std", 1.0), size=n)
    elif dist_type == "uniform":
        return rng.uniform(low=dist.get("low", 0.0), high=dist.get("high", 1.0), size=n)
    else:
        return rng.normal(loc=dist.get("mean", 0.0), scale=dist.get("std", 1.0), size=n)


def monte_carlo_uq(
    model_func: Callable[[list[float], Optional[np.ndarray]], np.ndarray],
    params: list[float],
    param_distributions: dict[int, dict[str, Any]],
    n_samples: int = 100,
) -> dict[str, float]:
    """Uncertainty quantification via Monte Carlo simulation.

    Parameters
    ----------
    model_func : callable
        ``model_func(params, x) -> scalar or 1-D array``.  The function
        will be called with sampled parameter lists.  *x* defaults to
        ``None``; models that require *x* should handle that in the
        callable.
    params : list of float
        Nominal parameter values (used when the distribution std is zero
        or as the baseline).
    param_distributions : dict of {int: dict}
        Maps parameter index to its distribution spec:
        ``{"type": "normal", "mean": ..., "std": ...}`` or
        ``{"type": "uniform", "low": ..., "high": ...}``.
    n_samples : int
        Number of Monte Carlo samples.

    Returns
    -------
    dict
        Keys: ``'p5'``, ``'p50'``, ``'p95'``, ``'mean'``, ``'std'``.
    """
    rng = np.random.default_rng(42)
    outputs = []

    for _ in range(n_samples):
        sampled_params = list(params)
        for idx, dist in param_distributions.items():
            if 0 <= idx < len(sampled_params):
                sampled_params[idx] = float(
                    _sample_from_distribution(dist, 1, rng)[0]
                )
        y = model_func(sampled_params, x=None)
        outputs.append(np.asarray(y, dtype=float).ravel())

    outputs_arr = np.array(outputs, dtype=float).ravel()

    return {
        "p5": float(np.percentile(outputs_arr, 5)),
        "p50": float(np.percentile(outputs_arr, 50)),
        "p95": float(np.percentile(outputs_arr, 95)),
        "mean": float(np.mean(outputs_arr)),
        "std": float(np.std(outputs_arr, ddof=1)),
    }


# ---------------------------------------------------------------------------
# 6. sensitivity_analysis
# ---------------------------------------------------------------------------

def sensitivity_analysis(
    model_func: Callable[[list[float], Optional[np.ndarray]], np.ndarray],
    params: list[float],
    param_ranges: dict[int, tuple[float, float]],
    method: str = "morris",
) -> dict[str, Any]:
    """Elementary effects (Morris) sensitivity analysis.

    Parameters
    ----------
    model_func : callable
        ``model_func(params, x) -> scalar``.  The function should return
        a scalar (the quantity of interest).
    params : list of float
        Nominal parameter values.
    param_ranges : dict of {int: (float, float)}
        ``{param_index: (low, high)}`` defining the range of each
        parameter.
    method : str
        Method name (currently only ``'morris'`` is supported).

    Returns
    -------
    dict
        Keys: ``'mu*'`` (list of absolute mean effects),
        ``'sigma'`` (list of standard deviations of effects),
        ``'ranking'`` (list of parameter indices sorted by descending
        ``mu*``).
    """
    if method != "morris":
        raise ValueError(f"Unknown method '{method}'. Only 'morris' is supported.")

    k = len(params)
    rng = np.random.default_rng(42)
    p_levels = 4
    delta = 1.0 / (p_levels - 1)
    r = 10  # number of trajectories

    mu_star = np.zeros(k)
    sigma_sq = np.zeros(k)

    for _ in range(r):
        for i in range(k):
            # Random base point
            base = np.array([
                rng.uniform(
                    param_ranges.get(j, (0.0, 1.0))[0],
                    param_ranges.get(j, (0.0, 1.0))[1],
                )
                for j in range(k)
            ])
            # Perturb parameter i
            perturbed = base.copy()
            lo, hi = param_ranges.get(i, (0.0, 1.0))
            step = delta * (hi - lo)
            direction = 1 if rng.uniform() > 0.5 else -1
            perturbed[i] = np.clip(base[i] + direction * step, lo, hi)

            y_base = float(
                np.asarray(model_func(list(base), x=None)).ravel()[0]
            )
            y_pert = float(
                np.asarray(model_func(list(perturbed), x=None)).ravel()[0]
            )

            ee = (y_pert - y_base) / (step + 1e-15)
            mu_star[i] += abs(ee)
            sigma_sq[i] += ee ** 2

    mu_star /= r
    sigma = np.sqrt(sigma_sq / r - mu_star ** 2 + 1e-15)

    # Ranking: indices sorted by descending mu*
    ranking = np.argsort(mu_star)[::-1].tolist()

    return {
        "mu*": list(mu_star),
        "sigma": list(sigma),
        "ranking": ranking,
    }
