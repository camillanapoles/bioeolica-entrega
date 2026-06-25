#!/usr/bin/env python3
"""
Fluid Dynamics Module — CFD & Aerodynamics for Wind Energy.

Per INSTRUCTIONS.md KDI: fluid_dynamics domain.
  - Aerodynamics of wind turbine blades (BEM theory)
  - Drag/lift coefficient estimation
  - Boundary layer analysis
  - Reynolds number, Mach number
  - Wind flow modeling (atmospheric boundary layer)
  - Basic CFD utilities (finite difference)

Usage:
    from fluid_dynamics import (
        wind_profile, bem_theory, lift_drag_coefficients,
        reynolds_number, boundary_layer_thickness
    )
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════
#  ATMOSPHERIC BOUNDARY LAYER
# ═══════════════════════════════════════════════════════════════

def wind_profile(z_m: float, v_ref_ms: float, z_ref_m: float = 10.0,
                 alpha: float = 0.14, terrain: str = "open") -> float:
    """Wind speed at height z using power law.

    Terrain types and alpha values:
      - open: 0.14 (open water, flat terrain)
      - suburban: 0.22 (suburban, woodland)
      - urban: 0.33 (city center, tall buildings)
    """
    alpha_map = {"open": 0.14, "suburban": 0.22, "urban": 0.33}
    a = alpha_map.get(terrain, alpha)
    return v_ref_ms * (z_m / z_ref_m) ** a


def atmospheric_boundary_layer_height(terrain: str = "open") -> float:
    """Estimate ABL height (m) by terrain type."""
    heights = {"open": 300, "suburban": 400, "urban": 500}
    return heights.get(terrain, 300)


# ═══════════════════════════════════════════════════════════════
#  REYNOLDS NUMBER & FLOW REGIME
# ═══════════════════════════════════════════════════════════════

def reynolds_number(velocity_ms: float, chord_m: float,
                    nu: float = 1.516e-5) -> float:
    """Reynolds number for airfoil/blade flow."""
    return velocity_ms * chord_m / nu


def flow_regime(Re: float) -> str:
    """Classify flow regime by Reynolds number."""
    if Re < 2000:
        return "laminar"
    elif Re < 40000:
        return "transitional"
    else:
        return "turbulent"


# ═══════════════════════════════════════════════════════════════
#  BOUNDARY LAYER
# ═══════════════════════════════════════════════════════════════

def boundary_layer_thickness(x_m: float, Re_x: float) -> Dict:
    """Estimate boundary layer thicknesses."""
    return {
        "laminar_delta_mm": round(5.0 * x_m / np.sqrt(Re_x) * 1000, 2),
        "turbulent_delta_mm": round(0.37 * x_m / (Re_x**0.2) * 1000, 2),
        "displacement_thickness_mm": round(1.72 * x_m / np.sqrt(Re_x) * 1000, 2),
        "momentum_thickness_mm": round(0.664 * x_m / np.sqrt(Re_x) * 1000, 2),
    }


# ═══════════════════════════════════════════════════════════════
#  AIRFOIL AERODYNAMICS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Airfoil:
    """Simple airfoil aerodynamics model."""
    name: str = "NACA0012"
    chord_m: float = 0.3
    thickness_ratio: float = 0.12

    def cl_alpha(self, alpha_deg: float, Re: float = 1e5) -> float:
        """Lift coefficient at angle of attack (deg)."""
        alpha = np.radians(alpha_deg)

        # Thin airfoil theory: Cl = 2*pi*alpha (linear range)
        cl_linear = 2 * np.pi * alpha

        # Stall model: Cl drops beyond stall angle
        alpha_stall_deg = 10 + 5 * np.sqrt(self.thickness_ratio / 0.12)  # thickness effect
        alpha_stall = np.radians(alpha_stall_deg)
        if abs(alpha_deg) > alpha_stall_deg:
            # Post-stall: exponential lift reduction
            cl = cl_linear * np.exp(-3 * (abs(alpha_deg) - alpha_stall_deg) / 10)
        else:
            cl = cl_linear

        return cl

    def cd_alpha(self, alpha_deg: float, Re: float = 1e5) -> float:
        """Drag coefficient."""
        alpha = np.radians(alpha_deg)
        # Profile drag + induced drag
        cd0 = 0.02 / np.sqrt(Re / 1e5)  # skin friction
        cdi = 0.1 * alpha**2  # induced drag
        return cd0 + cdi


# ═══════════════════════════════════════════════════════════════
#  BEM THEORY — Blade Element Momentum (simplified)
# ═══════════════════════════════════════════════════════════════

def bem_theory(v_wind_ms: float, rpm: float, R_m: float,
               B: int = 3, r_R_ratio: float = 0.75) -> Dict:
    """Simplified BEM for a single blade element."""
    if v_wind_ms <= 0 or rpm <= 0:
        return {
            "TSR": 0, "v_rel_ms": 0, "phi_deg": 0,
            "thrust_N": 0, "torque_Nm": 0, "power_W": 0,
            "Ct": 0, "Cq": 0,
        }
    omega = rpm * 2 * np.pi / 60  # rad/s
    r = r_R_ratio * R_m
    v_tip = omega * R_m
    TSR = v_tip / v_wind_ms

    # Local flow angles
    v_rel = np.sqrt(v_wind_ms**2 + (omega * r)**2)
    phi = np.arctan2(v_wind_ms, omega * r)

    # Thrust and torque coefficients (simplified)
    Ct = 0.8 / (1 + 0.5 / TSR)
    Cq = 0.04 * TSR / (1 + TSR)

    dT = 0.5 * 1.225 * v_rel**2 * Ct * (2 * np.pi * r / B)
    dQ = 0.5 * 1.225 * v_rel**2 * Cq * (2 * np.pi * r / B) * r
    dP = dQ * omega

    return {
        "TSR": round(TSR, 2),
        "v_rel_ms": round(v_rel, 2),
        "phi_deg": round(np.degrees(phi), 1),
        "thrust_N": round(dT, 1),
        "torque_Nm": round(dQ, 1),
        "power_W": round(dP, 1),
        "Ct": round(Ct, 3),
        "Cq": round(Cq, 4),
    }


# ═══════════════════════════════════════════════════════════════
#  WIND TURBINE POWER
# ═══════════════════════════════════════════════════════════════

def betz_limit() -> float:
    """Betz limit: max 59.3% of wind energy can be extracted."""
    return 16/27


def wind_power_density(v_ms: float, rho: float = 1.225) -> float:
    """Wind power per unit area (W/m²)."""
    return 0.5 * rho * v_ms**3


def turbine_power(v_wind_ms: float, R_m: float, Cp: float = 0.40,
                  rho: float = 1.225) -> Dict:
    """Wind turbine power output."""
    A = np.pi * R_m**2
    P_wind = 0.5 * rho * A * v_wind_ms**3
    P_out = Cp * P_wind
    return {
        "rotor_area_m2": round(A, 1),
        "wind_power_W": round(P_wind, 1),
        "power_W": round(P_out, 1),
        "Cp": Cp,
        "betz_efficiency_pct": round(Cp / (16/27) * 100, 1),
    }
