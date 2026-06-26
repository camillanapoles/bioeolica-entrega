"""ensaios/impacto.py — energia absorvida em impacto Charpy (proxy proporcional).

Ref VVV: ASTM D256 (Izod/Charpy). Modelo semi-empírico sem E -> proxy proporcional.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CharpyInputs:
    K_c: float            # tenacidade à fratura (Pa*sqrt(m))
    area_secao_m2: float
    fator_geometrico: float = 1.0


def energia_absorvida(cv: CharpyInputs) -> float:
    """Proxy proporcional: CV ~ K_c^2 * A * fg. Comparação entre materiais."""
    return (cv.K_c ** 2) * cv.area_secao_m2 * cv.fator_geometrico
