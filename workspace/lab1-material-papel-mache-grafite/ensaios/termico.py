"""ensaios/termico.py — condutividade efetiva (regra de misturas) + expansão térmica."""
from __future__ import annotations

from core.constants import get

_HASHIN_DIM = get("ensaios.termico.hashin_dim")  # dimensionalidade (n=3 esférico)


def condutividade_efetiva(k_m: float, k_f: float, Vf: float) -> float:
    """Born superior para condutividade térmica."""
    return k_m * (1 - Vf) + k_f * Vf


def cte_efetiva(alpha_m: float, alpha_f: float, Vf: float) -> float:
    """Coeficiente de expansão térmica (regra de misturas)."""
    return alpha_m * (1 - Vf) + alpha_f * Vf


def fluxo_calor_q(k: float, dT_dx: float) -> float:
    """Lei de Fourier: q = -k * dT/dx (magnitude)."""
    return abs(k * dT_dx)


def condutividade_efetiva_reuss(k_m: float, k_f: float, Vf: float) -> float:
    """Born inferior (média harmônica) — adequado para particulados desalinhados.

    Refs: Carson et al. (2005) Int. J. Heat Mass Transfer 48:2150-2158.
    Para compósito papel-machê+grafite (particulados), o borne inferior é
    tipicamente mais representativo que o superior (Voigt).
    """
    if k_m <= 0 or k_f <= 0:
        return 0.0
    return 1.0 / ((1 - Vf) / k_m + Vf / k_f)


def condutividade_efetiva_hashin_shtrikman(k_m: float, k_f: float, Vf: float) -> float:
    """Aproximação Hashin-Shtrikman lower bound — compósito particulado isotrópico."""
    if k_m <= 0 or k_f <= 0:
        return 0.0
    k_low = min(k_m, k_f)
    k_high = max(k_m, k_f)
    # HS lower bound
    return k_low + Vf / (1.0 / (k_high - k_low) + (1 - Vf) / (_HASHIN_DIM * k_low))
