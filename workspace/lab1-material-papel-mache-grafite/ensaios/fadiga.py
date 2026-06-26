"""ensaios/fadiga.py — fadiga virtual: Basquin (alta ciclagem) + Coffin-Manson (baixa ciclagem)."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class BasquinParams:
    sigma_f_linha: float   # coeficiente de resistência à fadiga (Pa)
    b: float               # expoente de Basquin (negativo, ~ -0.05 a -0.12)


def ciclos_para_falha_basquin(delta_sigma: float, p: BasquinParams) -> float:
    """Nf = (sigma_f'/delta_sigma)^(1/b)."""
    if delta_sigma <= 0 or p.sigma_f_linha <= 0:
        return 0.0
    razao = delta_sigma / p.sigma_f_linha
    if razao >= 1:
        return 0.5  # falha no primeiro ciclo (acima da resistência)
    return razao ** (1.0 / p.b)


@dataclass
class CoffinMansonParams:
    epsilon_f_linha: float  # ductilidade em fadiga (~0.2-1.0)
    c: float                # expoente de Coffin-Manson (~ -0.5 a -0.7)


def ciclos_para_falha_cm(delta_epsilon_plastico: float, p: CoffinMansonParams) -> float:
    """Nf = (epsilon_f'/delta_epsilon_p)^(1/c)."""
    if delta_epsilon_plastico <= 0:
        return float("inf")
    razao = delta_epsilon_plastico / p.epsilon_f_linha
    if razao >= 1:
        return 0.5
    return razao ** (1.0 / p.c)
