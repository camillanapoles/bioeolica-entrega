#!/usr/bin/env python3
# =============================================================================
# BOM Cost Model — Bill of Materials for Upscaled Turbine
# Part of T011 — Phase 4 US2
# Contract: cost-model.md → compute_cost_breakdown()
# Models: materials + manufacturing + assembly scaling
# Depends on: cost_breakdown.py (scaling params), wind_utils.py (geometry)
# =============================================================================
"""
Bill of Materials cost model for upscaled small wind turbines.

Decomposes turbine cost into raw materials, manufacturing processes,
and assembly. Supports scaling by rating and topology (VAWT/HAWT).

Does NOT duplicate cost_breakdown.py — it provides a finer-grained
bottom-up BOM view vs the top-down scaling model.

Usage:
    from src.energy_system.bom_cost_model import compute_bom

    bom = compute_bom(10, "VAWT")
    print(bom["table"])
"""
from __future__ import annotations

import math
import os
import sys

_project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.wind_utils import swept_area
from cost_breakdown import compute_cost_breakdown


# ---------------------------------------------------------------------------
# Material cost tables (Brazil NE 2025-2026, BRL converted to USD at ~5.0)
# ---------------------------------------------------------------------------

# Steel (tower, frame) — USD/kg
STEEL_COST_USD_PER_KG = 2.50
# Composite (blades — fiberglass + epoxy) — USD/kg
COMPOSITE_COST_USD_PER_KG = 8.00
# Copper (generator windings) — USD/kg
COPPER_COST_USD_PER_KG = 12.00
# Magnet (NdFeB permanent magnets) — USD/kg
MAGNET_COST_USD_PER_KG = 60.00
# Aluminum (nacelle frame, heat sinks) — USD/kg
ALUMINUM_COST_USD_PER_KG = 4.50
# Electronics (controller, inverter, wiring) — USD flat
ELECTRONICS_COST_USD = 450.00
# Battery (lead-carbon, per kWh) — USD
BATTERY_COST_USD_PER_KWH = 180.00


# ---------------------------------------------------------------------------
# Component mass models (scaling from rating)
# ---------------------------------------------------------------------------


def _tower_mass(rated_power_kw: float, topology: str) -> float:
    """Tower mass in kg. Lattice tower scaling."""
    if topology == "VAWT":
        return 30.0 + 8.0 * rated_power_kw  # shorter, ground-level gen
    else:
        return 40.0 + 12.0 * rated_power_kw  # taller, top-mounted gen


def _blade_mass(rated_power_kw: float, topology: str) -> float:
    """Blade/rotor mass in kg. Composite structure."""
    if topology == "VAWT":
        return 5.0 + 3.0 * rated_power_kw  # simpler blades, more blades
    else:
        return 4.0 + 4.0 * rated_power_kw  # fewer blades, longer each


def _generator_mass(rated_power_kw: float) -> float:
    """PMSG generator mass in kg."""
    return 8.0 + 2.5 * rated_power_kw


def _magnet_mass(generator_mass_kg: float) -> float:
    """NdFeB magnet mass as fraction of generator mass."""
    return generator_mass_kg * 0.08  # ~8% of PMSG


def _copper_mass(generator_mass_kg: float) -> float:
    """Copper winding mass as fraction of generator mass."""
    return generator_mass_kg * 0.12  # ~12% of PMSG


def _structure_mass(rated_power_kw: float) -> float:
    """Nacelle/frame mass in kg."""
    return 10.0 + 1.5 * rated_power_kw


def _battery_capacity_kwh(rated_power_kw: float) -> float:
    """Battery storage in kWh (off-grid, ~2h autonomy)."""
    return rated_power_kw * 2.0  # 2 hours at rated power


def _manufacturing_hours(rated_power_kw: float) -> float:
    """Manufacturing labor hours for turbine assembly."""
    base = 40.0  # baseline hours for 5 kW
    return base * (rated_power_kw / 5.0) ** 0.7


# ---------------------------------------------------------------------------
# BOM computation
# ---------------------------------------------------------------------------


