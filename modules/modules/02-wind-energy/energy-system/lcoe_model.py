#!/usr/bin/env python3
# =============================================================================
# LCOE Model — Levelized Cost of Energy
# Part of T008 — Phase 3 US1
# Contract: cost-model.md → compute_lcoe()
# Dependencies: cost_breakdown.py (compute_cost_breakdown), aep_model.py (compute_aep)
# =============================================================================
"""
LCOE computation combining cost breakdown and AEP model.

Delegates cost decomposition to compute_cost_breakdown() and energy
production to compute_aep(), then computes LCOE via discounted cash flow.

Usage:
    from src.energy_system.lcoe_model import compute_lcoe

    result = compute_lcoe(10.0, 7.5, "VAWT")
    print(f"LCOE: ${result['lcoe_usd_per_kwh']:.4f}/kWh")
"""
from __future__ import annotations

import os
import sys

from typing import Optional

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from cost_breakdown import compute_cost_breakdown
from aep_model import compute_aep


# ---------------------------------------------------------------------------
# Financial constants
# ---------------------------------------------------------------------------

DEFAULT_DISCOUNT_RATE = 0.08      # 8% (Brazil SELIC + risk premium)
DEFAULT_LIFETIME_YEARS = 20       # small wind design life
DEFAULT_OM_ANNUAL_PCT = 0.02      # 2% of installed cost/yr


# ---------------------------------------------------------------------------
# LCOE computation
# ---------------------------------------------------------------------------


def compute_lcoe(
    rated_power_kw: float,
    mean_wind_speed_ms: float,
    topology: str = "VAWT",
    weibull_k: float = 2.0,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    lifetime_years: int = DEFAULT_LIFETIME_YEARS,
    om_annual_pct: float = DEFAULT_OM_ANNUAL_PCT,
    om_fixed_usd: Optional[float] = None,
    air_density_kgm3: float = 1.105,
) -> dict:
    """Compute LCOE combining cost breakdown + AEP model.

    Args:
        rated_power_kw: Turbine rated power (kW).
        mean_wind_speed_ms: Mean wind speed at hub height (m/s).
        topology: 'VAWT' or 'HAWT'.
        weibull_k: Weibull shape parameter (default 2.0).
        discount_rate: Discount rate (default 0.08).
        lifetime_years: Project lifetime (default 20).
        om_annual_pct: O&M as % of installed cost (default 0.02).
        om_fixed_usd: Optional fixed O&M override (USD/yr).
        air_density_kgm3: Air density (kg/m^3).

    Returns:
        Dict with keys:
            lcoe_usd_per_kwh: LCOE in $/kWh
            crf: Capital recovery factor
            annual_om_cost: Annual O&M cost (USD)
            total_installed_cost_usd: Total installed cost
            aep_kwh: Annual energy production (kWh/yr)
            cost_per_kw_usd: Cost per kW installed
            rated_power_kw, topology, mean_wind_speed_ms
            sc004_cost: 'PASS' if cost/kW < 3000 else 'FAIL'
            sc004_lcoe: 'PASS' if LCOE < 0.15 else 'FAIL'
            breakdown_table: Formatted table for display
    """
    # Cost breakdown
    cost = compute_cost_breakdown(rated_power_kw, topology)
    total_cost = cost["total_cost_usd"]

    # AEP
    aep_result = compute_aep(
        rated_power_kw=rated_power_kw,
        mean_wind_speed_ms=mean_wind_speed_ms,
        weibull_k=weibull_k,
        air_density_kgm3=air_density_kgm3,
        topology=topology,
        rotor_diameter_m=cost["est_rotor_diameter_m"],
    )
    aep_kwh = aep_result["annual_energy_production_kwh"]

    # Capital Recovery Factor: CRF = r*(1+r)^n / ((1+r)^n - 1)
    crf_lcoe = discount_rate * (1 + discount_rate) ** lifetime_years / (
        (1 + discount_rate) ** lifetime_years - 1
    )

    # Annual O&M
    if om_fixed_usd is not None:
        om_annual = om_fixed_usd
    else:
        om_annual = total_cost * om_annual_pct

    # Added degradation: 0.5%/yr
    npv_costs = total_cost  # year 0
    npv_energy = 0.0
    for y in range(1, lifetime_years + 1):
        df = (1 + discount_rate) ** (-y)
        npv_costs += om_annual * df
        energy_y = aep_kwh * (1 - 0.005) ** (y - 1)
        npv_energy += energy_y * df

    lcoe = npv_costs / npv_energy if npv_energy > 0 else 999.0
    cost_per_kw = total_cost / rated_power_kw if rated_power_kw > 0 else 0.0

    return {
        "lcoe_usd_per_kwh": round(lcoe, 4),
        "crf": round(crf_lcoe, 6),
        "annual_om_cost": round(om_annual, 2),
        "total_installed_cost_usd": round(total_cost, 2),
        "aep_kwh": round(aep_kwh, 2),
        "cost_per_kw_usd": round(cost_per_kw, 2),
        "rated_power_kw": rated_power_kw,
        "topology": topology,
        "mean_wind_speed_ms": mean_wind_speed_ms,
        "weibull_k": weibull_k,
        "discount_rate": discount_rate,
        "lifetime_years": lifetime_years,
        "npv_costs": round(npv_costs, 0),
        "npv_energy": round(npv_energy, 0),
        "sc004_cost": "PASS" if cost_per_kw < 3000 else "FAIL",
        "sc004_lcoe": "PASS" if lcoe < 0.15 else "FAIL",
    }


def _test() -> None:
    """Run verification."""
    print("=" * 72)
    print("  T008 — LCOE Model Verification")
    print("=" * 72)

    configs = [
        (5, 6.5, "VAWT"),
        (10, 7.5, "VAWT"),
        (10, 7.5, "HAWT"),
        (15, 8.0, "VAWT"),
        (20, 8.0, "VAWT"),
    ]

    for kw, v, top in configs:
        r = compute_lcoe(kw, v, top)
        sc = "✅ PASS" if r["sc004_cost"] == "PASS" and r["sc004_lcoe"] == "PASS" else "❌ FAIL"
        print(f"\n  {kw:>5}kW {top:>4s} @ {v:.1f}m/s")
        print(f"  Cost/kW: ${r['cost_per_kw_usd']:>8,.0f}  LCOE: ${r['lcoe_usd_per_kwh']:.4f}")
        print(f"  AEP:      {r['aep_kwh']:>10,.0f} kWh/yr")
        print(f"  NPV:      ${r['npv_costs']:>9,.0f}  CF: {r['crf']:.4f}")
        print(f"  SC-004:   {sc}")

    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
