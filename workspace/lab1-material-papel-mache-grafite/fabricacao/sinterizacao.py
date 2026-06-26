"""fabricacao/sinterizacao.py — densificação por sinterização (lei de Arrhenius simplificada).

Refs: Kang, S.-J.L. Sintering (2005).
"""
from __future__ import annotations

import math

R_GAS = 8.31446


def densificacao_relativa(t: float, T_K: float, D0: float, Q: float = 200e3,
                          K0: float = 1e-3, D_max: float = 1.0) -> float:
    """Fração da densidade teórica alcançada após tempo t (s) a T (K)."""
    if T_K <= 0:
        return D0
    k = K0 * math.exp(-Q / (R_GAS * T_K))
    D = D0 + (D_max - D0) * (1 - math.exp(-k * t))
    return min(D_max, max(D0, D))
