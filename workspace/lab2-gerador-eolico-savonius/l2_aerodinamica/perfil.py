"""aerodinamica/perfil.py — ponto de extensão para rotor tipo Arquimedes.

Modelo placeholder: mesma interface de potência, com curva Cp característica
reportada em literatura para spiral turbines (Cp ~0.30-0.35).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArquimedesCurve:
    Cp_max: float = 0.33
    lambda_opt: float = 2.5


def cp_arquimedes(tsr: float, curve: ArquimedesCurve | None = None) -> float:
    """Proxy simples: Cp = Cp_max * exp(-((λ-λopt)/σ)^2)."""
    import math
    curve = curve or ArquimedesCurve()
    sigma = 1.0
    return curve.Cp_max * math.exp(-((tsr - curve.lambda_opt) / sigma) ** 2)
