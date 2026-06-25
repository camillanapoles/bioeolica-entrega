#!/usr/bin/env python3
"""
LCOE (Levelized Cost of Energy) and installed cost calculation
for small wind VAWT system in semi-arid NE Brazil.

SC-004 targets: LCOE < $0.15/kWh, cost < $3,000/kW installed.
"""

import sys
import os
import json
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.registry import create_object
from src.common.database import database


# ---- cost inputs ---- #

# Turbine
TURBINE_COST_PER_KW = 1800  # $/kW (VAWT DIY/local fab, lower than commercial HAWT)
TOWER_COST = 3500  # $ (30m lattice, galvanized)
BATTERY_COST_PER_KWH = 200  # $/kWh (lead-carbon deep-cycle)
INVERTER_COST_PER_KW = 300  # $/kW
CONTROLLER_COST = 800  # $ (MPPT)
INSTALLATION_PCT = 0.15  # 15% of equipment
TRANSPORT_FLAT = 2000  # $ (rural NE Brazil access)
BOS_PCT = 0.10  # 10% balance of system

# Financial
DISCOUNT_RATE = 0.08  # 8% (Brazil long-term SELIC + risk premium)
LIFETIME_YEARS = 20  # small wind turbine design life
OM_PCT_PER_YEAR = 0.02  # 2% of installed cost/yr (community O&M)
BATTERY_REPLACEMENT_YEAR = 8  # replace batteries at year 8
BATTERY_REPLACEMENT_PCT = 0.60  # 60% of original battery cost (recycling credit)


@dataclass
class LCOEResult:
    rated_power_kw: float
    annual_energy_kwh: float
    installed_cost_usd: float
    cost_per_kw_usd: float
    lcoe_usd_per_kwh: float
    turbine_cost: float
    tower_cost: float
    battery_cost: float
    inverter_cost: float
    controller_cost: float
    installation_cost: float
    transport_cost: float
    bos_cost: float
    om_annual: float
    battery_replacement_cost: float
    npv_costs: float
    npv_energy: float
    sc004_cost: str
    sc004_lcoe: str


def calculate_lcoe(
    rated_power_kw: float,
    annual_energy_kwh: float,
    battery_capacity_kwh: float,
    discount_rate: float = DISCOUNT_RATE,
    lifetime: int = LIFETIME_YEARS,
) -> LCOEResult:
    # Equipment costs
    turbine = rated_power_kw * TURBINE_COST_PER_KW
    tower = TOWER_COST
    battery = battery_capacity_kwh * BATTERY_COST_PER_KWH
    inverter = rated_power_kw * INVERTER_COST_PER_KW
    controller = CONTROLLER_COST
    equipment = turbine + tower + battery + inverter + controller

    installation = equipment * INSTALLATION_PCT
    transport = TRANSPORT_FLAT
    bos = equipment * BOS_PCT

    installed = equipment + installation + transport + bos
    cost_per_kw = installed / rated_power_kw if rated_power_kw > 0 else 0

    # O&M
    om_annual = installed * OM_PCT_PER_YEAR
    battery_repl = battery * BATTERY_REPLACEMENT_PCT

    # NPV
    npv_costs = installed  # year 0
    npv_energy = 0.0
    for y in range(1, lifetime + 1):
        df = (1 + discount_rate) ** (-y)
        npv_costs += om_annual * df
        # Battery replacement at year 8
        if y == BATTERY_REPLACEMENT_YEAR:
            npv_costs += battery_repl * df
        # Degradation: 0.5%/yr
        energy_y = annual_energy_kwh * (1 - 0.005) ** (y - 1)
        npv_energy += energy_y * df

    lcoe = npv_costs / npv_energy if npv_energy > 0 else 999.0

    return LCOEResult(
        rated_power_kw=rated_power_kw,
        annual_energy_kwh=annual_energy_kwh,
        installed_cost_usd=round(installed, 0),
        cost_per_kw_usd=round(cost_per_kw, 0),
        lcoe_usd_per_kwh=round(lcoe, 4),
        turbine_cost=round(turbine, 0),
        tower_cost=tower,
        battery_cost=round(battery, 0),
        inverter_cost=round(inverter, 0),
        controller_cost=controller,
        installation_cost=round(installation, 0),
        transport_cost=transport,
        bos_cost=round(bos, 0),
        om_annual=round(om_annual, 0),
        battery_replacement_cost=round(battery_repl, 0),
        npv_costs=round(npv_costs, 0),
        npv_energy=round(npv_energy, 0),
        sc004_cost="PASS" if cost_per_kw < 3000 else "FAIL",
        sc004_lcoe="PASS" if lcoe < 0.15 else "FAIL",
    )


