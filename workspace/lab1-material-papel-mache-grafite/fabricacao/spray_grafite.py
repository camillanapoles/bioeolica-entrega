"""fabricacao/spray_grafite.py — deposição de grafite por spray.

Modelo simples: espessura = massa_depositada / (rho * area).
Fração volumétrica efetiva = espessura * rho_grafite / espessura_total / rho_compos.
"""
from __future__ import annotations


def espessura_depositada(massa_kg: float, rho_kg_m3: float, area_m2: float) -> float:
    if rho_kg_m3 <= 0 or area_m2 <= 0:
        return 0.0
    return massa_kg / (rho_kg_m3 * area_m2)


def fracao_vol_superficial(espessura_grafite: float, espessura_total: float) -> float:
    """Fração volumétrica aproximada de grafite na superfície."""
    if espessura_total <= 0:
        return 0.0
    return min(1.0, max(0.0, espessura_grafite / espessura_total))
