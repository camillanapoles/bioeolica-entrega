#!/usr/bin/env python3
"""
Structural Analysis Module — M³ Mechanics for Composite Wind Energy.

Per INSTRUCTIONS.md KDI domains:
  - Analysis of stresses, strains, displacements
  - Beam/shell theory for composite structures
  - Buckling analysis (Euler, plate, shell)
  - Vibration analysis (modal, natural frequencies)
  - Failure criteria (Tsai-Wu, Tsai-Hill, Maximum Stress)
  - Laminate theory (CLT — Classical Laminate Theory)

Usage:
    from structural_analysis import (
        BeamSection, CompositeLaminate, von_mises_stress,
        tsai_wu_failure, modal_analysis
    )
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  STRESS ANALYSIS
# ═══════════════════════════════════════════════════════════════

def von_mises_stress(sx: float, sy: float, sz: float = 0,
                     txy: float = 0, tyz: float = 0, tzx: float = 0) -> float:
    """Von Mises equivalent stress (MPa)."""
    return np.sqrt(0.5 * (
        (sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2 +
        6 * (txy**2 + tyz**2 + tzx**2)
    ))


def tresca_stress(s1: float, s3: float) -> float:
    """Tresca maximum shear stress criterion (MPa)."""
    return abs(s1 - s3)


def principal_stresses(sx: float, sy: float, txy: float) -> Tuple[float, float, float]:
    """Principal stresses and max shear from 2D stress state (MPa)."""
    avg = (sx + sy) / 2
    rad = np.sqrt(((sx - sy) / 2)**2 + txy**2)
    s1 = avg + rad
    s2 = avg - rad
    tau_max = rad
    return s1, s2, tau_max


# ═══════════════════════════════════════════════════════════════
#  BEAM SECTION — Composite Beam Analysis
# ═══════════════════════════════════════════════════════════════

@dataclass
class BeamSection:
    """Composite beam cross-section with arbitrary layup."""
    width_mm: float = 50.0
    height_mm: float = 10.0
    E_modulus_GPa: float = 10.0
    G_modulus_GPa: float = 4.0
    density_kgm3: float = 1200.0
    length_mm: float = 1000.0

    @property
    def I_m4(self) -> float:
        """Moment of inertia (m⁴) about neutral axis."""
        w = self.width_mm / 1000
        h = self.height_mm / 1000
        return w * h**3 / 12

    @property
    def A_m2(self) -> float:
        """Cross-sectional area (m²)."""
        return (self.width_mm * self.height_mm) / 1e6

    def bending_stress(self, moment_Nm: float, y_mm: float = 0) -> float:
        """Bending stress at distance y from neutral axis (MPa)."""
        y = y_mm / 1000 if y_mm else self.height_mm / 2000
        E = self.E_modulus_GPa * 1e9
        sigma = moment_Nm * y / self.I_m4
        return sigma / 1e6

    def deflection_point(self, force_N: float, position: str = "center") -> float:
        """Deflection under point load (mm)."""
        L = self.length_mm / 1000
        E = self.E_modulus_GPa * 1e9
        F = force_N
        if position == "center":
            delta = (F * L**3) / (48 * E * self.I_m4)
        elif position == "end":
            delta = (F * L**3) / (3 * E * self.I_m4)
        else:
            delta = (F * L**3) / (48 * E * self.I_m4)
        return delta * 1000  # convert to mm

    def natural_frequency_Hz(self, mode: int = 1, bc: str = "pinned-pinned") -> float:
        """First natural frequency (Hz) for beam vibration."""
        L = self.length_mm / 1000
        E = self.E_modulus_GPa * 1e9
        I = self.I_m4
        A = self.A_m2
        rho = self.density_kgm3
        m = A * rho

        beta_L = {1: np.pi, 2: 2 * np.pi, 3: 3 * np.pi}
        bl = beta_L.get(mode, np.pi)
        return (bl**2 / (2 * np.pi * L**2)) * np.sqrt(E * I / m)


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE LAMINATE — Classical Laminate Theory (CLT)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PlyProperties:
    """Single orthotropic ply properties."""
    E1_GPa: float      # Longitudinal modulus
    E2_GPa: float      # Transverse modulus
    G12_GPa: float     # Shear modulus
    nu12: float        # Major Poisson's ratio
    thickness_mm: float = 0.5
    orientation_deg: float = 0.0

    def Q_matrix(self) -> np.ndarray:
        """Reduced stiffness matrix [Q] for the ply (GPa)."""
        E1, E2 = self.E1_GPa, self.E2_GPa
        G12, nu12 = self.G12_GPa, self.nu12
        nu21 = nu12 * E2 / E1
        denom = 1 - nu12 * nu21
        Q = np.array([
            [E1/denom, nu12*E2/denom, 0],
            [nu12*E2/denom, E2/denom, 0],
            [0, 0, G12]
        ])
        return Q


class CompositeLaminate:
    """Classical Laminate Theory for multi-ply composites."""

    def __init__(self):
        self.plies: List[PlyProperties] = []

    def add_ply(self, ply: PlyProperties):
        self.plies.append(ply)

    def ABD_matrix(self) -> Dict[str, np.ndarray]:
        """Compute ABD (extensional-bending-coupling) matrix."""
        A = np.zeros((3, 3))
        B = np.zeros((3, 3))
        D = np.zeros((3, 3))
        z0 = -sum(p.thickness_mm for p in self.plies) / 2

        for ply in self.plies:
            theta = np.radians(ply.orientation_deg)
            c, s = np.cos(theta), np.sin(theta)

            # Transformation matrix T
            T = np.array([
                [c**2, s**2, -2*c*s],
                [s**2, c**2, 2*c*s],
                [c*s, -c*s, c**2 - s**2]
            ])

            Q = ply.Q_matrix()
            Qbar = T @ Q @ T.T  # Transformed stiffness
            t = ply.thickness_mm
            z1, z2 = z0, z0 + t

            A += Qbar * (z2 - z1)
            B += 0.5 * Qbar * (z2**2 - z1**2)
            D += (1/3) * Qbar * (z2**3 - z1**3)
            z0 = z2

        return {"A": A, "B": B, "D": D}


# ═══════════════════════════════════════════════════════════════
#  FAILURE CRITERIA
# ═══════════════════════════════════════════════════════════════

def tsai_wu_failure(sx: float, sy: float, txy: float,
                    Xt: float, Xc: float, Yt: float, Yc: float, S: float) -> Dict:
    """Tsai-Wu interactive failure criterion for orthotropic materials.

    Returns failure index (FI): FI < 1 = safe, FI >= 1 = failure.
    """
    F1 = 1/Xt - 1/Xc
    F2 = 1/Yt - 1/Yc
    F11 = 1/(Xt * Xc)
    F22 = 1/(Yt * Yc)
    F66 = 1/S**2
    F12 = -0.5 * np.sqrt(F11 * F22)

    FI = (F1*sx + F2*sy + F11*sx**2 + F22*sy**2 + F66*txy**2 + 2*F12*sx*sy)
    return {"failure_index": round(float(FI), 3), "status": "FAIL" if FI >= 1 else "SAFE"}


def tsai_hill_failure(sx: float, sy: float, txy: float,
                      X: float, Y: float, S: float) -> Dict:
    """Tsai-Hill failure criterion."""
    FI = (sx/X)**2 + (sy/Y)**2 - (sx*sy)/(X**2) + (txy/S)**2
    return {"failure_index": round(float(FI), 3), "status": "FAIL" if FI >= 1 else "SAFE"}


def max_stress_failure(sx: float, sy: float, txy: float,
                       Xt: float, Xc: float, Yt: float, Yc: float, S: float) -> Dict:
    """Maximum stress failure criterion."""
    ratios = {
        "sigma_11": sx / (Xt if sx >= 0 else Xc),
        "sigma_22": sy / (Yt if sy >= 0 else Yc),
        "tau_12": abs(txy) / S,
    }
    FI = max(ratios.values())
    return {"failure_index": round(float(FI), 3), "status": "FAIL" if FI >= 1 else "SAFE",
            "ratios": ratios}


# ═══════════════════════════════════════════════════════════════
#  SAFETY FACTOR & STRUCTURAL INTEGRITY
# ═══════════════════════════════════════════════════════════════

def safety_factor(yield_MPa: float, applied_MPa: float, method: str = "von_mises") -> float:
    """Compute factor of safety."""
    if applied_MPa <= 0:
        return float('inf')
    return round(yield_MPa / applied_MPa, 2)
