"""ensaios/fluencia.py — fluência em regime secundário (lei de potência de Norton).

epsilon_ponto = A * sigma^n * exp(-Q/(R*T))
Refs: Norton (1929); Hertzberg (Deformation of Engineering Materials).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

R_GAS = 8.31446  # J/(mol.K)


@dataclass
class NortonParams:
    A: float          # pré-fator (1/(Pa^n.s))
    n: float          # expoente de tensão
    Q: float          # energia de ativação (J/mol)


def taxa_fluencia(sigma_pa: float, T_K: float, p: NortonParams) -> float:
    """Taxa de deformação por fluência (1/s)."""
    if sigma_pa <= 0 or T_K <= 0:
        return 0.0
    return p.A * (sigma_pa ** p.n) * math.exp(-p.Q / (R_GAS * T_K))


def deformacao_acumulada(sigma_pa: float, T_K: float, tempo_s: float, p: NortonParams) -> float:
    """Integra regime secundário: epsilon = taxa * t."""
    return taxa_fluencia(sigma_pa, T_K, p) * tempo_s
