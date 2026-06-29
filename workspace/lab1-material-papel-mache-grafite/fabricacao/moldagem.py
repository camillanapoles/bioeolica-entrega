"""fabricacao/moldagem.py — moldagem por prensa (pressão × tempo × temperatura).

Estima grau de cura/consolidação por modelo cinético de 1a ordem:
    dX/dt = k(T)*(1-X);  k(T) = A*exp(-Ea/RT);  X = 1 - exp(-k*t)
Refs: Kamal & Sourour, Polym. Eng. Sci. 13 (1973).
"""
from __future__ import annotations

import math

from core.constants import get

R_GAS = get("fisica.R_GAS")  # schema unificado (P$1)


def grau_cura(tempo_s: float, T_K: float, A: float = 1e6, Ea: float = 60e3) -> float:
    """Grau de cura X em [0,1] após tempo_s a T_K."""
    if T_K <= 0:
        return 0.0
    k = A * math.exp(-Ea / (R_GAS * T_K))
    return 1.0 - math.exp(-k * tempo_s)


def pressao_recomendada(densidade_alvo_kg_m3: float, densidade_solida_kg_m3: float) -> float:
    """Pressão mínima proporcional ao nível de consolidação (proxy)."""
    if densidade_solida_kg_m3 <= 0:
        return 0.0
    consolidacao = densidade_alvo_kg_m3 / densidade_solida_kg_m3
    return max(0.0, (consolidacao - 0.5) * 2.0) * 5e5  # até ~0.5 MPa
