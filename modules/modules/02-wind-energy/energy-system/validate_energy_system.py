#!/usr/bin/env python3
"""
Full system validation for SC-004 and SC-005 targets.

Runs validation queries against SQLite views and computes SC targets
from system sizing / LCOE data. Provides comprehensive pass/fail report
for the wind energy system.

Usage:
    python src/02-wind-energy/energy-system/validate_energy_system.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.database import database


# ---- System sizing data (from system_sizing.py constants) ---- #

RATED_POWER_KW = 0.82
ANNUAL_ENERGY_KWH = 4098
CAPACITY_FACTOR_PCT = 57.3
BATTERY_CAPACITY_KWH = 120.0
AUTONOMY_DAYS = 2.0
INVERTER_RATING_KW = 2.85
INVERTER_EFFICIENCY_PCT = 95.0
DISTRIBUTION_VOLTAGE_V = 220
ENERGY_TOTAL_KWH_DAY = 38.0
DESIGN_DEMAND_KWH_DAY = 45.6  # 38 * 1.2 growth margin
DEMAND_COVERAGE_PCT = 24.6

LCOE_USD_PER_KWH = 1.4173
INSTALLED_COST_USD = 39527
COST_PER_KW_USD = 48204


def check_sc_targets():
    """Return SC-004 and SC-005 target evaluation dict."""
    return {
        "SC-004": {
            "description": "LCOE < $0.15/kWh, cost < $3,000/kW",
            "checks": {
                "lcoe": {
                    "value": LCOE_USD_PER_KWH,
                    "target": 0.15,
                    "unit": "$/kWh",
                    "operator": "<",
                    "pass": LCOE_USD_PER_KWH < 0.15,
                },
                "cost_per_kw": {
                    "value": COST_PER_KW_USD,
                    "target": 3000,
                    "unit": "$/kW",
                    "operator": "<",
                    "pass": COST_PER_KW_USD < 3000,
                },
            },
            "overall": LCOE_USD_PER_KWH < 0.15 and COST_PER_KW_USD < 3000,
        },
        "SC-005": {
            "description": "100% demand met, 2-day autonomy, CF >= 20%",
            "checks": {
                "demand_coverage": {
                    "value": DEMAND_COVERAGE_PCT,
                    "target": 100.0,
                    "unit": "%",
                    "operator": ">=",
                    "pass": DEMAND_COVERAGE_PCT >= 100.0,
                },
                "autonomy": {
                    "value": AUTONOMY_DAYS,
                    "target": 2.0,
                    "unit": "days",
                    "operator": ">=",
                    "pass": AUTONOMY_DAYS >= 2.0 - 0.01,
                },
                "capacity_factor": {
                    "value": CAPACITY_FACTOR_PCT,
                    "target": 20.0,
                    "unit": "%",
                    "operator": ">=",
                    "pass": CAPACITY_FACTOR_PCT >= 20.0,
                },
            },
            "overall": (
                DEMAND_COVERAGE_PCT >= 100.0
                and AUTONOMY_DAYS >= 2.0 - 0.01
                and CAPACITY_FACTOR_PCT >= 20.0
            ),
        },
    }


def query_validation_views():
    """Query SQLite validation views for SC targets."""
    results = {}

    with database() as db:
        # Wind turbine systems summary
        rows = db.execute(
            """SELECT COUNT(*), COALESCE(MAX(created_at), 'none')
               FROM wind_turbine_systems"""
        ).fetchone()
        results["turbine_count"] = rows[0]
        results["latest_turbine"] = rows[1]

        # Energy systems (will be empty if SC-004 constraints blocked)
        rows = db.execute(
            """SELECT COUNT(*) FROM energy_systems"""
        ).fetchone()
        results["energy_system_count"] = rows[0]

        # Latest energy system if any
        if results["energy_system_count"] > 0:
            rows = db.execute(
                """SELECT id, lcoe_usd_per_kwh, cost_per_kw_usd,
                          autonomy_days, capacity_factor_pct
                   FROM energy_systems
                   ORDER BY created_at DESC LIMIT 1"""
            ).fetchone()
            results["energy_system"] = dict(rows)

        # v_energy_sizing
        try:
            rows = db.execute("SELECT * FROM v_energy_sizing").fetchall()
            results["v_energy_sizing"] = [dict(r) for r in rows]
        except Exception as e:
            results["v_energy_sizing"] = {"error": str(e)}

        # v_economic_targets
        try:
            rows = db.execute("SELECT * FROM v_economic_targets").fetchall()
            results["v_economic_targets"] = [dict(r) for r in rows]
        except Exception as e:
            results["v_economic_targets"] = {"error": str(e)}

        # v_success_criteria_status (only SC-004 and SC-005 rows)
        try:
            rows = db.execute(
                """SELECT criterion, description, status
                   FROM v_success_criteria_status
                   WHERE criterion IN ('SC-004', 'SC-005', 'SC-007', 'SC-008')"""
            ).fetchall()
            results["v_success_criteria"] = [dict(r) for r in rows]
        except Exception as e:
            results["v_success_criteria"] = {"error": str(e)}

    return results


def format_target_report(sc_targets, db_results):
    """Format comprehensive validation report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  ENERGY SYSTEM VALIDATION REPORT")
    lines.append("  VAWT H-rotor Darrieus — Assentamento Sertao Sustentavel")
    lines.append("=" * 64)

    # Registration status
    lines.append(f"\n  --- Registration Status ---")
    lines.append(f"  Wind turbine systems registered: {db_results['turbine_count']}")
    lines.append(f"  Latest turbine: {db_results['latest_turbine']}")
    lines.append(f"  Energy systems registered: {db_results['energy_system_count']}")
    if db_results["energy_system_count"] == 0:
        lines.append(f"  (Energy system rejected by SC-004 CHECK constraints)")
    lines.append(f"")

    # SC-004 Economic targets
    lines.append(f"  ═══ SC-004: Economic Targets ═══")
    lines.append(f"  {sc_targets['SC-004']['description']}")
    lines.append(f"  ─" * 20)
    for key, check in sc_targets["SC-004"]["checks"].items():
        icon = "✅" if check["pass"] else "❌"
        op = check["operator"]
        lines.append(
            f"  {icon} {key}: {check['value']} {op} {check['target']} {check['unit']} → "
            f"{'PASS' if check['pass'] else 'FAIL'}"
        )
    # Analysis of WHY SC-004 fails
    lines.append(f"")
    lines.append(f"  Root cause: 0.82 kW turbine with $24k battery bank")
    lines.append(f"  Fixed costs ($5.5k tower+transport+controller) dominate")
    lines.append(f"  per-kW economics at this scale")
    overall = "✅ PASS" if sc_targets["SC-004"]["overall"] else "❌ FAIL"
    lines.append(f"\n  SC-004 OVERALL: {overall}")

    # SC-005 System sizing targets
    lines.append(f"\n  ═══ SC-005: System Sizing ═══")
    lines.append(f"  {sc_targets['SC-005']['description']}")
    lines.append(f"  ─" * 20)
    for key, check in sc_targets["SC-005"]["checks"].items():
        icon = "✅" if check["pass"] else "❌"
        op = check["operator"]
        lines.append(
            f"  {icon} {key}: {check['value']} {op} {check['target']} {check['unit']} → "
            f"{'PASS' if check['pass'] else 'FAIL'}"
        )
    lines.append(f"")
    lines.append(f"  Note: demand coverage at 24.6% — the 0.82 kW VAWT")
    lines.append(f"  captures only a fraction of the 38 kWh/day demand.")
    lines.append(f"  A larger turbine (10-15 kW) is needed for full coverage.")
    overall = "✅ PASS" if sc_targets["SC-005"]["overall"] else "❌ FAIL"
    lines.append(f"\n  SC-005 OVERALL: {overall}")

    # System summary
    lines.append(f"\n  --- System Parameters ---")
    lines.append(f"  Turbine: VAWT H-rotor Darrieus, 3.5m × 3.5m, 3 blades")
    lines.append(f"  Rated power: {RATED_POWER_KW} kW")
    lines.append(f"  Annual energy: {ANNUAL_ENERGY_KWH:,} kWh/yr")
    lines.append(f"  Capacity factor: {CAPACITY_FACTOR_PCT}%")
    lines.append(f"  Battery: {BATTERY_CAPACITY_KWH} kWh (lead-carbon)")
    lines.append(f"  Autonomy: {AUTONOMY_DAYS} days")
    lines.append(f"  Inverter: {INVERTER_RATING_KW} kW")
    lines.append(f"  Distribution: {DISTRIBUTION_VOLTAGE_V} V")
    lines.append(f"  Community demand: {ENERGY_TOTAL_KWH_DAY} kWh/day ({ENERGY_TOTAL_KWH_DAY*365:.0f} kWh/yr)")
    lines.append(f"  Demand coverage: {DEMAND_COVERAGE_PCT}%")
    lines.append(f"  LCOE: ${LCOE_USD_PER_KWH:.4f}/kWh")
    lines.append(f"  Cost: ${COST_PER_KW_USD:,}/kW")

    # Database view status
    lines.append(f"\n  --- Database Validation Views ---")
    if db_results["v_energy_sizing"]:
        for row in db_results["v_energy_sizing"]:
            lines.append(
                f"  v_energy_sizing: autonomy={row.get('autonomy_check','?')}, "
                f"CF={row.get('capacity_factor_check','?')}, "
                f"SC-005={row.get('sc005_status','?')}"
            )
    else:
        lines.append(f"  v_energy_sizing: (no data — energy_systems table empty)")

    if db_results["v_economic_targets"]:
        for row in db_results["v_economic_targets"]:
            lines.append(f"  v_economic_targets: SC-004={row.get('sc004_status','?')}")
    else:
        lines.append(f"  v_economic_targets: (no data — energy_systems table empty)")

    if "v_success_criteria" in db_results:
        lines.append(f"\n  Success Criteria Dashboard:")
        for row in db_results["v_success_criteria"]:
            lines.append(f"    {row['criterion']}: {row['description']} → {row['status']}")

    # Cleanup note
    lines.append(f"\n  --- Notes ---")
    lines.append(f"  Multiple wind_turbine_system entries exist from re-runs.")
    lines.append(f"  Only the latest (most recent created_at) is current.")
    lines.append(f"  The energy_systems table enforces SC-004 via CHECK")
    lines.append(f"  constraints, so failing designs are blocked at SQL level.")
    lines.append(f"")

    return "\n".join(lines)


def main():
    # Evaluate targets
    sc_targets = check_sc_targets()

    # Clean up duplicate turbines from previous re-runs
    with database() as db:
        rows = db.execute(
            """SELECT id FROM wind_turbine_systems
               ORDER BY created_at DESC"""
        ).fetchall()
        if len(rows) > 1:
            for row in rows[1:]:
                # Delete from objects — CASCADE removes detail row
                db.execute("DELETE FROM objects WHERE id = ?", (row["id"],))
            db.commit()

    # Query database views
    db_results = query_validation_views()

    # Format and print report
    report = format_target_report(sc_targets, db_results)
    print(report)

    # Return 0 only if ALL SC targets pass
    all_pass = (
        sc_targets["SC-004"]["overall"]
        and sc_targets["SC-005"]["overall"]
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    main()
