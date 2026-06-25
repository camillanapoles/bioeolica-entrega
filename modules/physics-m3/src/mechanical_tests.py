#!/usr/bin/env python3
"""
Mechanical Test Emulators — Composite Material Characterization.

Emulates standard mechanical tests for composite material characterization:
  - Flexão (3-point bending): ASTM D790
  - Tração (tensile): ASTM D3039
  - Compressão (compression): ASTM D3410 / D6641
  - Flambagem (buckling): Euler critical load
  - Choque (impact): Charpy/Izod, drop-weight
  - Dureza (hardness): Shore D (polymers), Rockwell
  - Atrito (friction): Coefficient of friction

Each test accepts material properties and geometry, returns simulated
stress-strain curves, failure points, and key metrics.

Usage:
    from mechanical_tests import (
        flexure_test, tensile_test, compression_test,
        buckling_test, impact_test, hardness_test, friction_test
    )

    # 3-point bending of paper mache composite
    result = flexure_test(
        E=2.5, length=100, width=25, thickness=5, span_ratio=16
    )
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  FLEXÃO — 3-Point Bending (ASTM D790)
# ═══════════════════════════════════════════════════════════════

def flexure_test(
    E_GPa: float,           # Elastic modulus (GPa)
    length_mm: float,       # Support span (mm)
    width_mm: float,        # Specimen width (mm)
    thickness_mm: float,    # Specimen thickness (mm)
    strength_MPa: float = 30.0,  # Flexural strength (MPa)
    n_points: int = 100,    # Stress-strain curve resolution
    span_ratio: int = 16,   # Span-to-thickness ratio (ASTM D790)
) -> Dict:
    """Simulate 3-point bending test."""
    L = length_mm / 1000
    w = width_mm / 1000
    t = thickness_mm / 1000
    E = E_GPa * 1e9
    sigma_max = strength_MPa * 1e6

    I = w * t**3 / 12  # Moment of inertia
    max_force = (2 * sigma_max * I) / (t / 2 * L / 2)
    max_displacement = (max_force * L**3) / (48 * E * I)

    displacements = np.linspace(0, max_displacement * 1.2, n_points)
    forces = np.minimum(
        (48 * E * I * displacements) / L**3,
        max_force * np.exp(-10 * np.maximum(0, displacements - max_displacement) / max_displacement)
    )

    stress = (3 * forces * L) / (2 * w * t**2)
    strain = (6 * t * displacements) / L**2

    return {
        "test": "3-point bending (ASTM D790)",
        "max_force_N": round(float(max_force), 1),
        "flexural_strength_MPa": round(strength_MPa, 1),
        "max_displacement_mm": round(float(max_displacement * 1000), 2),
        "flexural_modulus_GPa": round(E_GPa, 2),
        "stress_strain": {
            "stress_MPa": [round(s / 1e6, 2) for s in stress[::10]],
            "strain_pct": [round(e * 100, 3) for e in strain[::10]],
        },
    }


# ═══════════════════════════════════════════════════════════════
#  TRAÇÃO — Tensile Test (ASTM D3039)
# ═══════════════════════════════════════════════════════════════

def tensile_test(
    E_GPa: float,
    width_mm: float,
    thickness_mm: float,
    tensile_strength_MPa: float,
    elongation_pct: float = 2.0,
    n_points: int = 100,
) -> Dict:
    """Simulate tensile test."""
    if tensile_strength_MPa <= 0:
        return {
            "test": "Tensile (ASTM D3039)", "max_force_N": 0.0,
            "tensile_strength_MPa": 0.0, "elongation_pct": 0.0,
            "modulus_GPa": round(E_GPa, 2),
            "stress_strain": {"stress_MPa": [], "strain_pct": []},
        }
    A = (width_mm / 1000) * (thickness_mm / 1000)
    E = E_GPa * 1e9
    sigma_max = tensile_strength_MPa * 1e6
    epsilon_max = elongation_pct / 100

    strain = np.linspace(0, epsilon_max * 1.3, n_points)
    stress = E * strain
    stress[strain > epsilon_max] = stress[strain > epsilon_max] * np.exp(
        -20 * (strain[strain > epsilon_max] - epsilon_max)
    )
    force = stress * A

    return {
        "test": "Tensile (ASTM D3039)",
        "max_force_N": round(float(np.max(force)), 1),
        "tensile_strength_MPa": round(float(np.max(stress) / 1e6), 1),
        "elongation_pct": round(elongation_pct, 1),
        "modulus_GPa": round(E_GPa, 2),
        "stress_strain": {
            "stress_MPa": [round(s / 1e6, 2) for s in stress[::10]],
            "strain_pct": [round(e * 100, 3) for e in strain[::10]],
        },
    }


# ═══════════════════════════════════════════════════════════════
#  COMPRESSÃO — Compression Test (ASTM D3410)
# ═══════════════════════════════════════════════════════════════

def compression_test(
    E_GPa: float,
    width_mm: float,
    thickness_mm: float,
    compressive_strength_MPa: float,
    n_points: int = 100,
) -> Dict:
    """Simulate compression test."""
    A = (width_mm / 1000) * (thickness_mm / 1000)
    E = E_GPa * 1e9
    sigma_max = compressive_strength_MPa * 1e6

    strain = np.abs(np.linspace(0, 0.05, n_points))
    stress = E * strain
    failure_idx = np.where(stress >= sigma_max)[0]
    if len(failure_idx) > 0:
        stress[failure_idx[0]:] = sigma_max * np.exp(
            -15 * (strain[failure_idx[0]:] - strain[failure_idx[0]])
        )
    force = stress * A

    return {
        "test": "Compression (ASTM D3410)",
        "max_force_N": round(float(np.max(force)), 1),
        "compressive_strength_MPa": round(float(np.max(stress) / 1e6), 1),
        "modulus_GPa": round(E_GPa, 2),
        "stress_strain": {
            "stress_MPa": [round(s / 1e6, 2) for s in stress[::10]],
            "strain_pct": [round(e * 100, 3) for e in strain[::10]],
        },
    }


# ═══════════════════════════════════════════════════════════════
#  FLAMBAGEM — Euler Buckling
# ═══════════════════════════════════════════════════════════════

def buckling_test(
    E_GPa: float,
    length_mm: float,
    width_mm: float,
    thickness_mm: float,
    end_condition: str = "pinned-pinned",
) -> Dict:
    """Calculate Euler critical buckling load."""
    E = E_GPa * 1e9
    L = length_mm / 1000
    w = width_mm / 1000
    t = thickness_mm / 1000

    # Moment of inertia (weak axis)
    I = min(w * t**3 / 12, t * w**3 / 12)

    # Effective length factor K
    K_factors = {
        "pinned-pinned": 1.0,
        "fixed-fixed": 0.5,
        "fixed-pinned": 0.7,
        "fixed-free": 2.0,
    }
    K = K_factors.get(end_condition, 1.0)

    P_cr = (np.pi**2 * E * I) / ((K * L)**2)
    sigma_cr = P_cr / (w * t)

    return {
        "test": f"Euler buckling ({end_condition})",
        "critical_load_N": round(float(P_cr), 1),
        "critical_stress_MPa": round(float(sigma_cr / 1e6), 2),
        "slenderness_ratio": round(float(K * L / np.sqrt(I / (w * t))), 1),
    }


# ═══════════════════════════════════════════════════════════════
#  CHOQUE — Charpy Impact
# ═══════════════════════════════════════════════════════════════

def impact_test(
    impact_energy_J: float = 5.0,
    cross_section_mm2: float = 100.0,
    material_toughness_kJm2: float = 15.0,
) -> Dict:
    """Simulate Charpy/Izod impact test."""
    A = cross_section_mm2 / 1e6
    absorbed_energy = min(impact_energy_J, material_toughness_kJm2 * 1000 * A)
    toughness = absorbed_energy / A

    return {
        "test": "Charpy impact",
        "impact_energy_J": impact_energy_J,
        "absorbed_energy_J": round(float(absorbed_energy), 2),
        "toughness_kJm2": round(float(toughness / 1000), 1),
        "failure": "complete" if absorbed_energy >= impact_energy_J * 0.5 else "partial",
    }


# ═══════════════════════════════════════════════════════════════
#  DUREZA — Hardness (Shore D)
# ═══════════════════════════════════════════════════════════════

def hardness_test(
    E_GPa: float,
    yield_strength_MPa: float,
    method: str = "shore_d",
) -> Dict:
    """Estimate hardness from elastic and plastic properties."""
    E = E_GPa * 1e9
    sy = yield_strength_MPa * 1e6

    if method == "shore_d":
        # Correlation: Shore D ~ 100 * (1 - exp(-0.025 * E))
        shore_d = 100 * (1 - np.exp(-0.025 * E_GPa * 1000))
        return {
            "test": "Hardness (Shore D)",
            "shore_d": round(float(shore_d), 1),
            "indentation_modulus_GPa": round(E_GPa * 0.8, 2),
        }
    elif method == "rockwell_m":
        rockwell_m = 120 - 30 * np.log10(E_GPa * 1000)
        return {
            "test": "Hardness (Rockwell M)",
            "rockwell_m": round(float(rockwell_m), 1),
        }
    else:
        return {"test": "Unknown method", "error": f"No model for {method}"}


# ═══════════════════════════════════════════════════════════════
#  ATRITO — Coefficient of Friction
# ═══════════════════════════════════════════════════════════════

def friction_test(
    normal_force_N: float = 10.0,
    surface_roughness_um: float = 1.0,
    material_pair: str = "composite-steel",
    lubrication: str = "dry",
) -> Dict:
    """Estimate coefficient of friction for composite-on-material pairs."""
    friction_coeffs = {
        "composite-steel": {"dry": 0.35, "wet": 0.25, "lubricated": 0.12},
        "composite-composite": {"dry": 0.45, "wet": 0.30, "lubricated": 0.15},
        "composite-concrete": {"dry": 0.60, "wet": 0.50, "lubricated": 0.30},
    }

    mu = friction_coeffs.get(material_pair, friction_coeffs["composite-steel"])
    mu_val = mu.get(lubrication, mu["dry"])

    friction_force_N = mu_val * normal_force_N

    return {
        "test": f"Friction ({material_pair}, {lubrication})",
        "coefficient_friction": mu_val,
        "friction_force_N": round(friction_force_N, 2),
        "surface_roughness_um": surface_roughness_um,
    }


def run_all_tests(E_GPa: float, strength_MPa: float, **geom) -> Dict:
    """Run all mechanical tests on a single material specification.

    Args:
        E_GPa: Elastic modulus (GPa)
        strength_MPa: Estimated strength (MPa)
        geom: Geometry dict with keys: length_mm, width_mm, thickness_mm

    Returns:
        Dict with all test results.
    """
    length = geom.get("length_mm", 100)
    width = geom.get("width_mm", 25)
    thickness = geom.get("thickness_mm", 5)

    return {
        "material": {
            "E_GPa": E_GPa,
            "strength_MPa": strength_MPa,
            "geometry_mm": {"length": length, "width": width, "thickness": thickness},
        },
        "flexao": flexure_test(E_GPa, length, width, thickness, strength_MPa),
        "tracao": tensile_test(E_GPa, width, thickness, strength_MPa),
        "compressao": compression_test(E_GPa, width, thickness, strength_MPa),
        "flambagem": buckling_test(E_GPa, length, width, thickness),
        "choque": impact_test(cross_section_mm2=width * thickness),
        "dureza": hardness_test(E_GPa, strength_MPa),
        "atrito": friction_test(normal_force_N=strength_MPa * (width * thickness) / 1e6),
    }
