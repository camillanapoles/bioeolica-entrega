"""ensaios/tracao.py — tração virtual: regra de misturas (Voigt/Reuss) + Halpin-Tsai.

Refs VVV:
- Halpin, J.C.; Kardos, J.L. (1976) Polym. Eng. Sci. 16(5):344-352.
- Callister & Rethwisch, Materials Science and Engineering, cap. 16 (Composites).
"""
from __future__ import annotations

from dataclasses import dataclass

from core.constants import get


@dataclass
class MisturaInputs:
    E_matriz: float       # Pa
    E_carga: float        # Pa
    V_carga: float        # fração volumétrica [0,1]


def regra_voigt(x: MisturaInputs) -> float:
    """Born superior (iso-deformação): E = Em*(1-Vf) + Ef*Vf."""
    return x.E_matriz * (1 - x.V_carga) + x.E_carga * x.V_carga


def regra_reuss(x: MisturaInputs) -> float:
    """Born inferior (iso-tensão): 1/E = (1-Vf)/Em + Vf/Ef."""
    if x.E_matriz == 0 or x.E_carga == 0:
        return 0.0
    return 1.0 / ((1 - x.V_carga) / x.E_matriz + x.V_carga / x.E_carga)


def halpin_tsai(x: MisturaInputs, xi: float = get("ensaios.tracao.xi_halpin_tsai")) -> float:
    """Halpin-Tsai: E = Em*(1 + xi*eta*Vf)/(1 - eta*Vf);  eta=(Ef/Em - 1)/(Ef/Em + xi)."""
    if x.E_matriz == 0:
        return 0.0
    r = x.E_carga / x.E_matriz
    eta = (r - 1) / (r + xi)
    num = 1 + xi * eta * x.V_carga
    den = 1 - eta * x.V_carga
    if den <= 0:
        return float("inf")
    return x.E_matriz * (num / den)


def tensao_ruptura_mistura(sigma_m: float, sigma_f: float, Vf: float) -> float:
    """Estimativa simples de tensão de ruptura por regra de misturas."""
    return sigma_m * (1 - Vf) + sigma_f * Vf


def densidade_composita(rho_m: float, rho_f: float, Vf: float) -> float:
    """Densidade do compósito: rho = rho_m*(1-Vf) + rho_f*Vf."""
    return rho_m * (1 - Vf) + rho_f * Vf
