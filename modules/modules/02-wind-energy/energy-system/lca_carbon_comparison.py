#!/usr/bin/env python3
"""
Carbon footprint comparison: paper mache + graphite composite blade
vs. conventional fiberglass blade baseline.

SC-010 target: >= 60% lower carbon footprint vs. fiberglass.

Sources:
  - Fiberglass blade production emission factor: 8.5-12.0 kg CO2e/kg
    (Liu et al. 2022, Renewable & Sustainable Energy Reviews; Ecoinvent 3.9)
  - Fiberglass blade mass (3.5m small wind): ~10 kg (typical)
  - Transport of glass fiber: 0.3-0.8 kg CO2e/kg (regional sourcing)
  - Paper mache factors from lca_inventory.py

Usage:
    python src/02-wind-energy/energy-system/lca_carbon_comparison.py
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.common.registry import create_object
from src.common.database import database
from src.common.provenance import record_edge


# ---- Fiberglass baseline data ---- #

@dataclass
class FiberglassData:
    name: str
    mass_kg: float
    production_kgco2e_per_kg: float
    transport_kgco2e_per_kg: float
    eol_kgco2e_per_kg: float          # incineration / landfill
    recyclable_pct: float
    biodegradable_pct: float
    source_quality: int
    notes: str

    @property
    def total_carbon_kgco2e(self) -> float:
        return self.mass_kg * (self.production_kgco2e_per_kg
                                + self.transport_kgco2e_per_kg
                                + self.eol_kgco2e_per_kg)


FIBERGLASS_BASELINE = {
    "production": FiberglassData(
        name="Fiberglass blade production (hand layup, polyester resin)",
        mass_kg=10.0,
        production_kgco2e_per_kg=9.5,        # 8.5-12.0, midpoint
        transport_kgco2e_per_kg=0.5,          # regional transport
        eol_kgco2e_per_kg=0.8,                # landfill (non-biodegradable)
        recyclable_pct=5.0,                    # fiberglass recycling < 5% globally
        biodegradable_pct=0.0,                 # thermoset polymer, not biodegradable
        source_quality=9,
        notes="Hand lay-up fiberglass (polyester resin + E-glass fiber). "
              "Dominant in small wind blades (<5 kW).",
    ),
    "transport": FiberglassData(
        name="Fiberglass transport (factory → community, 500 km)",
        mass_kg=10.0,
        production_kgco2e_per_kg=0.0,         # accounted in production
        transport_kgco2e_per_kg=0.5,
        eol_kgco2e_per_kg=0.0,
        recyclable_pct=0.0,
        biodegradable_pct=0.0,
        source_quality=9,
        notes="Same transport distance as paper mache — identical logistics.",
    ),
    "eol": FiberglassData(
        name="Fiberglass end-of-life (landfill, non-biodegradable)",
        mass_kg=10.0,
        production_kgco2e_per_kg=0.0,
        transport_kgco2e_per_kg=0.0,
        eol_kgco2e_per_kg=0.8,               # landfill emissions
        recyclable_pct=5.0,
        biodegradable_pct=0.0,
        source_quality=7,
        notes="Thermoset composites cannot be remelted. "
              "Most end in landfill. Incineration adds 1.5 kg CO2e/kg.",
    ),
}

# Paper mache inventory data (from lca_inventory.py, 3-blade turbine)
PAPER_MACHE_BLADE_MASS_KG = 8.5      # per blade (lighter than fiberglass)
FIBERGLASS_BLADE_MASS_KG = 10.0       # per blade
BLADE_COUNT = 3


@dataclass
class LCAComparison:
    paper_mache_per_blade: Dict[str, float]
    fiberglass_per_blade: Dict[str, float]
    paper_mache_turbine: Dict[str, float]
    fiberglass_turbine: Dict[str, float]
    carbon_reduction_pct: float            # full system (incl. shared tower/foundation)
    blade_only_carbon_reduction_pct: float  # blade material only
    biodegradable_ratio: float
    recyclable_ratio: float
    sc010_carbon_pass: bool
    sc010_biodegradable_pass: bool
    sc010_overall: bool
    details: Dict = field(default_factory=dict)


def compare_carbon() -> LCAComparison:
    """Compare paper mache composite vs. fiberglass carbon footprint."""
    # Paper mache per-blade carbon (aggregated from lca_inventory)
    # Re-derive from the known inventory data
    # Raw materials + production + transport + installation per blade
    paper_raw_carbon = (
        3.8 * 0.024 +      # waste paper
        2.2 * 2.3 +        # PVA
        0.8 * 1.8 +        # graphite
        1.7 * 0.001        # water
    )
    paper_prod_carbon = (
        3.8 * 0.002 +      # shredding
        8.5 * 0.004 +      # mixing (total batch mass)
        8.5 * 0.006 +      # molding
        8.5 * 0.02 +       # drying
        0.8 * 0.002        # graphite coating
    )
    paper_transport_carbon = (
        3.8 * 0.015 +      # paper collection
        0.8 * 0.06 +       # graphite transport
        8.5 * 0.15         # blade delivery
    )
    # Installation is shared across turbine (tower+foundation amortized)
    # Per blade: share of tower+foundation / 3
    paper_install_carbon = (4800 * 0.15 + 350 * 2.8 + 40.0) / 3  # foundation + steel + assembly / 3 blades
    paper_per_blade = {
        "raw_materials": round(paper_raw_carbon, 3),
        "production": round(paper_prod_carbon, 3),
        "transportation": round(paper_transport_carbon, 3),
        "installation": round(paper_install_carbon, 3),
        "total": round(paper_raw_carbon + paper_prod_carbon + paper_transport_carbon
                       + paper_install_carbon, 3),
    }

    # Fiberglass per-blade carbon
    fg_blade = FIBERGLASS_BASELINE["production"]
    fg_transport = FIBERGLASS_BASELINE["transport"]
    fg_eol = FIBERGLASS_BASELINE["eol"]
    fg_prod = fg_blade.mass_kg * fg_blade.production_kgco2e_per_kg
    fg_trans = fg_blade.mass_kg * fg_blade.transport_kgco2e_per_kg
    fg_eol_val = fg_blade.mass_kg * fg_blade.eol_kgco2e_per_kg
    # Fiberglass also needs tower+foundation (same turbine structure)
    fg_install = paper_install_carbon  # identical tower/foundation
    fiberglass_per_blade = {
        "production": round(fg_prod, 3),
        "transportation": round(fg_trans + fg_transport.transport_kgco2e_per_kg, 3),
        "installation": round(fg_install, 3),
        "end_of_life": round(fg_eol_val, 3),
        "total": round(fg_prod + fg_trans + fg_install + fg_eol_val, 3),
    }

    # Turbine totals (3 blades)
    paper_turbine = {
        "blades_carbon": round(paper_per_blade["total"] * BLADE_COUNT, 3),
        "total": round(paper_per_blade["total"] * BLADE_COUNT, 3),
    }
    fg_turbine = {
        "blades_carbon": round(fiberglass_per_blade["total"] * BLADE_COUNT, 3),
        "total": round(fiberglass_per_blade["total"] * BLADE_COUNT, 3),
    }

    # SC-010: >= 60% lower carbon (blade material only — excludes shared tower/foundation)
    reduction = (1 - paper_turbine["total"] / fg_turbine["total"]) * 100
    paper_blade_only_carbon = paper_per_blade["total"] - paper_install_carbon
    fg_blade_only_carbon = fiberglass_per_blade["total"] - fg_install
    blade_only_reduction = (
        (1 - paper_blade_only_carbon / fg_blade_only_carbon) * 100
        if fg_blade_only_carbon > 0 else 0
    )
    sc010_carbon = blade_only_reduction >= 60  # SC-010 uses blade material comparison

    # Biodegradability comparison (blade-only, excludes water which evaporates during drying)
    blade_dry_mass = 3.8 + 2.2 + 0.8  # paper + PVA + graphite (water evaporates)
    paper_biodeg = (
        3.8 * 1.0 +     # paper: 100%
        2.2 * 0.3 +     # PVA: 30%
        0.8 * 0.0       # graphite: 0%
    ) / blade_dry_mass
    fg_biodeg = 0.0  # fiberglass: 0% biodegradable

    # Recyclability (blade-only, excludes water)
    paper_recycle = (
        3.8 * 0.9 +     # paper: 90%
        2.2 * 0.2 +     # PVA: 20%
        0.8 * 0.85      # graphite: 85%
    ) / blade_dry_mass
    fg_recycle = 0.05   # fiberglass: 5% recyclable

    return LCAComparison(
        paper_mache_per_blade=paper_per_blade,
        fiberglass_per_blade=fiberglass_per_blade,
        paper_mache_turbine=paper_turbine,
        fiberglass_turbine=fg_turbine,
        carbon_reduction_pct=round(reduction, 1),
        blade_only_carbon_reduction_pct=round(blade_only_reduction, 1),
        biodegradable_ratio=round(paper_biodeg * 100, 1),
        recyclable_ratio=round(paper_recycle * 100, 1),
        sc010_carbon_pass=sc010_carbon,
        sc010_biodegradable_pass=paper_biodeg >= 0.8,
        sc010_overall=sc010_carbon and paper_biodeg >= 0.8,
        details={
            "paper_mache_biodegradable_pct": round(paper_biodeg * 100, 1),
            "fiberglass_biodegradable_pct": round(fg_biodeg * 100, 1),
            "paper_mache_recyclable_pct": round(paper_recycle * 100, 1),
            "fiberglass_recyclable_pct": round(fg_recycle * 100, 1),
            "blade_count": BLADE_COUNT,
            "paper_mache_mass_kg": PAPER_MACHE_BLADE_MASS_KG,
            "fiberglass_mass_kg": FIBERGLASS_BLADE_MASS_KG,
        },
    )


def register_comparison(result: LCAComparison) -> str:
    """Register comparison result in SQLite."""
    model_id = create_object(
        "computational_model",
        tags=["lca", "carbon_comparison_model", "analytical"],
        metadata={
            "source": "src/02-wind-energy/energy-system/lca_carbon_comparison.py",
            "type": "carbon_comparison_model",
        },
    )

    obj_id = create_object(
        "simulation_result",
        tags=["lca", "carbon_comparison", "sc010", "paper_vs_fiberglass"],
        metadata={
            "source": "src/02-wind-energy/energy-system/lca_carbon_comparison.py",
            "type": "carbon_footprint_comparison",
            "carbon_reduction_pct": result.carbon_reduction_pct,
            "biodegradable_pct": result.biodegradable_ratio,
            "sc010_pass": result.sc010_overall,
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
                    "paper_mache_per_blade": result.paper_mache_per_blade,
                    "fiberglass_per_blade": result.fiberglass_per_blade,
                    "paper_mache_turbine": result.paper_mache_turbine,
                    "fiberglass_turbine": result.fiberglass_turbine,
                    "carbon_reduction_pct": result.carbon_reduction_pct,
                    "blade_only_carbon_reduction_pct": result.blade_only_carbon_reduction_pct,
                    "sc010_carbon_pass": result.sc010_carbon_pass,
                    "sc010_biodegradable_pass": result.sc010_biodegradable_pass,
                    "sc010_overall": result.sc010_overall,
                    "details": result.details,
                }),
                f"SC-010: {result.carbon_reduction_pct}% carbon reduction, "
                f"{'PASS' if result.sc010_overall else 'FAIL'}",
            ),
        )
        db.commit()

    return obj_id


def report(result: LCAComparison) -> str:
    """Format comparison report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  CARBON FOOTPRINT COMPARISON")
    lines.append("  Paper Mache + Graphite vs. Fiberglass Baseline")
    lines.append("  VAWT H-rotor Darrieus — 3.5m blade")
    lines.append("=" * 64)

    # Per-blade comparison table
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  PER-BLADE CARBON FOOTPRINT (kg CO2e)")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  {'Category':<20} {'Paper Mache':>14} {'Fiberglass':>14} {'Unit'}")
    lines.append(f"  {'─' * 56}")
    all_categories = set(result.paper_mache_per_blade.keys()) | set(result.fiberglass_per_blade.keys())
    for cat in sorted(all_categories):
        pm = result.paper_mache_per_blade.get(cat, 0)
        fg = result.fiberglass_per_blade.get(cat, 0)
        lines.append(f"  {cat:<20} {pm:>14.3f} {fg:>14.3f} kg CO2e")
    lines.append(f"  {'─' * 56}")
    lines.append(f"  {'TOTAL':<20} {result.paper_mache_per_blade['total']:>14.3f}"
                 f" {result.fiberglass_per_blade['total']:>14.3f} kg CO2e")

    # Turbine comparison
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  3-BLADE TURBINE CARBON FOOTPRINT")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  Paper mache composite:  "
                 f"{result.paper_mache_turbine['total']:>10.3f} kg CO2e")
    lines.append(f"  Fiberglass baseline:    "
                 f"{result.fiberglass_turbine['total']:>10.3f} kg CO2e")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  Carbon reduction (system): "
                 f"{result.carbon_reduction_pct:>9.1f}%")
    lines.append(f"  Carbon reduction (blade):  "
                 f"{result.blade_only_carbon_reduction_pct:>9.1f}%")

    # Biodegradability comparison
    lines.append(f"\n  {'─' * 60}")
    lines.append(f"  BIODEGRADABILITY / RECYCLABILITY")
    lines.append(f"  {'─' * 60}")
    lines.append(f"  {'Metric':<25} {'Paper Mache':>14} {'Fiberglass':>14}")
    lines.append(f"  {'─' * 56}")
    lines.append(f"  {'Biodegradable':<25} {result.details['paper_mache_biodegradable_pct']:>13.1f}%"
                 f" {result.details['fiberglass_biodegradable_pct']:>13.1f}%")
    lines.append(f"  {'Recyclable':<25} {result.details['paper_mache_recyclable_pct']:>13.1f}%"
                 f" {result.details['fiberglass_recyclable_pct']:>13.1f}%")

    # SC-010 validation
    lines.append(f"\n  {'═' * 60}")
    lines.append(f"  SC-010 VALIDATION")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  Target: >= 60% lower carbon than fiberglass")
    lines.append(f"  System-level: {result.carbon_reduction_pct}% → "
                 f"{'✅' if result.carbon_reduction_pct >= 60 else '❌'} "
                 f"(incl. shared tower/foundation)")
    lines.append(f"  Blade material: {result.blade_only_carbon_reduction_pct}% → "
                 f"{'✅ PASS' if result.sc010_carbon_pass else '❌ FAIL'}"
                 f" (excl. shared tower/foundation)")
    lines.append(f"  Target: >= 80% biodegradable")
    lines.append(f"  Result: {result.biodegradable_ratio}% → "
                 f"{'✅ PASS' if result.sc010_biodegradable_pass else '❌ FAIL'}")
    lines.append(f"\n  SC-010 OVERALL: "
                 f"{'✅ PASS' if result.sc010_overall else '❌ FAIL'}")
    lines.append("")

    return "\n".join(lines)


def main():
    result = compare_carbon()
    print(report(result))

    obj_id = register_comparison(result)
    print(f"  Registered comparison: {obj_id}")

    return 0 if result.sc010_overall else 1


if __name__ == "__main__":
    main()
