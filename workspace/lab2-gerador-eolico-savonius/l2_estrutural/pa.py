"""estrutural/pa.py — dimensionamento de pá em compósito (Lab1 material).

Usa propriedades do compósito papel-machê+grafite (Lab1) para estimar massa,
inércia, tensão de flap e fator de segurança.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaCompuesto:
    comprimento_m: float
    corda_m: float
    espessura_m: float
    densidade_kg_m3: float
    resistencia_pa: float        # tensão de ruptura


def massa_pa(pa: PaCompuesto) -> float:
    return pa.densidade_kg_m3 * (pa.comprimento_m * pa.corda_m * pa.espessura_m)


def tensao_flap(pa: PaCompuesto, forca_n: float) -> float:
    """σ ~ M*c/I; I = b*h^3/12; M = F*L/4 (carga central)."""
    I = pa.corda_m * pa.espessura_m ** 3 / 12.0
    M = forca_n * pa.comprimento_m / 4.0
    c = pa.espessura_m / 2.0
    if I <= 0:
        return float("inf")
    return M * c / I


def fator_seguranca(pa: PaCompuesto, forca_n: float) -> float:
    sigma = tensao_flap(pa, forca_n)
    if sigma <= 0:
        return float("inf")
    return pa.resistencia_pa / sigma
