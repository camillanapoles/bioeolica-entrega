#!/usr/bin/env python3
# =============================================================================
# Blade Mass and Cost Estimation — Composite Biomaterial for Wind Energy
# Phase 5 — Wind Turbine Blade Application | T043
# Reference: SC-004 economic targets (LCOE < $0.15/kWh, cost < $3,000/kW)
# Material: Paper mache + graphite composite (calibrated properties)
# =============================================================================
"""
Mass and cost estimation for the paper mache + graphite composite wind
turbine blade. Provides per-blade and per-rotor estimates.

Uses a simplified analytical blade model with distributed chord and
thickness to compute structural volume and mass.

Usage:
    python blade_cost_estimate.py

    Prints mass and cost summary for single blade and complete rotor.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Inline geometry constants (matches blade_geometry.py)
AIRFOIL = "NACA 0018"
MAX_THICKNESS_PCT = 0.18
CHORD_ROOT_M = 0.35
CHORD_TIP_M = 0.12


@dataclass
class BladeGeometry:
    """Simplified blade geometry for cost estimation.

    Mirrors the fields from src/02-wind-energy/structural/blade_geometry.py
    without depending on that module's file path.
    """
    blade_length_m: float = 3.5
    num_blades: int = 3

    def chord_at(self, fraction: float) -> float:
        """Interpolated chord at span fraction (0=root, 1=tip)."""
        return CHORD_ROOT_M + fraction * (CHORD_TIP_M - CHORD_ROOT_M)


DEFAULT_BLADE = BladeGeometry()

# ---------------------------------------------------------------------------
# Material cost parameters
# ---------------------------------------------------------------------------

# Material costs (USD per kg) — semi-urban Brazilian context, 2026
PAPER_COST_USD_PER_KG = 0.50        # Recycled newspaper / office paper
PVA_BINDER_COST_USD_PER_KG = 3.00   # PVA glue (industrial grade)
GRAPHITE_COST_USD_PER_KG = 8.00     # Flake graphite, industrial grade
LABOR_COST_USD_PER_HOUR = 5.00      # Semi-skilled labor (Brazilian NE region)

# Production parameters
BLADE_PRODUCTION_HOURS = 12.0       # Hours per blade (manual layup)
MOLD_COST_USD = 500.0               # Mold/tooling amortized per blade
OVERHEAD_PCT = 30.0                 # Overhead as % of direct costs
TRANSPORT_COST_USD = 200.0          # Transport per blade to installation site
INSTALLATION_COST_USD = 800.0       # Installation per blade (crane, crew)

# Composite composition (mass fractions)
PAPER_MASS_FRACTION = 0.55          # Paper fiber content
BINDER_MASS_FRACTION = 0.35         # PVA binder content
GRAPHITE_MASS_FRACTION = 0.10       # Graphite coating content

# Scrap / waste factor
SCRAP_FACTOR = 1.15                 # 15% material waste

# ---------------------------------------------------------------------------
# Structural mass model
# ---------------------------------------------------------------------------

# Skin thickness distribution (mm) along span
SKIN_THICKNESS_ROOT_MM = 8.0
SKIN_THICKNESS_TIP_MM = 2.5

# Structural fraction: fraction of enclosed area that is solid material
# (accounts for hollow blade sections with internal structure)
STRUCTURAL_FRACTION = 0.35

# Number of spanwise integration segments
NUM_SEGMENTS = 50


def _integrate_blade_mass(blade: BladeGeometry) -> float:
    """Compute blade mass by integrating along the span.

    Uses trapezoidal integration of cross-sectional area × density
    at each spanwise segment.

    Args:
        blade: BladeGeometry instance.

    Returns:
        Estimated blade mass in kg.
    """
    # Density in kg/m^3
    density_kg_m3 = 920.0
    density_g_cm3 = density_kg_m3 / 1000.0  # 0.92 g/cm^3

    total_mass_kg = 0.0
    segment_length = blade.blade_length_m / NUM_SEGMENTS

    for i in range(NUM_SEGMENTS):
        f0 = i / NUM_SEGMENTS
        f1 = (i + 1) / NUM_SEGMENTS

        c0 = blade.chord_at(f0)
        c1 = blade.chord_at(f1)

        t0 = SKIN_THICKNESS_ROOT_MM + f0 * (SKIN_THICKNESS_TIP_MM - SKIN_THICKNESS_ROOT_MM)
        t1 = SKIN_THICKNESS_ROOT_MM + f1 * (SKIN_THICKNESS_TIP_MM - SKIN_THICKNESS_ROOT_MM)

        # Cross-sectional area at each station (approximate as elliptical shell)
        # Area ~ pi * (chord/2) * (thickness*chord/2) - interior
        # Simplified: area ≈ structural_fraction * chord^2 * t/c
        area0 = STRUCTURAL_FRACTION * c0 * (MAX_THICKNESS_PCT * c0)
        area1 = STRUCTURAL_FRACTION * c1 * (MAX_THICKNESS_PCT * c1)

        # Average area for this segment (m^2)
        avg_area = (area0 + area1) / 2.0

        # Segment volume (m^3)
        seg_volume = avg_area * segment_length

        # Segment mass (kg)
        seg_mass = seg_volume * density_kg_m3

        total_mass_kg += seg_mass

    return total_mass_kg


# ---------------------------------------------------------------------------
# Cost model
# ---------------------------------------------------------------------------

@dataclass
class BladeCostBreakdown:
    """Detailed cost breakdown for a single blade.

    Attributes:
        blade_mass_kg: Estimated blade mass.
        material_cost_usd: Total raw material cost.
        labor_cost_usd: Direct labor cost.
        mold_tooling_usd: Amortized mold/tooling cost.
        transport_usd: Transport cost.
        installation_usd: Installation cost.
        overhead_usd: Overhead costs.
        total_cost_usd: Total blade cost.
    """
    blade_mass_kg: float
    material_cost_usd: float
    labor_cost_usd: float
    mold_tooling_usd: float
    transport_usd: float
    installation_usd: float
    overhead_usd: float
    total_cost_usd: float

    def summary(self, label: str = "Single Blade") -> str:
        """Multi-line cost breakdown."""
        lines = [
            f"Cost Breakdown: {label}",
            f"  {'Blade mass':30s} {self.blade_mass_kg:>8.2f} kg",
            f"  {'Material cost':30s} ${self.material_cost_usd:>8.2f}",
            f"  {'Labor cost':30s} ${self.labor_cost_usd:>8.2f}",
            f"  {'Mold/tooling':30s} ${self.mold_tooling_usd:>8.2f}",
            f"  {'Transport':30s} ${self.transport_usd:>8.2f}",
            f"  {'Installation':30s} ${self.installation_usd:>8.2f}",
            f"  {'Overhead':30s} ${self.overhead_usd:>8.2f}",
            f"  {'─' * 40}",
            f"  {'TOTAL':30s} ${self.total_cost_usd:>8.2f}",
        ]
        return "\n".join(lines)


def estimate_blade_cost(blade: BladeGeometry) -> BladeCostBreakdown:
    """Estimate the full cost of a single blade.

    Args:
        blade: BladeGeometry instance.

    Returns:
        BladeCostBreakdown with all cost components.
    """
    mass = _integrate_blade_mass(blade)

    # Material costs with scrap factor
    paper_mass = mass * PAPER_MASS_FRACTION * SCRAP_FACTOR
    binder_mass = mass * BINDER_MASS_FRACTION * SCRAP_FACTOR
    graphite_mass = mass * GRAPHITE_MASS_FRACTION * SCRAP_FACTOR

    material_cost = (
        paper_mass * PAPER_COST_USD_PER_KG
        + binder_mass * PVA_BINDER_COST_USD_PER_KG
        + graphite_mass * GRAPHITE_COST_USD_PER_KG
    )

    # Direct labor
    labor_cost = BLADE_PRODUCTION_HOURS * LABOR_COST_USD_PER_HOUR

    # Mold/tooling amortized
    mold_cost = MOLD_COST_USD

    # Transport
    transport = TRANSPORT_COST_USD

    # Installation
    installation = INSTALLATION_COST_USD

    # Overhead
    direct_costs = material_cost + labor_cost + mold_cost
    overhead = direct_costs * (OVERHEAD_PCT / 100.0)

    total = material_cost + labor_cost + mold_cost + transport + installation + overhead

    return BladeCostBreakdown(
        blade_mass_kg=round(mass, 2),
        material_cost_usd=round(material_cost, 2),
        labor_cost_usd=round(labor_cost, 2),
        mold_tooling_usd=round(mold_cost, 2),
        transport_usd=round(transport, 2),
        installation_usd=round(installation, 2),
        overhead_usd=round(overhead, 2),
        total_cost_usd=round(total, 2),
    )


def estimate_rotor_cost(blade: BladeGeometry) -> dict:
    """Estimate complete rotor cost (all blades + hub assembly).

    Args:
        blade: BladeGeometry instance.

    Returns:
        Dict with rotor cost breakdown.
    """
    per_blade = estimate_blade_cost(blade)

    # Hub & assembly costs
    hub_material_cost = 150.0      # Hub materials (wood/steel)
    hub_labor_cost = 4 * LABOR_COST_USD_PER_HOUR  # 4h assembly
    fasteners_cost = 25.0          # Bolts, brackets
    hub_total = hub_material_cost + hub_labor_cost + fasteners_cost

    blades_total = per_blade.total_cost_usd * blade.num_blades
    rotor_total = blades_total + hub_total

    return {
        "num_blades": blade.num_blades,
        "cost_per_blade_usd": per_blade.total_cost_usd,
        "blades_subtotal_usd": round(blades_total, 2),
        "hub_assembly_usd": round(hub_total, 2),
        "rotor_total_usd": round(rotor_total, 2),
        "blade_mass_kg": per_blade.blade_mass_kg,
        "rotor_mass_kg": round(per_blade.blade_mass_kg * blade.num_blades + 15.0, 2),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    blade = DEFAULT_BLADE

    print("=" * 70)
    print("  T043 — Blade Mass and Cost Estimation")
    print("=" * 70)
    print(f"  Blade: {blade.blade_length_m}m, {AIRFOIL}, {blade.num_blades} blades")
    print(f"  Material: Paper mache + graphite composite")
    print()

    # Per-blade cost
    cost = estimate_blade_cost(blade)
    print(cost.summary())
    print()

    # Rotor cost
    rotor = estimate_rotor_cost(blade)
    print("Rotor Assembly (all blades + hub):")
    print(f"  {'Number of blades':30s} {rotor['num_blades']:>8}")
    print(f"  {'Cost per blade':30s} ${rotor['cost_per_blade_usd']:>8.2f}")
    print(f"  {'Blades subtotal':30s} ${rotor['blades_subtotal_usd']:>8.2f}")
    print(f"  {'Hub assembly':30s} ${rotor['hub_assembly_usd']:>8.2f}")
    print(f"  {'─' * 40}")
    print(f"  {'ROTOR TOTAL':30s} ${rotor['rotor_total_usd']:>8.2f}")
    print(f"  {'Rotor mass':30s} {rotor['rotor_mass_kg']:>8.2f} kg")
    print(f"  {'Blade mass':30s} {rotor['blade_mass_kg']:>8.2f} kg")
    print()

    # Cost per kW (assuming 1.5 kW rated per IEC 61400-2 small turbine)
    rated_power_kw = 1.5
    cost_per_kw = rotor["rotor_total_usd"] / rated_power_kw
    print(f"  {'Rated power':30s} {rated_power_kw:>8.1f} kW")
    print(f"  {'Cost per kW (rotor only)':30s} ${cost_per_kw:>8.2f}/kW")
    print(f"  SC-004 target: < $3,000/kW")
    print(f"  SC-004 status: {'PASS' if cost_per_kw < 3000 else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
