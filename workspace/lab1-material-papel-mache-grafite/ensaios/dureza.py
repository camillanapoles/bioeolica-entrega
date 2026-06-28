"""ensaios/dureza.py — estimativa Shore D via correlação empírica com módulo.

Correlação (Ashby; Briscoe & Sebastian 1996): ShoreD = a*log10(E[MPa]) + b.
Calibração: a=12, b=38 -> E=3.4GPa dá ShoreD~80 (polímero rígido típico).
Refs: ASTM D2240; Ashby, M.F. Materials Selection in Mechanical Design.
"""
from __future__ import annotations

import math

from core.constants import get

# Constantes de domínio vindas do schema unificado (P$1: zero hardcoded)
_PA_MPA = get("ensaios.dureza.pa_para_mpa")
_SHORE_D_MAX = get("ensaios.dureza.shore_d_max")
_SHORE_D_MIN = get("ensaios.dureza.shore_d_min")
_BRINELL_COEF = get("ensaios.dureza.brinell_coef")
_BRINELL_ESCALA = get("ensaios.dureza.brinell_escala")


def shore_d_from_young(E_pa: float,
                       a: float = get("ensaios.dureza.shore_d_coef_a"),
                       b: float = get("ensaios.dureza.shore_d_intercepto_b")) -> float:
    """Estima dureza Shore D a partir do módulo de Young (Pa)."""
    if E_pa <= 0:
        return 0.0
    E_mpa = E_pa / _PA_MPA
    sd = a * math.log10(E_mpa) + b
    return max(_SHORE_D_MIN, min(_SHORE_D_MAX, sd))


def brinell_from_young(E_pa: float, sigma_y_pa: float) -> float:
    """Proxy Brinell (HB) proporcional: HB ~ 3*sigma_y/E*100."""
    if E_pa <= 0:
        return 0.0
    return _BRINELL_COEF * sigma_y_pa / E_pa * _BRINELL_ESCALA
