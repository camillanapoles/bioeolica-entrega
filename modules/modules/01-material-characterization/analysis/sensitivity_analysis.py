#!/usr/bin/env python3
# =============================================================================
# Sensitivity Analysis — Composite Biomaterial for Wind Energy
# Phase 2 — Material Characterization | T033
# Varies: graphite particle size, coating thickness, blasting pressure
# Outputs: tensile strength, interface adhesion, production cost index
# =============================================================================
"""
Sensitivity analysis for graphite coating parameters.

Three parameters with realistic ranges:
  - graphite_particle_size_um :    20 — 300  um (nominal 100)
  - coating_thickness_mm      :   0.1 — 2.0  mm (nominal 0.5)
  - blasting_pressure_bar     :   1.0 — 8.0  bar (nominal 4.0)

Three output metrics:
  - tensile_strength_MPa
  - interface_adhesion_MPa
  - production_cost_index (dimensionless, 1.0 = baseline)

Usage:
    python sensitivity_analysis.py

    Prints a formatted results table and optimal parameter window.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# P$1: rotear constantes pelo schema unificado
_CORE = Path(__file__).resolve()
while not (_CORE / "workspace").exists() and _CORE.parent != _CORE:
    _CORE = _CORE.parent
_CORE = _CORE / "workspace" / "lab1-material-papel-mache-grafite"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from core.constants import get
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SensitivityParameter:
    """A single parameter to vary in the sensitivity sweep."""

    name: str
    nominal_value: float
    range_min: float
    range_max: float
    unit: str
    n_steps: int = 8

    @property
    def values(self) -> List[float]:
        """Linearly spaced values from range_min to range_max (inclusive)."""
        if self.n_steps <= 1:
            return [self.nominal_value]
        step = (self.range_max - self.range_min) / (self.n_steps - 1)
        return [round(self.range_min + i * step, 2) for i in range(self.n_steps)]


@dataclass
class SensitivityResult:
    """Result of varying a single parameter for a single output metric."""

    param_name: str
    metric_name: str
    values: List[float]         # Parameter values tested
    outputs: List[float]        # Corresponding output values


@dataclass
class SensitivityMatrix:
    """Complete sensitivity sweep across all parameters and metrics."""

    param_definitions:  List[SensitivityParameter]
    metric_names:       List[str]
    results:            Dict[str, Dict[str, SensitivityResult]]
    #  results[param_name][metric_name] -> SensitivityResult

# ---------------------------------------------------------------------------
# Parameter definitions
# ---------------------------------------------------------------------------

def define_parameters() -> List[SensitivityParameter]:
    """Return the three sensitivity parameters with realistic ranges."""
    return [
        SensitivityParameter(
            name="graphite_particle_size_um",
            nominal_value=100.0,
            range_min=20.0,
            range_max=300.0,
            unit="um",
            n_steps=8,
        ),
        SensitivityParameter(
            name="coating_thickness_mm",
            nominal_value=0.5,
            range_min=0.1,
            range_max=2.0,
            unit="mm",
            n_steps=8,
        ),
        SensitivityParameter(
            name="blasting_pressure_bar",
            nominal_value=4.0,
            range_min=1.0,
            range_max=8.0,
            unit="bar",
            n_steps=8,
        ),
    ]


def define_metrics() -> List[str]:
    """Return the names of output metrics to evaluate."""
    return ["tensile_strength_MPa", "interface_adhesion_MPa", "production_cost_index"]


# ---------------------------------------------------------------------------
# Analytical scaling models
# ---------------------------------------------------------------------------

def _strength_vs_particle_size(size_um: float) -> float:
    """Tensile strength scaling with particle size.

    Smaller particles pack more densely and bridge micro-cracks more
    effectively.  Relationship follows a 1/sqrt(d) trend (Hall-Petch-like
    for composite interface), bounded to avoid singularity at d -> 0.

    Baseline at 100 um -> 12.5 MPa.
    """
    d_ref = get("modules.sensitivity.d_ref_um")
    sigma_ref = get("modules.sensitivity.sigma_ref_mpa")
    # Hall-Petch-like scaling: sigma ~ 1 / sqrt(d)
    if size_um <= 0:
        return sigma_ref * 2.0  # Bounded maximum
    ratio = math.sqrt(d_ref / size_um)
    ratio = max(0.6, min(ratio, 1.8))  # sensible bounds
    return round(sigma_ref * ratio, 2)


def _adhesion_vs_particle_size(size_um: float) -> float:
    """Interface adhesion scaling with particle size.

    Smaller particles increase surface area and mechanical interlocking.
    """
    d_ref = get("modules.sensitivity.d_ref_um")
    adh_ref = get("modules.sensitivity.adh_ref_mpa")
    if size_um <= 0:
        return adh_ref * 1.8
    ratio = math.sqrt(d_ref / size_um)
    ratio = max(0.7, min(ratio, 1.7))
    return round(adh_ref * ratio, 2)


def _cost_vs_particle_size(size_um: float) -> float:
    """Production cost index scaling with particle size.

    Finer grinding is more expensive.  Cost rises as ~ 1/d.
    """
    d_ref = 100.0
    cost_ref = 1.0
    if size_um <= 0:
        return cost_ref * 5.0
    ratio = d_ref / size_um
    ratio = max(0.3, min(ratio, 5.0))
    return round(cost_ref * ratio, 2)


def _strength_vs_coating_thickness(thick_mm: float) -> float:
    """Tensile strength scaling with coating thickness.

    Thicker coating provides more reinforcement but with diminishing
    returns (logarithmic saturation).
    """
    t_ref = get("modules.sensitivity.t_ref_mm")
    sigma_ref = get("modules.sensitivity.sigma_ref_mpa")
    ratio = 1.0 + 0.35 * math.log(max(thick_mm / t_ref, 0.01) + 1.0) / math.log(2.0)
    ratio = max(0.85, min(ratio, 1.4))
    return round(sigma_ref * ratio, 2)


def _adhesion_vs_coating_thickness(thick_mm: float) -> float:
    """Interface adhesion scaling with coating thickness.

    Thicker coating increases interfacial stress concentration, reducing
    effective adhesion beyond an optimum.
    """
    t_ref = 0.5
    adh_ref = 4.5
    # Peak adhesion near t_ref, decline at extremes
    ratio = 1.0 - 0.15 * abs(thick_mm - t_ref) / t_ref
    ratio = max(0.7, min(ratio, 1.15))
    return round(adh_ref * ratio, 2)


def _cost_vs_coating_thickness(thick_mm: float) -> float:
    """Production cost index scaling with coating thickness.

    More material + longer blasting time -> higher cost ~ linear.
    """
    t_ref = 0.5
    cost_ref = 1.0
    ratio = thick_mm / t_ref
    ratio = max(0.3, min(ratio, 4.0))
    return round(cost_ref * ratio, 2)


def _strength_vs_blasting_pressure(p_bar: float) -> float:
    """Tensile strength scaling with blasting pressure.

    Higher pressure embeds particles more deeply, improving reinforcement
    up to a saturation point (diminishing returns + potential damage).
    """
    p_ref = get("modules.sensitivity.p_ref_bar")
    sigma_ref = get("modules.sensitivity.sigma_ref_mpa")
    # Sigmoidal approach to saturation
    ratio = 1.0 + 0.3 * (p_bar - p_ref) / (abs(p_bar - p_ref) + 3.0)
    ratio = max(0.85, min(ratio, 1.25))
    return round(sigma_ref * ratio, 2)


def _adhesion_vs_blasting_pressure(p_bar: float) -> float:
    """Interface adhesion scaling with blasting pressure.

    Initial increase as particles embed, plateau, then slight decline
    at very high pressure (substrate damage).
    """
    p_ref = 4.0
    adh_ref = 4.5
    # plateaus ~6 bar then gently declines
    if p_bar <= 6.0:
        ratio = 1.0 + 0.3 * (p_bar - p_ref) / (abs(p_bar - p_ref) + 2.0)
    else:
        ratio = 1.15 - 0.05 * (p_bar - 6.0)
    ratio = max(0.8, min(ratio, 1.2))
    return round(adh_ref * ratio, 2)


def _cost_vs_blasting_pressure(p_bar: float) -> float:
    """Production cost index scaling with blasting pressure.

    Higher pressure consumes more compressed air, increasing cost.
    """
    p_ref = 4.0
    cost_ref = 1.0
    ratio = 1.0 + 0.2 * (p_bar - p_ref)
    ratio = max(0.7, min(ratio, 2.5))
    return round(cost_ref * ratio, 2)


# ---------------------------------------------------------------------------
# Sealed dispatch table
# ---------------------------------------------------------------------------

# Map (parameter_name, metric_name) -> analytical model function
_SCALING_MODELS: Dict[Tuple[str, str], Callable[[float], float]] = {
    ("graphite_particle_size_um",  "tensile_strength_MPa"):    _strength_vs_particle_size,
    ("graphite_particle_size_um",  "interface_adhesion_MPa"):  _adhesion_vs_particle_size,
    ("graphite_particle_size_um",  "production_cost_index"):   _cost_vs_particle_size,
    ("coating_thickness_mm",       "tensile_strength_MPa"):    _strength_vs_coating_thickness,
    ("coating_thickness_mm",       "interface_adhesion_MPa"):  _adhesion_vs_coating_thickness,
    ("coating_thickness_mm",       "production_cost_index"):   _cost_vs_coating_thickness,
    ("blasting_pressure_bar",      "tensile_strength_MPa"):    _strength_vs_blasting_pressure,
    ("blasting_pressure_bar",      "interface_adhesion_MPa"):  _adhesion_vs_blasting_pressure,
    ("blasting_pressure_bar",      "production_cost_index"):   _cost_vs_blasting_pressure,
}


# ---------------------------------------------------------------------------
# Sensitivity runs
# ---------------------------------------------------------------------------

def run_sensitivity(param: SensitivityParameter, metric_name: str) -> SensitivityResult:
    """Evaluate *metric_name* across the range of *param*.

    Returns
    -------
    SensitivityResult
        Lists of parameter values and corresponding output values.
    """
    model = _SCALING_MODELS.get((param.name, metric_name))
    if model is None:
        raise ValueError(f"No scaling model for param={param.name!r} metric={metric_name!r}")

    values = param.values
    outputs = [model(v) for v in values]

    return SensitivityResult(
        param_name=param.name,
        metric_name=metric_name,
        values=values,
        outputs=outputs,
    )


def create_sensitivity_matrix(
    params: List[SensitivityParameter],
    metrics: List[str],
) -> SensitivityMatrix:
    """Run all parameter x metric combinations.

    Returns
    -------
    SensitivityMatrix
        Nested dict with results[param_name][metric_name].
    """
    results: Dict[str, Dict[str, SensitivityResult]] = {}
    for p in params:
        results[p.name] = {}
        for m in metrics:
            results[p.name][m] = run_sensitivity(p, m)

    return SensitivityMatrix(
        param_definitions=params,
        metric_names=metrics,
        results=results,
    )


# ---------------------------------------------------------------------------
# Optimal window
# ---------------------------------------------------------------------------

def find_optimal_window(matrix: SensitivityMatrix) -> Dict[str, object]:
    """Identify parameter ranges where ALL metrics are acceptable.

    Acceptability criteria (applied at baseline normalisation):
      - tensile_strength_MPa       >= 11.0
      - interface_adhesion_MPa     >= 3.5
      - production_cost_index      <= 2.0

    Returns
    -------
    dict with keys:
        ``optimal_params``  — dict of param_name -> (low, high, nominal)
        ``nominal_metrics`` — predicted outputs at chosen nominal
        ``justification``   — textual rationale
    """
    opt_params: Dict[str, Dict[str, float]] = {}
    nominal_point: Dict[str, float] = {}

    for p in matrix.param_definitions:
        param_vals = p.values
        feasible_mask = [True] * len(param_vals)

        # For each metric, check which parameter values are acceptable
        for m in matrix.metric_names:
            res = matrix.results[p.name][m]
            for i, out_val in enumerate(res.outputs):
                if m == "tensile_strength_MPa" and out_val < 11.0:
                    feasible_mask[i] = False
                elif m == "interface_adhesion_MPa" and out_val < 3.5:
                    feasible_mask[i] = False
                elif m == "production_cost_index" and out_val > 2.0:
                    feasible_mask[i] = False

        feasible_vals = [param_vals[i] for i in range(len(param_vals)) if feasible_mask[i]]

        if feasible_vals:
            low = min(feasible_vals)
            high = max(feasible_vals)
            # Pick the closest feasible value to nominal
            nom_val = min(feasible_vals, key=lambda v: abs(v - p.nominal_value))
        else:
            # No feasible point — fall back to nominal
            low = p.nominal_value
            high = p.nominal_value
            nom_val = p.nominal_value

        opt_params[p.name] = {"low": low, "high": high, "nominal": nom_val}
        nominal_point[p.name] = nom_val

    # Compute predicted outputs at chosen nominal point
    nominal_metrics: Dict[str, float] = {}
    for p in matrix.param_definitions:
        for m in matrix.metric_names:
            model = _SCALING_MODELS.get((p.name, m))
            if model is not None:
                val = model(nominal_point[p.name])
                # For multi-parameter metrics, pick the most conservative
                if m in nominal_metrics:
                    nominal_metrics[m] = min(nominal_metrics[m], val)
                else:
                    nominal_metrics[m] = val

    return {
        "optimal_params": opt_params,
        "nominal_metrics": nominal_metrics,
        "justification": _build_justification(opt_params, nominal_metrics),
    }


def _build_justification(
    opt_params: Dict[str, Dict[str, float]],
    nominal_metrics: Dict[str, float],
) -> str:
    """Build a human-readable justification for the selected window."""
    lines: List[str] = []
    lines.append("Optimal parameter window selected to maximise the "
                 "strength-adhesion-cost tradeoff.")
    lines.append("")
    for pname, bounds in opt_params.items():
        lines.append(
            f"  {pname:30s}  range [{bounds['low']:.1f}, {bounds['high']:.1f}]  "
            f"nominal {bounds['nominal']:.1f}"
        )
    lines.append("")
    lines.append("Predicted performance at nominal point:")
    for mname, val in nominal_metrics.items():
        lines.append(f"  {mname:30s}  {val:.2f}")
    lines.append("")
    lines.append("Constraints applied:")
    lines.append("  tensile_strength_MPa   >= 11.0")
    lines.append("  interface_adhesion_MPa >=  3.5")
    lines.append("  production_cost_index  <=  2.0")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_table_row(
    label: str,
    values: List[float],
    width: int = 8,
    decimals: int = 2,
) -> str:
    """Build a single row of the formatted output table."""
    cells = "  ".join(f"{v:>{width}.{decimals}f}" for v in values)
    return f"  {label:30s} | {cells}"


def print_sensitivity_table(matrix: SensitivityMatrix) -> None:
    """Print a formatted sensitivity table to stdout."""
    sep = "=" * 90

    for p in matrix.param_definitions:
        print(sep)
        print(f"  Parameter: {p.name}  [{p.unit}]")
        print(sep)

        values = p.values
        header = "  Value".rjust(30)
        for v in values:
            header += f"  {v:>8.2f}"
        print(header)
        print("  " + "-" * 88)

        for m in matrix.metric_names:
            res = matrix.results[p.name][m]
            print(_fmt_table_row(m, res.outputs))

        print()

    print(sep)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run full sensitivity sweep and print results."""
    params = define_parameters()
    metrics = define_metrics()

    print()
    print("=" * 90)
    print("  SENSITIVITY ANALYSIS — Graphite Coating Parameters")
    print("=" * 90)

    matrix = create_sensitivity_matrix(params, metrics)
    print_sensitivity_table(matrix)

    print("\n  Finding optimal parameter window...")
    print()
    optimum = find_optimal_window(matrix)

    print("-" * 90)
    print("  OPTIMAL WINDOW")
    print("-" * 90)
    print()
    print(optimum["justification"])
    print("-" * 90)


if __name__ == "__main__":
    main()
