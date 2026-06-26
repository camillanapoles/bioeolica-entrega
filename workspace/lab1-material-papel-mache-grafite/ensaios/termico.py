"""ensaios/termico.py — condutividade efetiva (regra de misturas) + expansão térmica."""
from __future__ import annotations


def condutividade_efetiva(k_m: float, k_f: float, Vf: float) -> float:
    """Born superior para condutividade térmica."""
    return k_m * (1 - Vf) + k_f * Vf


def cte_efetiva(alpha_m: float, alpha_f: float, Vf: float) -> float:
    """Coeficiente de expansão térmica (regra de misturas)."""
    return alpha_m * (1 - Vf) + alpha_f * Vf


def fluxo_calor_q(k: float, dT_dx: float) -> float:
    """Lei de Fourier: q = -k * dT/dx (magnitude)."""
    return abs(k * dT_dx)
