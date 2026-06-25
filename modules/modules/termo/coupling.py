"""
Thermal-structural coupling bridge.

Maps thermal results (temperature field, thermal stress)
to structural analysis loads.
"""

from __future__ import annotations

import numpy as np


def thermal_to_structural_loads(temps: np.ndarray, ref_temp: float,
                                 E: float = 200e9, alpha: float = 1.2e-5,
                                 nu: float = 0.3) -> np.ndarray:
    """
    Convert temperature field to equivalent structural nodal forces (1D estimate).

    For full 3D coupling, this feeds into the structural FEM solver
    as thermal load vector.
    """
    from .stress import thermal_stress
    sigma = thermal_stress(temps, ref_temp, E, alpha, nu)
    # Equivalent nodal force per DOF (simplified)
    forces = np.repeat(sigma, 2 if len(sigma.shape) == 1 else 3) * 0.1
    return forces
