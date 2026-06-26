"""fabricacao/extrusao.py — extrusão: vazão por equação de Hagen-Poiseuille."""
from __future__ import annotations

import math


def vazao_laminar(dP: float, mu: float, L: float, r: float) -> float:
    """Q = pi*r^4*dP / (8*mu*L)."""
    if mu <= 0 or L <= 0:
        return 0.0
    return math.pi * r**4 * dP / (8 * mu * L)


def tensao_cisalhamento_parede(dP: float, r: float, L: float) -> float:
    """tau_w = dP*r/(2*L)."""
    if L <= 0:
        return 0.0
    return dP * r / (2 * L)
