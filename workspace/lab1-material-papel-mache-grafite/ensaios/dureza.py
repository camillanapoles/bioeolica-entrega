"""ensaios/dureza.py — estimativa Shore D via correlação empírica com módulo.

Correlação (Ashby; Briscoe & Sebastian 1996): ShoreD = a*log10(E[MPa]) + b.
Calibração: a=12, b=38 -> E=3.4GPa dá ShoreD~80 (polímero rígido típico).
Refs: ASTM D2240; Ashby, M.F. Materials Selection in Mechanical Design.
"""
from __future__ import annotations

import math


def shore_d_from_young(E_pa: float, a: float = 12.0, b: float = 38.0) -> float:
    """Estima dureza Shore D a partir do módulo de Young (Pa)."""
    if E_pa <= 0:
        return 0.0
    E_mpa = E_pa / 1e6
    sd = a * math.log10(E_mpa) + b
    return max(0.0, min(100.0, sd))


def brinell_from_young(E_pa: float, sigma_y_pa: float) -> float:
    """Proxy Brinell (HB) proporcional: HB ~ 3*sigma_y/E*100."""
    if E_pa <= 0:
        return 0.0
    return 3.0 * sigma_y_pa / E_pa * 100.0
