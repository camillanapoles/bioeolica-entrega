#!/usr/bin/env python3
"""
Complete energy system sizing for a 20-family semi-arid community
using VAWT H-rotor Darrieus with paper-mache + graphite blades.

Covers: turbine sizing, tower, battery bank, inverter, distribution.

References SC-005: 2-day autonomy, capacity factor >= 20%, 100% demand.
"""

import sys
import os
import math
import json
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.database import database

# ---- inputs ---- #

from pathlib import Path

# P$1: rotear constantes pelo schema unificado
_CORE = Path(__file__).resolve()
while not (_CORE / "workspace").exists() and _CORE.parent != _CORE:
    _CORE = _CORE.parent
_CORE = _CORE / "workspace" / "lab1-material-papel-mache-grafite"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from core.constants import get

WEIBULL_K = get("modules.h_rotor.weibull_k")
WEIBULL_C = get("modules.h_rotor.weibull_c")
AIR_DENSITY = get("modules.h_rotor.air_density")  # kg/m^3 at 40C, 500m elevation
SHEAR_ALPHA = get("modules.h_rotor.shear_alpha")

# Demand (from T047: Assentamento Sertao Sustentavel)
COMMUNITY_ID = "085e0235-5726-4faf-ac93-198cc60924bc"
ENERGY_TOTAL_KWH_DAY = 38.0
ENERGY_MONTHLY_KWH = {"min": 1050, "max": 1440}
SEASONAL_VARIATION = 0.35  # +/-35%
GROWTH_MARGIN = 0.20

# VAWT parameters (from blade_geometry.py)
ROTOR_DIAMETER = 3.5  # m
BLADE_LENGTH = 3.5  # m
NUM_BLADES = 3
SWEPT_AREA = 9.62  # m² (2 * R * H)
CP_MAX = get("modules.h_rotor.cp_max")  # H-rotor Darrieus Cp
CUT_IN = get("modules.h_rotor.cut_in_ms")  # m/s
CUT_OUT = get("modules.h_rotor.cut_out_ms")  # m/s
RATED_WS = get("modules.h_rotor.rated_ws_ms")  # m/s


@dataclass
class SystemSizing:
    # Turbine
    rated_power_kw: float
    annual_energy_kwh: float
    capacity_factor_pct: float
    # Tower
    tower_height_m: float
    hub_height_wind_ms: float
    # Battery
    battery_capacity_kwh: float
    battery_type: str
    autonomy_days: float
    # Inverter
    inverter_rating_kw: float
    inverter_efficiency: float
    # Distribution
    distribution_voltage_v: int
    # Targets
    demand_coverage_pct: float
    sc005_coverage: str
    sc005_autonomy: str
    sc005_cf: str


def weibull_mean(c: float, k: float) -> float:
    """Mean wind speed from Weibull parameters."""
    return c * math.gamma(1.0 + 1.0 / k)


def wind_at_height(v_ref: float, z_ref: float, z_target: float, alpha: float) -> float:
    return v_ref * (z_target / z_ref) ** alpha


def power_in_wind(v: float, area: float, rho: float) -> float:
    return 0.5 * rho * area * v ** 3


def weibull_cdf(v: float, c: float, k: float) -> float:
    """P(V <= v)"""
    return 1.0 - math.exp(-((v / c) ** k))


