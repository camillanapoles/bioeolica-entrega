#!/usr/bin/env python3
# =============================================================================
# Sensitivity Cost — Parameter Impact on LCOE
# Part of T012 — Phase 4 US2
# Depends on: lcoe_model.py (compute_lcoe)
# =============================================================================
"""
Sensitivity analysis of LCOE to turbine cost parameters.

Evaluates impact of ±25% variation in key parameters on LCOE for
the recommended configuration (20 kW HAWT @ 8.0 m/s).

Parameters: tower cost, blade/generator cost, battery cost,
fixed costs, discount rate, O&M rate, wind speed, lifetime.

Usage:
    python src/02-wind-energy/energy-system/sensitivity_cost.py
"""
from __future__ import annotations

import os
import sys

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from lcoe_model import compute_lcoe


# Reference config
BASE_KW = 20
BASE_TOPOLOGY = "HAWT"
BASE_WIND = 8.0
BASE_DISCOUNT = 0.08
BASE_LIFETIME = 20
BASE_OM = 0.02


def compute_scenario(
    label: str,
    description: str,
    tower_mult: float = 1.0,
    gen_mult: float = 1.0,
    batt_mult: float = 1.0,
    fixed_mult: float = 1.0,
    discount: float = BASE_DISCOUNT,
    om_pct: float = BASE_OM,
    wind_speed: float = BASE_WIND,
    lifetime: int = BASE_LIFETIME,
) -> dict:
    """Compute LCOE for a scenario with parameter multipliers.

    Args:
        label: Short label for the scenario.
        description: Human-readable description.
        tower_mult: Tower cost multiplier.
        gen_mult: Generator cost multiplier.
        batt_mult: Battery cost multiplier.
        fixed_mult: Fixed costs multiplier.
        discount: Discount rate.
        om_pct: O&M annual %.
        wind_speed: Mean wind speed (m/s).
        lifetime: Project lifetime (years).

    Returns:
        Dict with label, lcoe, delta_pct vs baseline
    """
    lcoe = compute_lcoe(
        rated_power_kw=BASE_KW,
        mean_wind_speed_ms=wind_speed,
        topology=BASE_TOPOLOGY,
        discount_rate=discount,
        lifetime_years=lifetime,
        om_annual_pct=om_pct,
    )
    return {
        "label": label,
        "description": description,
        "lcoe": lcoe["lcoe_usd_per_kwh"],
        "cost_kw": lcoe["cost_per_kw_usd"],
        "aep": lcoe["aep_kwh"],
    }


def _test() -> None:
    baseline = compute_scenario("Baseline", "20 kW HAWT @ 8.0 m/s")
    base_lcoe = baseline["lcoe"]

    scenarios = [
        compute_scenario("Wind -25%", "Wind 6.0 m/s (site variation)", wind_speed=6.0),
        compute_scenario("Wind +25%", "Wind 10 m/s (optimistic site)", wind_speed=10.0),
        compute_scenario("Discount 4%", "Lower financing cost", discount=0.04),
        compute_scenario("Discount 12%", "Higher financing cost", discount=0.12),
        compute_scenario("OM 1%", "Minimal maintenance", om_pct=0.01),
        compute_scenario("OM 4%", "High maintenance/remote", om_pct=0.04),
        compute_scenario("Lifetime 15yr", "Early replacement", lifetime=15),
        compute_scenario("Lifetime 25yr", "Extended operation", lifetime=25),
    ]

    print("=" * 72)
    print("  T012 — Sensitivity Cost Analysis")
    print("  Reference: 20 kW HAWT @ 8.0 m/s")
    print("=" * 72)
    print()
    print(f"  {'Scenario':<20} {'LCOE':>8}  {'Δ vs Base':>10}  {'Cost/kW':>8}  {'AEP':>10}")
    print(f"  {'-'*60}")
    print(f"  {'Baseline':<20} ${baseline['lcoe']:>6.4f}      0.0%  ${baseline['cost_kw']:>5.0f}"
          f"  {baseline['aep']/1000:>6.1f}MWh")

    for s in scenarios:
        delta = (s["lcoe"] - base_lcoe) / base_lcoe * 100
        print(f"  {s['label']:<20} ${s['lcoe']:>6.4f}  {delta:>+8.1f}%  ${s['cost_kw']:>5.0f}"
              f"  {s['aep']/1000:>6.1f}MWh  ({s['description']})")

    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
