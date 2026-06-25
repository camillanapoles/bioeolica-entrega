#!/usr/bin/env python3
"""
Comprehensive LCA report for paper mache + graphite composite
wind turbine blades. Consolidates inventory, carbon comparison,
and end-of-life assessment into a single validation report.

SC-010 targets:
  - >= 60% lower carbon vs. fiberglass
  - >= 80% biodegradable within 5 years
  - Source quality >= 8/10 for all data

Also computes:
  - Carbon payback period (years of wind energy operation to offset embodied carbon)
  - Embodied energy payback period
  - Overall environmental score

Usage:
    python src/02-wind-energy/energy-system/lca_report.py
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.registry import create_object
from src.common.database import database
from src.common.provenance import record_edge

# Import LCA modules (soft import — they work standalone too)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
try:
    from src.common.database import database as db_module
except ImportError:
    pass

# ---- System parameters (from system_sizing.py) ---- #

ANNUAL_ENERGY_KWH = 4098              # Annual energy production (kWh/yr)
GRID_CARBON_INTENSITY = 0.15          # kg CO2e/kWh (NE Brazil grid)
BLADE_COUNT = 3
BLADE_LIFETIME_YEARS = 20
TURBINE_LIFETIME_GENERATION_KWH = ANNUAL_ENERGY_KWH * BLADE_LIFETIME_YEARS

# ---- Inventory data (from lca_inventory.py, replicated for independence) ---- #

PAPER_MACHE_CARBON_PER_TURBINE = 64.6   # kg CO2e (3-blade, from lca_inventory)
FIBERGLASS_CARBON_PER_TURBINE = 390.0   # kg CO2e (3-blade, from carbon comparison)
PAPER_MACHE_BIODEGRADABLE_PCT = 73.5    # % mass-weighted (home compost best-case)
PAPER_MACHE_RECYCLABLE_PCT = 78.2       # % mass-weighted
FIBERGLASS_BIODEGRADABLE_PCT = 0.0
FIBERGLASS_RECYCLABLE_PCT = 5.0


@dataclass
class LCAReport:
    carbon_reduction_pct: float
    biodegradable_pct: float
    recyclable_pct: float
    source_quality: float
    carbon_payback_years: float
    embodied_energy_mj: float
    energy_payback_years: float
    grid_emissions_avoided_annual: float
    lifetime_carbon_benefit: float
    sc010_carbon_pass: bool
    sc010_biodegradable_pass: bool
    sc010_overall: bool
    environmental_score: float           # 0-100 composite


def compute_report() -> LCAReport:
    """Compute comprehensive LCA report."""
    # Carbon reduction
    carbon_reduction = (
        1 - PAPER_MACHE_CARBON_PER_TURBINE / FIBERGLASS_CARBON_PER_TURBINE
    ) * 100

    # Source quality (mass-weighted average)
    source_quality = 8.3  # from lca_inventory reported data

    # Carbon payback: years of turbine operation to offset embodied carbon
    # Embodied carbon = paper mache turbine carbon
    # Avoided annual emissions = grid intensity × annual energy
    annual_avoided = grid_intensity_kgco2e() * ANNUAL_ENERGY_KWH
    carbon_payback = PAPER_MACHE_CARBON_PER_TURBINE / annual_avoided if annual_avoided > 0 else 0

    # Embodied energy: approximate (from inventory data)
    embodied_energy = 486.0  # MJ (estimated from inventory — raw + production per turbine)
    annual_energy_output_mj = ANNUAL_ENERGY_KWH * 3.6  # kWh → MJ
    energy_payback = embodied_energy / annual_energy_output_mj if annual_energy_output_mj > 0 else 0

    # Lifetime carbon benefit
    lifetime_avoided = annual_avoided * BLADE_LIFETIME_YEARS
    lifetime_benefit = lifetime_avoided - PAPER_MACHE_CARBON_PER_TURBINE

    # SC-010 checks
    sc010_carbon = carbon_reduction >= 60
    sc010_biodeg = PAPER_MACHE_BIODEGRADABLE_PCT >= 80
    sc010_overall = sc010_carbon and sc010_biodeg

    # Composite environmental score (0-100)
    carbon_score = min(carbon_reduction / 60 * 40, 40)  # 0-40 pts (40 = 60% reduction)
    biodeg_score = min(PAPER_MACHE_BIODEGRADABLE_PCT / 80 * 30, 30)  # 0-30 pts (30 = 80%)
    recycle_score = min(PAPER_MACHE_RECYCLABLE_PCT / 80 * 15, 15)  # 0-15 pts
    payback_score = min((1 - carbon_payback / 3) * 10, 10) if carbon_payback < 3 else 0  # 0-10
    quality_score = min(source_quality / 8 * 5, 5)  # 0-5 pts
    env_score = round(carbon_score + biodeg_score + recycle_score + payback_score + quality_score, 1)

    return LCAReport(
        carbon_reduction_pct=round(carbon_reduction, 1),
        biodegradable_pct=PAPER_MACHE_BIODEGRADABLE_PCT,
        recyclable_pct=PAPER_MACHE_RECYCLABLE_PCT,
        source_quality=source_quality,
        carbon_payback_years=round(carbon_payback, 2),
        embodied_energy_mj=embodied_energy,
        energy_payback_years=round(energy_payback, 3),
        grid_emissions_avoided_annual=round(annual_avoided, 3),
        lifetime_carbon_benefit=round(lifetime_benefit, 2),
        sc010_carbon_pass=sc010_carbon,
        sc010_biodegradable_pass=sc010_biodeg,
        sc010_overall=sc010_overall,
        environmental_score=env_score,
    )


def grid_intensity_kgco2e() -> float:
    """Brazil NE grid carbon intensity (kg CO2e/kWh).

    Source: IEA 2023, Brazilian National Grid Operator (ONS) 2023.
    NE Brazil grid is ~80% wind+solar, ~15% hydro, ~5% fossil backup.
    """
    return GRID_CARBON_INTENSITY


def register_lca_report(report: LCAReport) -> str:
    """Register LCA report in SQLite."""
    model_id = create_object(
        "computational_model",
        tags=["lca", "lca_report_model", "analytical"],
        metadata={
            "source": "src/02-wind-energy/energy-system/lca_report.py",
            "type": "lca_report_model",
        },
    )

    obj_id = create_object(
        "simulation_result",
        tags=["lca", "report", "sc010", "environmental_score", "carbon_payback"],
        metadata={
            "source": "src/02-wind-energy/energy-system/lca_report.py",
            "type": "lca_comprehensive_report",
            "environmental_score": report.environmental_score,
            "sc010_overall": report.sc010_overall,
            "carbon_payback_years": report.carbon_payback_years,
        },
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
            (
                obj_id,
                model_id,
                json.dumps({
                    "carbon_reduction_pct": report.carbon_reduction_pct,
                    "biodegradable_pct": report.biodegradable_pct,
                    "recyclable_pct": report.recyclable_pct,
                    "source_quality": report.source_quality,
                    "carbon_payback_years": report.carbon_payback_years,
                    "embodied_energy_mj": report.embodied_energy_mj,
                    "energy_payback_years": report.energy_payback_years,
                    "grid_emissions_avoided_annual_kgco2e": report.grid_emissions_avoided_annual,
                    "lifetime_carbon_benefit_kgco2e": report.lifetime_carbon_benefit,
                    "sc010_carbon_pass": report.sc010_carbon_pass,
                    "sc010_biodegradable_pass": report.sc010_biodegradable_pass,
                    "sc010_overall": report.sc010_overall,
                    "environmental_score": report.environmental_score,
                    "system_parameters": {
                        "annual_energy_kwh": ANNUAL_ENERGY_KWH,
                        "lifetime_years": BLADE_LIFETIME_YEARS,
                        "grid_intensity_kgco2e_per_kwh": grid_intensity_kgco2e(),
                    },
                }),
                f"LCA report: env.score={report.environmental_score}/100, "
                f"SC-010={'PASS' if report.sc010_overall else 'FAIL'}",
            ),
        )
        db.commit()

    return obj_id


def report(report: LCAReport) -> str:
    """Format comprehensive LCA report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  COMPREHENSIVE LCA REPORT")
    lines.append("  Paper Mache + Graphite Composite Wind Turbine Blade")
    lines.append("  VAWT H-rotor Darrieus — Assentamento Sertao Sustentavel")
    lines.append("=" * 64)

    # System summary
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  SYSTEM PARAMETERS")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Turbine:            VAWT H-rotor Darrieus, 3 blades")
    lines.append(f"  Blade length:       3.5 m")
    lines.append(f"  Blade mass:         8.5 kg (paper mache)")
    lines.append(f"  Annual energy:      {ANNUAL_ENERGY_KWH:,} kWh/yr")
    lines.append(f"  Lifetime:           {BLADE_LIFETIME_YEARS} years")
    lines.append(f"  Grid intensity:     {grid_intensity_kgco2e()} kg CO2e/kWh (NE Brazil)")

    # Carbon footprint comparison
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  CARBON FOOTPRINT (3-blade turbine)")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Paper mache composite:   {PAPER_MACHE_CARBON_PER_TURBINE:>8.1f} kg CO2e")
    lines.append(f"  Fiberglass baseline:     {FIBERGLASS_CARBON_PER_TURBINE:>8.1f} kg CO2e")
    lines.append(f"  Carbon reduction:        {report.carbon_reduction_pct:>7.1f}%")
    lines.append(f"  SC-010 target >=60%:     "
                 f"{'✅ PASS' if report.sc010_carbon_pass else '❌ FAIL'}")

    # Carbon payback
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  CARBON PAYBACK ANALYSIS")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Grid emissions avoided/yr:  {report.grid_emissions_avoided_annual:>8.3f} kg CO2e")
    lines.append(f"  Carbon payback period:     "
                 f"{report.carbon_payback_years:>8.2f} years")
    lines.append(f"  Embodied energy:           "
                 f"{report.embodied_energy_mj:>8.0f} MJ")
    lines.append(f"  Energy payback period:     "
                 f"{report.energy_payback_years:>8.3f} years")
    lines.append(f"  Lifetime carbon benefit:   "
                 f"{report.lifetime_carbon_benefit:>8.1f} kg CO2e")

    # Biodegradability / recyclability
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  BIODEGRADABILITY / RECYCLABILITY")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  {'Metric':<30} {'Paper Mache':>12} {'Fiberglass':>12}")
    lines.append(f"  {'─' * 56}")
    lines.append(f"  {'Biodegradable (5yr)':<30} {PAPER_MACHE_BIODEGRADABLE_PCT:>11.1f}%"
                 f" {FIBERGLASS_BIODEGRADABLE_PCT:>11.1f}%")
    lines.append(f"  {'Recyclable':<30} {PAPER_MACHE_RECYCLABLE_PCT:>11.1f}%"
                 f" {FIBERGLASS_RECYCLABLE_PCT:>11.1f}%")
    lines.append(f"  SC-010 >=80%:              "
                 f"{'✅ PASS' if report.sc010_biodegradable_pass else '❌ FAIL'} "
                 f"({report.biodegradable_pct}%)")

    # Source quality
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  DATA QUALITY")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Avg. source quality:  {report.source_quality}/10")
    lines.append(f"  SC-010 >=8/10:        "
                 f"{'✅ PASS' if report.source_quality >= 8 else '❌ FAIL'}")

    # Environmental score
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  OVERALL ENVIRONMENTAL SCORE: {report.environmental_score:.1f}/100")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Carbon reduction (0-40):    "
                 f"{min(report.carbon_reduction_pct / 60 * 40, 40):.1f}")
    lines.append(f"  Biodegradability (0-30):    "
                 f"{min(report.biodegradable_pct / 80 * 30, 30):.1f}")
    lines.append(f"  Recyclability (0-15):       "
                 f"{min(report.recyclable_pct / 80 * 15, 15):.1f}")
    lines.append(f"  Payback period (0-10):      "
                 f"{min((1 - report.carbon_payback_years / 3) * 10, 10) if report.carbon_payback_years < 3 else 0:.1f}")
    lines.append(f"  Data quality (0-5):         "
                 f"{min(report.source_quality / 8 * 5, 5):.1f}")

    # SC-010 verdict
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  SC-010 VERDICT")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  >=60% carbon reduction:  "
                 f"{'✅' if report.sc010_carbon_pass else '❌'} "
                 f"({report.carbon_reduction_pct}%)")
    lines.append(f"  >=80% biodegradable:     "
                 f"{'✅' if report.sc010_biodegradable_pass else '❌'} "
                 f"({report.biodegradable_pct}%)")
    lines.append(f"  Source quality >=8:      "
                 f"{'✅' if report.source_quality >= 8 else '❌'} "
                 f"({report.source_quality})")
    lines.append(f"")
    lines.append(f"  SC-010 OVERALL: "
                 f"{'✅ PASS' if report.sc010_overall else '❌ FAIL'}")
    lines.append(f"  Environmental Score: "
                 f"{report.environmental_score}/100")
    lines.append("")

    return "\n".join(lines)


def main():
    report_data = compute_report()
    print(report(report_data))

    obj_id = register_lca_report(report_data)
    print(f"  Registered LCA report: {obj_id}")

    return 0 if report_data.sc010_overall else 1


if __name__ == "__main__":
    main()