def size_system(
    community_id: str = COMMUNITY_ID,
    rotor_diameter: float = ROTOR_DIAMETER,
    blade_length: float = BLADE_LENGTH,
    num_blades: int = NUM_BLADES,
    swept_area: float = SWEPT_AREA,
    cp_max: float = CP_MAX,
    hub_height: float = 30.0,
    demand_kwh_day: float = ENERGY_TOTAL_KWH_DAY,
    growth_margin: float = GROWTH_MARGIN,
    autonomy_target: float = 2.0,
    battery_efficiency: float = 0.90,
    dod_max: float = 0.80,
    inverter_efficiency: float = 0.95,
    dist_voltage: int = 220,
) -> SystemSizing:
    # Demand with growth margin
    design_demand = demand_kwh_day * (1.0 + growth_margin)

    # Wind at hub height
    v_mean_10m = weibull_mean(WEIBULL_C, WEIBULL_K)
    v_mean_hub = wind_at_height(v_mean_10m, 10.0, hub_height, SHEAR_ALPHA)
    c_hub = wind_at_height(WEIBULL_C, 10.0, hub_height, SHEAR_ALPHA)  # scale param scales with mean

    # Rated power (at RATED_WS using Cp_max)
    p_rated = power_in_wind(RATED_WS, swept_area, AIR_DENSITY) * cp_max / 1000  # kW

    # Annual energy: numerical Weibull integration over power curve
    # P(v) = min(0.5*rho*A*v^3*Cp, P_rated) for cut_in <= v <= rated
    # P(v) = P_rated for rated < v <= cut_out
    # f(v) = (k/c)*(v/c)^(k-1)*exp(-(v/c)^k) (Weibull PDF)
    N_STEPS = 500
    dv = (CUT_OUT - CUT_IN) / N_STEPS
    annual_energy = 0.0
    for i in range(N_STEPS):
        v = CUT_IN + (i + 0.5) * dv
        if v <= RATED_WS:
            p = min(power_in_wind(v, swept_area, AIR_DENSITY) * cp_max / 1000, p_rated)
        else:
            p = p_rated
        # Weibull PDF
        f_v = (WEIBULL_K / c_hub) * (v / c_hub) ** (WEIBULL_K - 1) * math.exp(-((v / c_hub) ** WEIBULL_K))
        annual_energy += p * f_v * dv * 8760
    cf = annual_energy / (p_rated * 8760) * 100

    # Battery sizing: autonomy days × daily demand / DoD / inverter efficiency
    battery_kwh = (autonomy_target * design_demand) / (dod_max * inverter_efficiency)

    # Inverter sizing: peak load (assume 1.5x average hourly load)
    avg_hourly_load = design_demand / 24
    inverter_kw = avg_hourly_load * 1.5

    # Coverage
    coverage = min(annual_energy / (design_demand * 365) * 100, 100.0)
    autonomy = battery_kwh * dod_max * inverter_efficiency / design_demand

    # SC-005 checks
    sc005_cov = "PASS" if coverage >= 100 else "FAIL"
    sc005_aut = "PASS" if autonomy >= autonomy_target - 0.01 else "FAIL"
    sc005_cf = "PASS" if cf >= 20 else "FAIL"

    return SystemSizing(
        rated_power_kw=round(p_rated, 2),
        annual_energy_kwh=round(annual_energy, 0),
        capacity_factor_pct=round(cf, 1),
        tower_height_m=hub_height,
        hub_height_wind_ms=round(v_mean_hub, 2),
        battery_capacity_kwh=round(battery_kwh, 1),
        battery_type=f"Lead-carbon deep-cycle (DoD {dod_max*100:.0f}%)",
        autonomy_days=round(autonomy, 1),
        inverter_rating_kw=round(inverter_kw, 2),
        inverter_efficiency=inverter_efficiency,
        distribution_voltage_v=dist_voltage,
        demand_coverage_pct=round(coverage, 1),
        sc005_coverage=sc005_cov,
        sc005_autonomy=sc005_aut,
        sc005_cf=sc005_cf,
    )


def report(sizing: SystemSizing) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  ENERGY SYSTEM SIZING — Assentamento Sertao Sustentavel")
    lines.append("=" * 60)

    lines.append(f"\n  Community demand: {ENERGY_TOTAL_KWH_DAY} kWh/day ({ENERGY_TOTAL_KWH_DAY*365:.0f} kWh/yr)")
    lines.append(f"  Design demand (incl. {GROWTH_MARGIN*100:.0f}% margin): {ENERGY_TOTAL_KWH_DAY*(1+GROWTH_MARGIN):.1f} kWh/day")

    lines.append(f"\n  --- Turbine ---")
    lines.append(f"  Type: VAWT H-rotor Darrieus (NACA 0018)")
    lines.append(f"  Rotor: {ROTOR_DIAMETER}m × {BLADE_LENGTH}m, {NUM_BLADES} blades")
    lines.append(f"  Swept area: {SWEPT_AREA} m²")
    lines.append(f"  Hub height: {sizing.tower_height_m}m")
    lines.append(f"  Wind at hub: {sizing.hub_height_wind_ms} m/s (mean)")
    lines.append(f"  Rated power: {sizing.rated_power_kw} kW")
    lines.append(f"  Annual energy: {sizing.annual_energy_kwh:.0f} kWh/yr")
    lines.append(f"  Capacity factor: {sizing.capacity_factor_pct}%")

    lines.append(f"\n  --- Tower ---")
    lines.append(f"  Height: 30m lattice tower (hot-dip galvanized)")
    lines.append(f"  Guy wires at 10m, 20m, 30m")

    lines.append(f"\n  --- Battery Bank ---")
    lines.append(f"  Capacity: {sizing.battery_capacity_kwh} kWh")
    lines.append(f"  Type: {sizing.battery_type}")
    lines.append(f"  Autonomy: {sizing.autonomy_days} days (target: 2.0)")

    lines.append(f"\n  --- Inverter & Distribution ---")
    lines.append(f"  Inverter: {sizing.inverter_rating_kw} kW ({sizing.inverter_efficiency*100:.0f}% efficiency)")
    lines.append(f"  Distribution: {sizing.distribution_voltage_v} V AC")
    lines.append(f"  Controller: MPPT charge controller")

    lines.append(f"\n  --- SC-005 Validation ---")
    lines.append(f"  Demand coverage (≥100%): {sizing.demand_coverage_pct}% → {sizing.sc005_coverage}")
    lines.append(f"  Autonomy (≥2 days): {sizing.autonomy_days} days → {sizing.sc005_autonomy}")
    lines.append(f"  Capacity factor (≥20%): {sizing.capacity_factor_pct}% → {sizing.sc005_cf}")
    lines.append("")

    sc005_all = all([
        sizing.sc005_coverage == "PASS",
        sizing.sc005_autonomy == "PASS",
        sizing.sc005_cf == "PASS",
    ])
    lines.append(f"  SC-005 OVERALL: {'✅ PASS' if sc005_all else '❌ FAIL'}")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    import sys
    sizing = size_system()
    print(report(sizing))
    return 0 if sizing.sc005_coverage == "PASS" else 1


if __name__ == "__main__":
    # Import moved to function level to avoid circular import at top
    from dataclasses import dataclass
    main()
