"""aerodinamica/savonius.py — modelo de potência de turbina Savonius.

Modelos semi-empíricos:
- Limite de Betz: P = 0.5 * rho * A * v^3 * Cp; Cp_max <= 16/27 ~ 0.593
- Savonius: Cp(lambda) ~ Cp_max * exp(-((lambda-lambda_opt)/sigma)^2)
Refs: Savonius (1931); Wilson & Lissaman (1974); IEC 61400-2 (small wind).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

BETZ = 16.0 / 27.0


def potencia_disponivel(rho_ar: float, area_varrida_m2: float, v_mps: float) -> float:
    """P = 0.5 * rho * A * v^3."""
    return 0.5 * rho_ar * area_varrida_m2 * v_mps ** 3


@dataclass
class SavoniusCurve:
    Cp_max: float = 0.25      # Savonius típico 0.20-0.30
    lambda_opt: float = 0.8   # TSR ótimo Savonius (~0.5-1.0)
    sigma: float = 0.35       # largura da curva (dispersão)


def coeficiente_potencia(tsr: float, curve: SavoniusCurve) -> float:
    """Cp(lambda) Gaussiano, pico em lambda_opt, limitado por Betz."""
    if tsr <= 0:
        return 0.0
    cp = curve.Cp_max * math.exp(-((tsr - curve.lambda_opt) / curve.sigma) ** 2)
    return max(0.0, min(BETZ, cp))


def potencia_turbina(rho_ar: float, area_varrida_m2: float, v_mps: float,
                     tsr: float, curve: SavoniusCurve | None = None) -> float:
    """P = P_disponivel * Cp(lambda)."""
    curve = curve or SavoniusCurve()
    cp = coeficiente_potencia(tsr, curve)
    return potencia_disponivel(rho_ar, area_varrida_m2, v_mps) * cp


def area_varrida_savonius(diametro_m: float, altura_m: float) -> float:
    """Área varrida de rotor Savonius = D * H."""
    return diametro_m * altura_m
