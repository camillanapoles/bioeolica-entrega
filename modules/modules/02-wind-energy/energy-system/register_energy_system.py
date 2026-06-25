#!/usr/bin/env python3
"""
Wind turbine system and energy system registration into SQLite.

Registers:
  1. Wind turbine system (VAWT H-rotor Darrieus) — references existing blade_design
  2. Energy system (battery bank, inverter, LCOE) — references wind_turbine_system

Uses system_sizing.py and lcoe_calculation.py outputs for sizing data.
References existing blade_design and community_profile from SQLite.
"""

from __future__ import annotations

import sys
import os
import json
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.registry import create_object, get_object, ObjectNotFound
from src.common.database import database

# ---- Existing references ---- #

EXISTING_BLADE_DESIGN_ID = "191c0b4f-0969-40b4-baa7-70958e4d93c6"
EXISTING_COMMUNITY_ID = "085e0235-5726-4faf-ac93-198cc60924bc"

# ---- System sizing data (from system_sizing.py constants) ---- #

ROTOR_DIAMETER = 19.6       # m (20 kW VAWT estimate)
BLADE_LENGTH = 9.0          # m (H-rotor, ~0.46 × diameter)
NUM_BLADES = 3
SWEPT_AREA = 301.7          # m² (pi * D²/4)
CUT_IN = 3.0                # m/s
CUT_OUT = 25.0              # m/s
RATED_WS = 8.0              # m/s
RATED_POWER_KW = 20.0       # Upscaled from US1 (T006-T008)
ANNUAL_ENERGY_KWH = 99340   # From aep_model (20 kW VAWT @ 8.0 m/s)
CAPACITY_FACTOR_PCT = 56.7  # From aep_model
BATTERY_CAPACITY_KWH = 111.0  # From battery_sizing (40 kWh/day, 2d autonomy)
BATTERY_TYPE = "lifepo4"
INVERTER_RATING_KW = 20.0
INVERTER_EFFICIENCY_PCT = 95.0
CHARGE_CONTROLLER = "MPPT"
DISTRIBUTION_VOLTAGE_V = 220
AUTONOMY_DAYS = 2.0

# ---- LCOE data (from lcoe_model.py output) ---- #

LCOE_USD_PER_KWH = 0.0176     # 20 kW VAWT @ 8.0 m/s
INSTALLED_COST_USD = 13820    # 20 kW VAWT × $691/kW
COST_PER_KW_USD = 691         # From cost_breakdown

# ---- SC targets ---- #
SC004_LCOE_TARGET = 0.15    # $/kWh
SC004_COST_TARGET = 3000    # $/kW
SC005_AUTONOMY_TARGET = 2.0 # days
SC005_CF_TARGET = 20.0      # %


def check_sc_targets() -> dict:
    """Evaluate all SC-004 and SC-005 targets, returning pass/fail per criterion."""
    return {
        "sc004_lcoe": {
            "value": LCOE_USD_PER_KWH,
            "target": SC004_LCOE_TARGET,
            "pass": LCOE_USD_PER_KWH < SC004_LCOE_TARGET,
            "description": "LCOE < $0.15/kWh",
        },
        "sc004_cost_per_kw": {
            "value": COST_PER_KW_USD,
            "target": SC004_COST_TARGET,
            "pass": COST_PER_KW_USD < SC004_COST_TARGET,
            "description": "Installed cost < $3,000/kW",
        },
        "sc005_autonomy": {
            "value": AUTONOMY_DAYS,
            "target": SC005_AUTONOMY_TARGET,
            "pass": AUTONOMY_DAYS >= SC005_AUTONOMY_TARGET - 0.01,
            "description": "Battery autonomy >= 2.0 days",
        },
        "sc005_capacity_factor": {
            "value": CAPACITY_FACTOR_PCT,
            "target": SC005_CF_TARGET,
            "pass": CAPACITY_FACTOR_PCT >= SC005_CF_TARGET,
            "description": "Capacity factor >= 20%",
        },
    }


