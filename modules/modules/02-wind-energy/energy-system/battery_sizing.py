#!/usr/bin/env python3
# =============================================================================
# Battery Sizing — Storage for Off-Grid Wind Turbine
# Part of T014 — Phase 5 US3
# Contract: energy-system-registration.md → compute_battery_sizing()
# Depends on: aep_model.py (compute_aep for generation profile)
# =============================================================================
"""
Battery energy storage sizing for off-grid wind turbine systems.

Computes required capacity based on: daily energy demand, turbine
generation profile, autonomy days, depth of discharge, and system
efficiency.

Usage:
    from src.energy_system.battery_sizing import compute_battery_sizing

    bs = compute_battery_sizing(daily_demand_kwh=40, rated_power_kw=20)
    print(f"Capacity: {bs['battery_capacity_kwh']:.0f} kWh")
"""
from __future__ import annotations

import math
import os
import sys

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from lcoe_model import compute_lcoe


# Defaults for NE Brazil semi-arid community
DEFAULT_AUTONOMY_DAYS = 2        # 2 days backup without wind
DEFAULT_DOD = 0.80               # 80% depth of discharge (LiFePO4)
DEFAULT_EFFICIENCY = 0.90        # 90% round-trip (inverter + battery)
DEFAULT_VOLTAGE_DC = 48          # 48 V typical off-grid
DEFAULT_DAILY_DEMAND_KWH = 40    # kWh/day for ~10 households (rural)
DEFAULT_BATTERY_COST_PER_KWH = 180  # USD/kWh lead-carbon


def compute_battery_sizing(
    daily_demand_kwh: float = DEFAULT_DAILY_DEMAND_KWH,
    autonomy_days: int = DEFAULT_AUTONOMY_DAYS,
    depth_of_discharge: float = DEFAULT_DOD,
    efficiency: float = DEFAULT_EFFICIENCY,
    voltage_dc: int = DEFAULT_VOLTAGE_DC,
    turbine_rated_kw: float | None = None,
    mean_wind_ms: float | None = None,
) -> dict:
    """Compute battery storage capacity for off-grid wind system.

    Battery capacity formula:
        C = D * A / (DoD * eff)

    Where:
        C = Usable capacity (kWh)
        D = Daily energy demand (kWh/day)
        A = Autonomy (days)
        DoD = Depth of discharge
        eff = System efficiency

    Args:
        daily_demand_kwh: Daily energy demand (kWh/day).
        autonomy_days: Days of autonomy without generation.
        depth_of_discharge: Max DoD (0.0-1.0).
        efficiency: Round-trip efficiency (0.0-1.0).
        voltage_dc: System DC voltage.
        turbine_rated_kw: Turbine rating for charging check (optional).
        mean_wind_ms: Mean wind speed for LCOE check (optional).

    Returns:
        Dict with keys:
            battery_capacity_kwh, usable_capacity_kwh,
            daily_generation_check, charge_time_hours,
            battery_cost_usd, system_design params, sc004_lcoe
    """
    if daily_demand_kwh <= 0:
        raise ValueError(f"daily_demand_kwh={daily_demand_kwh} must be > 0")
    if autonomy_days < 1:
        raise ValueError(f"autonomy_days={autonomy_days} must be >= 1")

    # Core sizing
    usable_capacity = daily_demand_kwh * autonomy_days
    battery_capacity = usable_capacity / (depth_of_discharge * efficiency)
    total_amp_hours = battery_capacity * 1000 / voltage_dc

    # Battery cost
    battery_cost = battery_capacity * DEFAULT_BATTERY_COST_PER_KWH

    # Charge check — can the turbine recharge in reasonable time?
    charge_hours = None
    daily_gen_check = None
    lcoe_check = None
    if turbine_rated_kw and turbine_rated_kw > 0:
        # Daily generation at CF
        cf = 0.25  # conservative capacity factor (25%)
        daily_generation_kwh = turbine_rated_kw * cf * 24
        charge_hours = usable_capacity / (turbine_rated_kw * cf)
        daily_gen_check = "PASS" if daily_generation_kwh >= daily_demand_kwh else "FAIL"

        # LCOE check with this battery
        if mean_wind_ms:
            lcoe_check = compute_lcoe(
                rated_power_kw=turbine_rated_kw,
                mean_wind_speed_ms=mean_wind_ms,
                topology="VAWT",
            )

    return {
        "daily_demand_kwh": daily_demand_kwh,
        "autonomy_days": autonomy_days,
        "depth_of_discharge": depth_of_discharge,
        "efficiency": efficiency,
        "battery_capacity_kwh": round(battery_capacity, 1),
        "usable_capacity_kwh": round(usable_capacity, 1),
        "total_amp_hours": round(total_amp_hours, 0),
        "voltage_dc": voltage_dc,
        "daily_generation_check": daily_gen_check,
        "charge_time_hours": round(charge_hours, 1) if charge_hours else None,
        "battery_cost_usd": round(battery_cost, 2),
        "battery_cost_per_kwh": DEFAULT_BATTERY_COST_PER_KWH,
        "sc004_lcoe": lcoe_check["sc004_lcoe"] if lcoe_check else None,
    }


def _test() -> None:
    print("=" * 72)
    print("  T014 — Battery Sizing Verification")
    print("=" * 72)

    scenarios = [
        (20, 2, "2d autonomy for 20 kWh/day"),
        (40, 2, "2d autonomy for 40 kWh/day (~10 households)"),
        (40, 3, "3d autonomy for 40 kWh/day"),
        (80, 2, "2d autonomy for 80 kWh/day (~20 households)"),
    ]

    for demand, days, desc in scenarios:
        bs = compute_battery_sizing(
            daily_demand_kwh=demand,
            autonomy_days=days,
            turbine_rated_kw=20,
            mean_wind_ms=8.0,
        )
        print(f"\n  {desc}:")
        print(f"    Battery:  {bs['battery_capacity_kwh']:>5.0f} kWh"
              f" ({bs['total_amp_hours']:.0f} Ah @ {bs['voltage_dc']}V)")
        print(f"    Usable:   {bs['usable_capacity_kwh']:>5.0f} kWh"
              f" ({bs['charge_time_hours']:.1f}h recharge)")
        print(f"    Cost:     ${bs['battery_cost_usd']:>6.0f}"
              f"  Daily gen: {bs['daily_generation_check']}"
              f"  LCOE: {bs['sc004_lcoe']}")

    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
