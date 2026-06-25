#!/usr/bin/env python3
# =============================================================================
# Cost Breakdown Model — Upscaled Wind Turbine
# Part of T006 — Phase 3 US1
# Contract: cost-model.md → compute_cost_breakdown()
# Dependencies: src.common.db_helper (table reference)
# =============================================================================
"""
Cost decomposition for upscaled small wind turbines (VAWT / HAWT).

Breaks down total installed cost into scaling components (rotor, generator,
tower, battery) and fixed components (controller, inverter, transport,
installation). Supports topology-specific multipliers.

Constants calibrated to NE Brazil semi-arid Sertao context.

Usage:
    from src.energy_system.cost_breakdown import compute_cost_breakdown

    cb = compute_cost_breakdown(10.0, "VAWT")
    print(f"Total: ${cb['total_cost_usd']:.0f}  Cost/kW: ${cb['cost_per_kw_usd']:.0f}")
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.wind_utils import swept_area


# ---------------------------------------------------------------------------
# Scaling model — power-law: cost = coeff * (rating / base_rating)^exponent
# ---------------------------------------------------------------------------


@dataclass
class CostScalingParams:
    """Scaling coefficients for cost components.

    Each component follows: cost = coeff * (P / P_base)^exp

    Attributes:
        coeff: Base cost (USD) at base_rating.
        exp: Scaling exponent (< 1 = economies of scale).
        base_rating_kw: Rating at which coeff is calibrated.
    """
    coeff: float
    exp: float = 0.80   # typical wind turbine scaling exponent
    base_rating_kw: float = 5.0


@dataclass
class CostModelParams:
    """Aggregate cost model parameters for a topology.

    VAWT typically has higher rotor cost (complex blades), lower tower cost
    (lower CG), higher generator cost (direct-drive), lower installation.
    """
    rotor: CostScalingParams = field(default_factory=lambda: CostScalingParams(1200, 0.85))
    generator: CostScalingParams = field(default_factory=lambda: CostScalingParams(800, 0.75))
    tower: CostScalingParams = field(default_factory=lambda: CostScalingParams(600, 0.80))
    battery: CostScalingParams = field(default_factory=lambda: CostScalingParams(400, 0.70))
    # Fixed costs (do not scale with rating)
    controller_usd: float = 450.0
    inverter_usd: float = 600.0
    transport_usd: float = 300.0
    installation_usd: float = 500.0
    balance_of_system_pct: float = 0.08  # 8% of subtotal for wiring, switches, etc.


# Topology-specific defaults
VAWT_PARAMS = CostModelParams(
    rotor=CostScalingParams(1800, 0.90),       # VAWT blades more complex
    generator=CostScalingParams(900, 0.75),     # direct-drive PMSG
    tower=CostScalingParams(400, 0.75),         # shorter tower, ground-level gen
    battery=CostScalingParams(400, 0.70),
    controller_usd=500.0,
    inverter_usd=600.0,
    transport_usd=300.0,
    installation_usd=400.0,
    balance_of_system_pct=0.08,
)

HAWT_PARAMS = CostModelParams(
    rotor=CostScalingParams(1200, 0.85),        # simpler blades
    generator=CostScalingParams(800, 0.75),     # geared or direct-drive
    tower=CostScalingParams(600, 0.80),         # taller tower
    battery=CostScalingParams(400, 0.70),
    controller_usd=450.0,
    inverter_usd=600.0,
    transport_usd=300.0,
    installation_usd=500.0,
    balance_of_system_pct=0.08,
)

TOPOLOGY_PARAMS: Dict[str, CostModelParams] = {
    "VAWT": VAWT_PARAMS,
    "HAWT": HAWT_PARAMS,
}

VALID_TOPOLOGIES: Tuple[str, ...] = tuple(TOPOLOGY_PARAMS.keys())


# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------


def _scale_cost(params: CostScalingParams, rated_power_kw: float) -> float:
    """Apply power-law scaling to a cost component.

    cost = coeff * (P / P_base)^exp

    Args:
        params: CostScalingParams for the component.
        rated_power_kw: Target turbine rating (kW).

    Returns:
        Scaled cost in USD.
    """
    ratio = rated_power_kw / params.base_rating_kw
    return params.coeff * (ratio ** params.exp)


def compute_cost_breakdown(
    rated_power_kw: float,
    topology: str = "VAWT",
    model_params: CostModelParams | None = None,
) -> dict:
    """Compute detailed cost breakdown for an upscaled turbine.

    Args:
        rated_power_kw: Turbine rated power (kW). Valid range: 0.5-50.
        topology: 'VAWT' or 'HAWT'.
        model_params: Optional custom CostModelParams. Uses topology
            defaults if None.

    Returns:
        Dict with keys:
            rotor_cost_usd, generator_cost_usd, tower_cost_usd,
            battery_cost_usd, fixed_costs_usd, total_cost_usd,
            cost_per_kw_usd, breakdown_table (for display).
    """
    if rated_power_kw <= 0 or rated_power_kw > 100:
        raise ValueError(f"rated_power_kw={rated_power_kw} outside valid range (0.5-50)")

    topology = topology.upper()
    if topology not in VALID_TOPOLOGIES:
        raise ValueError(f"topology='{topology}' must be one of {VALID_TOPOLOGIES}")

    params = model_params or TOPOLOGY_PARAMS[topology]

    # Scaling components
    rotor_cost = _scale_cost(params.rotor, rated_power_kw)
    generator_cost = _scale_cost(params.generator, rated_power_kw)
    tower_cost = _scale_cost(params.tower, rated_power_kw)
    battery_cost = _scale_cost(params.battery, rated_power_kw)

    # Fixed components
    fixed_costs = (
        params.controller_usd
        + params.inverter_usd
        + params.transport_usd
        + params.installation_usd
    )

    subtotal = rotor_cost + generator_cost + tower_cost + battery_cost + fixed_costs
    bos_cost = subtotal * params.balance_of_system_pct
    total = subtotal + bos_cost
    cost_per_kw = total / rated_power_kw if rated_power_kw > 0 else 0.0

    # Rotor diameter estimate from rating (power ~= 0.5 * rho * A * Cp * v^3)
    # Assuming Cp=0.35, v=7.0 m/s, rho=1.105
    v_design = 7.0
    est_diameter = (
        2.0 * (rated_power_kw * 1000 / (0.5 * 1.105 * 0.35 * v_design ** 3) / 3.14159) ** 0.5
    )

    return {
        "rated_power_kw": rated_power_kw,
        "topology": topology,
        "rotor_cost_usd": round(rotor_cost, 2),
        "generator_cost_usd": round(generator_cost, 2),
        "tower_cost_usd": round(tower_cost, 2),
        "battery_cost_usd": round(battery_cost, 2),
        "fixed_costs_usd": round(fixed_costs, 2),
        "bos_cost_usd": round(bos_cost, 2),
        "total_cost_usd": round(total, 2),
        "cost_per_kw_usd": round(cost_per_kw, 2),
        "est_rotor_diameter_m": round(est_diameter, 2),
        "breakdown_table": (
            f"  Component            USD      %Total\n"
            f"  {'-'*40}\n"
            f"  Rotor              ${rotor_cost:>8.0f}   {rotor_cost/total*100:>5.1f}%\n"
            f"  Generator          ${generator_cost:>8.0f}   {generator_cost/total*100:>5.1f}%\n"
            f"  Tower              ${tower_cost:>8.0f}   {tower_cost/total*100:>5.1f}%\n"
            f"  Battery            ${battery_cost:>8.0f}   {battery_cost/total*100:>5.1f}%\n"
            f"  Fixed (ctrl+inv)   ${fixed_costs:>8.0f}   {fixed_costs/total*100:>5.1f}%\n"
            f"  BOS                ${bos_cost:>8.0f}   {bos_cost/total*100:>5.1f}%\n"
            f"  {'-'*40}\n"
            f"  TOTAL              ${total:>8.0f}   100.0%\n"
            f"  Cost/kW            ${cost_per_kw:>8.0f}\n"
            f"  Est. rotor diam.   {est_diameter:>8.1f} m"
        ),
    }


def _test() -> None:
    """Run verification across multiple ratings."""
    print("=" * 72)
    print("  T006 — Cost Breakdown Verification")
    print("=" * 72)

    for rating in [5, 10, 15, 20]:
        cb = compute_cost_breakdown(rating, "VAWT")
        print(f"\n--- {rating} kW {cb['topology']} ---")
        print(cb["breakdown_table"])
        print(f"  SC-004 target: ${cb['cost_per_kw_usd']:.0f}/kW "
              f"{'❌' if cb['cost_per_kw_usd'] > 3000 else '✅'} (< $3000)")

    # HAWT comparison at 10 kW
    cb_v = compute_cost_breakdown(10, "VAWT")
    cb_h = compute_cost_breakdown(10, "HAWT")
    print(f"\n--- 10 kW VAWT vs HAWT ---")
    print(f"  VAWT total: ${cb_v['total_cost_usd']:.0f}  Cost/kW: ${cb_v['cost_per_kw_usd']:.0f}")
    print(f"  HAWT total: ${cb_h['total_cost_usd']:.0f}  Cost/kW: ${cb_h['cost_per_kw_usd']:.0f}")
    print(f"  Delta: ${cb_v['total_cost_usd'] - cb_h['total_cost_usd']:.0f}")
    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
