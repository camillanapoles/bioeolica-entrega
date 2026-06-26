"""sim/macro.py — exposição macro: ciclos UV + amplitude térmica anual."""
from __future__ import annotations


def ciclos_termicos_anuais(deltaT_diario: float, dias: int = 365) -> float:
    """Número efetivo de ciclos térmicos anuais (proxy: ciclos = dias)."""
    return dias * max(0.0, deltaT_diario) / 25.0  # normalizado por 25°C


def fator_envelhecimento_uv(intensidade_relativa: float, horas_exposicao: float) -> float:
    """Proxy de envelhecimento UV: proporcional à dose (I*t)."""
    return max(0.0, intensidade_relativa) * horas_exposicao