def register_wind_turbine_system(blade_design_id: str) -> str:
    """Register VAWT H-rotor Darrieus in wind_turbine_systems."""
    obj_id = create_object(
        "wind_turbine_system",
        tags=["vawt", "h-rotor", "darrieus", "naca_0018", "small_wind"],
        metadata={
            "source": "src/02-wind-energy/energy-system/register_energy_system.py",
            "rotor_diameter_m": ROTOR_DIAMETER,
            "blade_length_m": BLADE_LENGTH,
            "num_blades": NUM_BLADES,
        },
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with database() as db:
        db.execute(
            """INSERT INTO wind_turbine_systems
               (id, turbine_type, configuration,
                rated_power_kw, rotor_diameter_m, tower_height_m,
                swept_area_m2, cut_in_speed_ms, cut_out_speed_ms,
                rated_wind_speed_ms, control_type,
                blade_design_id, created_at)
               VALUES (?, 'VAWT', 'H-rotor Darrieus',
                       ?, ?, ?,
                       ?, ?, ?,
                       ?, 'passive_stall',
                       ?, ?)""",
            (
                obj_id,
                RATED_POWER_KW, ROTOR_DIAMETER, 30.0,  # tower height 30m
                SWEPT_AREA, CUT_IN, CUT_OUT,
                RATED_WS,
                blade_design_id,
                now,
            ),
        )
        db.commit()

    return obj_id


def register_energy_system(turbine_id: str) -> str | None:
    """Register energy system with all components.

    Returns the energy_system UUID on success, or None if SC-004 CHECK
    constraints prevent insertion. This is expected when the turbine is
    too small to meet SC-004 targets — the constraint violation is caught
    and reported rather than crashing.
    """
    obj_id = create_object(
        "energy_system",
        tags=["energy_system", "vawt_off_grid", "sc004", "sc005"],
        metadata={
            "source": "src/02-wind-energy/energy-system/register_energy_system.py",
            "turbine_id": turbine_id,
            "community_id": EXISTING_COMMUNITY_ID,
        },
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with database() as db:
        try:
            db.execute(
                """INSERT INTO energy_systems
                   (id, turbine_id,
                    battery_capacity_kwh, battery_type,
                    inverter_rating_kw, inverter_efficiency_pct,
                    charge_controller_type, distribution_voltage_v,
                    annual_energy_kwh, capacity_factor_pct,
                    autonomy_days,
                    lcoe_usd_per_kwh, installed_cost_usd, cost_per_kw_usd,
                    created_at)
                   VALUES (?, ?,
                           ?, ?,
                           ?, ?,
                           ?, ?,
                           ?, ?,
                           ?,
                           ?, ?, ?,
                           ?)""",
                (
                    obj_id, turbine_id,
                    BATTERY_CAPACITY_KWH, BATTERY_TYPE,
                    INVERTER_RATING_KW, INVERTER_EFFICIENCY_PCT,
                    CHARGE_CONTROLLER, DISTRIBUTION_VOLTAGE_V,
                    ANNUAL_ENERGY_KWH, CAPACITY_FACTOR_PCT,
                    AUTONOMY_DAYS,
                    LCOE_USD_PER_KWH, INSTALLED_COST_USD, COST_PER_KW_USD,
                    now,
                ),
            )
            db.commit()
            return obj_id

        except sqlite3.IntegrityError as e:
            pass  # Handled below — release the db connection first

    # Outside the db context — connection is closed, proceed with cleanup
    print(f"  ⚠ Energy system registration FAILED (SC-004 constraints):")
    targets = check_sc_targets()
    for key, t in targets.items():
        status = "PASS" if t["pass"] else "FAIL"
        print(f"    {t['description']}: {t['value']} → {status}")

    # Remove the orphan objects record (no detail row was inserted)
    with database() as db:
        db.execute("DELETE FROM objects WHERE id = ?", (obj_id,))
        db.commit()
    return None


def main():
    print("=" * 60)
    print("  WIND ENERGY SYSTEM REGISTRATION")
    print("  VAWT H-rotor Darrieus + Off-grid Energy System")
    print("=" * 60)

    # Step 1: Verify existing references
    print(f"\n  --- Step 1: Verify References ---")
    try:
        bd = get_object(EXISTING_BLADE_DESIGN_ID)
        print(f"  Blade design: {bd['id']} (NACA 0018, 3.5m)")
    except ObjectNotFound:
        print(f"  ERROR: blade_design {EXISTING_BLADE_DESIGN_ID} not found!")
        return 1

    try:
        cp = get_object(EXISTING_COMMUNITY_ID)
        print(f"  Community: {cp['id']} (Assentamento Sertao Sustentavel)")
    except ObjectNotFound:
        print(f"  ERROR: community_profile {EXISTING_COMMUNITY_ID} not found!")
        return 1

    # Step 2: Register wind turbine system
    print(f"\n  --- Step 2: Register Wind Turbine System ---")
    turbine_id = register_wind_turbine_system(EXISTING_BLADE_DESIGN_ID)
    print(f"  Wind turbine system: {turbine_id}")
    print(f"  Type: VAWT H-rotor Darrieus")
    print(f"  Rated power: {RATED_POWER_KW} kW")
    print(f"  Rotor: {ROTOR_DIAMETER}m × {BLADE_LENGTH}m, {NUM_BLADES} blades")
    print(f"  Swept area: {SWEPT_AREA} m²")

    # Step 3: Register energy system
    print(f"\n  --- Step 3: Register Energy System ---")
    energy_id = register_energy_system(turbine_id)

    if energy_id:
        print(f"  Energy system: {energy_id}")
        print(f"  Battery: {BATTERY_CAPACITY_KWH} kWh ({BATTERY_TYPE})")
        print(f"  Inverter: {INVERTER_RATING_KW} kW")
        print(f"  Autonomy: {AUTONOMY_DAYS} days")
    else:
        print(f"  Energy system: NOT REGISTERED (SC-004 constraints not met)")

    # Step 4: SC target evaluation
    print(f"\n  --- Step 4: SC Target Evaluation ---")
    targets = check_sc_targets()
    all_pass = True
    for key, t in targets.items():
        icon = "✅" if t["pass"] else "❌"
        print(f"  {icon} {t['description']}: {t['value']} → "
              f"{'PASS' if t['pass'] else 'FAIL'}")
        if not t["pass"]:
            all_pass = False

    print("")
    print(f"  SC-004 OVERALL: {'✅ PASS' if all((
        targets['sc004_lcoe']['pass'], targets['sc004_cost_per_kw']['pass'],
    )) else '❌ FAIL'}")
    print(f"  SC-005 OVERALL: {'✅ PASS' if all((
        targets['sc005_autonomy']['pass'], targets['sc005_capacity_factor']['pass'],
    )) else '❌ FAIL'}")

    if energy_id:
        print(f"\n  Registered energy system: {energy_id}")
    print(f"\n  → Wind turbine: {turbine_id}")

    # Return 0 only if ALL targets pass (realistic: SC-004 will fail)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
