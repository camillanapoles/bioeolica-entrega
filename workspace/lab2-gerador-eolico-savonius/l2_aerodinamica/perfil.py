"""aerodinamica/perfil.py — ponto de extensão para rotor tipo Arquimedes.

Modelo placeholder: mesma interface de potência, com curva Cp característica
reportada em literatura para spiral turbines (Cp ~0.30-0.35).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import get


@dataclass
class ArquimedesCurve:
    Cp_max: float = field(default_factory=lambda: get("lab2.arquimedes.Cp_max"))
    lambda_opt: float = field(default_factory=lambda: get("lab2.arquimedes.lambda_opt"))


def cp_arquimedes(tsr: float, curve: ArquimedesCurve | None = None) -> float:
    """Proxy simples: Cp = Cp_max * exp(-((λ-λopt)/σ)^2)."""
    import math
    curve = curve or ArquimedesCurve()
    sigma = get("lab2.arquimedes.sigma_curva")
    return curve.Cp_max * math.exp(-((tsr - curve.lambda_opt) / sigma) ** 2)