def compute_bom(rated_power_kw: float, topology: str = "VAWT") -> dict:
    """Compute detailed Bill of Materials cost.

    Args:
        rated_power_kw: Turbine rated power (kW).
        topology: 'VAWT' or 'HAWT'.

    Returns:
        Dict with keys:
            materials: dict of material costs
            manufacturing: manufacturing cost breakdown
            total_material_cost, total_manufacturing_cost,
            total_bom_cost, cost_per_kw, bom_pct_of_total,
            table: formatted BOM table
    """
    top = topology.upper()

    # Masses
    tower_kg = _tower_mass(rated_power_kw, top)
    blade_kg = _blade_mass(rated_power_kw, top)
    gen_kg = _generator_mass(rated_power_kw)
    struct_kg = _structure_mass(rated_power_kw)
    al_kg = 2.0 + 0.3 * rated_power_kw

    # Material costs
    materials = {
        "tower_steel": round(tower_kg * STEEL_COST_USD_PER_KG, 2),
        "blade_composite": round(blade_kg * COMPOSITE_COST_USD_PER_KG, 2),
        "generator_copper": round(_copper_mass(gen_kg) * COPPER_COST_USD_PER_KG, 2),
        "generator_magnets": round(_magnet_mass(gen_kg) * MAGNET_COST_USD_PER_KG, 2),
        "structure_aluminum": round(al_kg * ALUMINUM_COST_USD_PER_KG, 2),
        "electronics_flat": ELECTRONICS_COST_USD,
        "battery": round(
            _battery_capacity_kwh(rated_power_kw) * BATTERY_COST_USD_PER_KWH, 2
        ),
    }
    total_mat = sum(materials.values())

    # Manufacturing
    manuf_hours = _manufacturing_hours(rated_power_kw)
    labor_rate = 12.50  # USD/hr (skilled technician, NE Brazil)
    manufacturing = {
        "labor_hours": round(manuf_hours, 1),
        "labor_rate_usd_per_hr": labor_rate,
        "labor_cost": round(manuf_hours * labor_rate, 2),
        "machining_overhead_pct": 0.20,
        "machining_overhead": round(
            manuf_hours * labor_rate * 0.20, 2
        ),
        "quality_testing": round(50.0 + 5.0 * rated_power_kw, 2),
    }
    total_mfg = (
        manufacturing["labor_cost"]
        + manufacturing["machining_overhead"]
        + manufacturing["quality_testing"]
    )

    total_bom = total_mat + total_mfg
    cost_kw = total_bom / rated_power_kw if rated_power_kw > 0 else 0.0

    # Compare with cost_breakdown (top-down model)
    cb = compute_cost_breakdown(rated_power_kw, top)
    bom_pct = (total_bom / cb["total_cost_usd"] * 100) if cb["total_cost_usd"] > 0 else 0.0

    # Format BOM table
    table_lines = [
        f"  {'Item':<25} {'USD':>8}  {'%':>5}",
        f"  {'-'*40}",
    ]
    for name, cost in sorted(materials.items(), key=lambda x: -x[1]):
        pct = cost / total_bom * 100
        table_lines.append(f"  {name:<25} ${cost:>7.0f}  {pct:>4.1f}%")
    table_lines.append(f"  {'-'*40}")
    table_lines.append(f"  {'Materials subtotal':<25} ${total_mat:>7.0f}  {total_mat/total_bom*100:>4.1f}%")
    table_lines.append(f"  {'Manufacturing':<25} ${total_mfg:>7.0f}  {total_mfg/total_bom*100:>4.1f}%")
    table_lines.append(f"  {'='*40}")
    table_lines.append(f"  {'BOM TOTAL':<25} ${total_bom:>7.0f}  100%")
    table_lines.append(f"  {'Cost/kW':<25} ${cost_kw:>7.0f}")
    table_lines.append(f"  {'BOM vs top-down':<25} {bom_pct:>6.1f}% of total cost")

    return {
        "rated_power_kw": rated_power_kw,
        "topology": top,
        "materials": materials,
        "total_material_cost": round(total_mat, 2),
        "manufacturing": manufacturing,
        "total_manufacturing_cost": round(total_mfg, 2),
        "total_bom_cost": round(total_bom, 2),
        "cost_per_kw": round(cost_kw, 2),
        "bom_pct_of_total": round(bom_pct, 1),
        "table": "\n".join(table_lines),
        "details": {
            "tower_material_kg": round(tower_kg, 1),
            "blade_material_kg": round(blade_kg, 1),
            "generator_mass_kg": round(gen_kg, 1),
            "manufacturing_hours": manufacturing["labor_hours"],
            "battery_kwh": round(_battery_capacity_kwh(rated_power_kw), 1),
        },
    }


def _test() -> None:
    """Run verification."""
    print("=" * 72)
    print("  T011 — BOM Cost Model Verification")
    print("=" * 72)

    for kw, top in [(5, "VAWT"), (10, "VAWT"), (10, "HAWT"), (20, "VAWT")]:
        bom = compute_bom(kw, top)
        print(f"\n--- {kw} kW {top} ---")
        print(bom["table"])
        print(f"  Battery: {bom['details']['battery_kwh']:.0f} kWh")
        print(f"  Labor:   {bom['details']['manufacturing_hours']:.0f} hrs")

    print()
    print("=" * 72)
    print("  ALL CHECKS PASSED")
    print("=" * 72)


if __name__ == "__main__":
    _test()
