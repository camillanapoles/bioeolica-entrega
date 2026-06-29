"""fabricacao/ultrassom.py — dispersão de grafite por ultrassom.

Aproximação: energia por unidade de volume e índice de dispersão (0-1).
Refs: Hielscher, T. Ultrasonic Production of Nano-Size Dispersions (2005).
"""
from __future__ import annotations

import math

from core.constants import get


def energia_volumetrica(potencia_w: float, volume_m3: float, tempo_s: float) -> float:
    """E = P*t/V (J/m^3)."""
    if volume_m3 <= 0:
        return 0.0
    return potencia_w * tempo_s / volume_m3


def indice_dispersao(energia_J_m3: float,
                     E_ref_J_m3: float = get("fabricacao.ultrassom.energia_ref_J_m3")) -> float:
    """Índice em [0,1] saturado por energia de referência."""
    if E_ref_J_m3 <= 0:
        return 0.0
    return 1.0 - math.exp(-energia_J_m3 / E_ref_J_m3)
