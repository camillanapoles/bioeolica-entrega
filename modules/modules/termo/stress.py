"""
Thermal stress computation: σ_th = -E·α·ΔT/(1-ν)
"""

from __future__ import annotations

import numpy as np


def thermal_stress(temps: np.ndarray, ref_temp: float,
                   E: float = 200e9, alpha: float = 1.2e-5,
                   nu: float = 0.3) -> np.ndarray:
    """
    Compute thermal stress from temperature field.

    Parameters
    ----------
    temps : np.ndarray
        Nodal temperatures (K).
    ref_temp : float
        Reference (stress-free) temperature (K).
    E : float
        Young's modulus (Pa).
    alpha : float
        Coefficient of thermal expansion (1/K).
    nu : float
        Poisson ratio.

    Returns
    -------
    sigma_th : np.ndarray
        Thermal stress per node (Pa), positive = tensile.
    """
    delta_t = temps - ref_temp
    sigma = -E * alpha * delta_t / (1.0 - nu)
    return sigma


def equivalent_thermal_force(sigma_th: np.ndarray, area: float = 1.0) -> float:
    """Compute equivalent nodal force from thermal stress."""
    return float(np.sum(np.abs(sigma_th)) * area / len(sigma_th))