def report(lcoe: LCOEResult) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  LCOE CALCULATION — Assentamento Sertao Sustentavel")
    lines.append("=" * 60)

    lines.append(f"\n  --- Cost Breakdown ---")
    lines.append(f"  Turbine ({lcoe.rated_power_kw:.1f} kW × ${TURBINE_COST_PER_KW}/kW): ${lcoe.turbine_cost:,.0f}")
    lines.append(f"  Tower (30m lattice):         ${lcoe.tower_cost:,.0f}")
    lines.append(f"  Battery bank:                ${lcoe.battery_cost:,.0f}")
    lines.append(f"  Inverter/Controller:         ${lcoe.inverter_cost + lcoe.controller_cost:,.0f}")
    lines.append(f"  Installation (15%):          ${lcoe.installation_cost:,.0f}")
    lines.append(f"  Transport:                   ${lcoe.transport_cost:,.0f}")
    lines.append(f"  BOS (10%):                   ${lcoe.bos_cost:,.0f}")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  INSTALLED COST:              ${lcoe.installed_cost_usd:,.0f}")

    lines.append(f"\n  --- Metrics ---")
    lines.append(f"  Cost per kW:                 ${lcoe.cost_per_kw_usd:,}/kW")
    lines.append(f"  Annual energy:               {lcoe.annual_energy_kwh:,.0f} kWh/yr")
    lines.append(f"  O&M (${lcoe.om_annual:,}/yr @ {OM_PCT_PER_YEAR*100:.0f}%)")
    lines.append(f"  Battery replacement (yr {BATTERY_REPLACEMENT_YEAR}): ${lcoe.battery_replacement_cost:,}")
    lines.append(f"  NPV costs ({LIFETIME_YEARS}yr @ {DISCOUNT_RATE*100:.0f}%): ${lcoe.npv_costs:,.0f}")
    lines.append(f"  NPV energy:                  {lcoe.npv_energy:,.0f} kWh")
    lines.append(f"  LCOE:                        ${lcoe.lcoe_usd_per_kwh:.4f}/kWh")

    lines.append(f"\n  --- SC-004 Validation ---")
    lines.append(f"  Cost < $3,000/kW: ${lcoe.cost_per_kw_usd:,}/kW → {lcoe.sc004_cost}")
    lines.append(f"  LCOE < $0.15/kWh: ${lcoe.lcoe_usd_per_kwh:.4f}/kWh → {lcoe.sc004_lcoe}")
    lines.append("")
    sc004_all = lcoe.sc004_cost == "PASS" and lcoe.sc004_lcoe == "PASS"
    lines.append(f"  SC-004 OVERALL: {'✅ PASS' if sc004_all else '❌ FAIL'}")
    lines.append("=" * 60)

    return "\n".join(lines)


def register_lcoe(lcoe: LCOEResult) -> str:
    """Register LCOE results in SQLite."""
    data = {
        "installed_cost_usd": lcoe.installed_cost_usd,
        "cost_per_kw_usd": lcoe.cost_per_kw_usd,
        "lcoe_usd_per_kwh": lcoe.lcoe_usd_per_kwh,
        "cost_breakdown": {
            "turbine": lcoe.turbine_cost,
            "tower": lcoe.tower_cost,
            "battery": lcoe.battery_cost,
            "inverter": lcoe.inverter_cost,
            "controller": lcoe.controller_cost,
            "installation": lcoe.installation_cost,
            "transport": lcoe.transport_cost,
            "bos": lcoe.bos_cost,
        },
        "financial_params": {
            "discount_rate": DISCOUNT_RATE,
            "lifetime_years": LIFETIME_YEARS,
            "om_pct": OM_PCT_PER_YEAR,
        },
        "sc004": {
            "cost": lcoe.sc004_cost,
            "lcoe": lcoe.sc004_lcoe,
        },
    }

    model_id = create_object(
        "computational_model",
        tags=["lcoe", "energy_system_model"],
        metadata={"type": "LCOE_calculation",
                   "source": "src/02-wind-energy/energy-system/lcoe_calculation.py"},
    )
    obj_id = create_object(
        "simulation_result",
        tags=["lcoe", "sc004", "energy_cost"],
        metadata={"source": "src/02-wind-energy/energy-system/lcoe_calculation.py"},
    )

    with database() as db:
        db.execute(
            """INSERT INTO computational_models
               (id, model_type, domain, solver_software, solver_version,
                boundary_conditions, material_model, material_properties)
               VALUES (?, 'analytical', 'coupled', 'python_numpy', '1.0',
                       'N/A_analytical', 'N/A_analytical', 'N/A_analytical')""",
            (model_id,),
        )
        db.execute(
            """INSERT INTO simulation_results
               (id, model_id, run_timestamp, output_quantities, notes)
               VALUES (?, ?, datetime('now'), ?, ?)""",
            (obj_id, model_id, json.dumps(data),
             f"LCOE=${lcoe.lcoe_usd_per_kwh:.4f}/kWh, cost=${lcoe.cost_per_kw_usd:,}/kW"),
        )
        db.commit()

    return obj_id


def main():
    # Get sizing from system_sizing module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from system_sizing import size_system

    sizing = size_system()
    lcoe = calculate_lcoe(sizing.rated_power_kw, sizing.annual_energy_kwh, sizing.battery_capacity_kwh)

    print(report(lcoe))
    lcoe_id = register_lcoe(lcoe)
    print(f"\n  Registered LCOE: {lcoe_id}")

    all_pass = lcoe.sc004_cost == "PASS" and lcoe.sc004_lcoe == "PASS"
    return 0 if all_pass else 1


if __name__ == "__main__":
    from dataclasses import dataclass
    main()
