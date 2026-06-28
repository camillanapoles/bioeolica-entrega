"""sim/macro.py — exposição macro: ciclos UV + amplitude térmica anual."""
from __future__ import annotations

from core.constants import get

_DIAS_ANO = get("sim.macro.dias_por_ano")
_DELTA_T_NORM = get("sim.macro.delta_t_normalizacao_c")  # normalização por 25°C


def ciclos_termicos_anuais(deltaT_diario: float, dias: int = _DIAS_ANO) -> float:
    """Número efetivo de ciclos térmicos anuais (proxy: ciclos = dias)."""
    return dias * max(0.0, deltaT_diario) / _DELTA_T_NORM


def fator_envelhecimento_uv(intensidade_relativa: float, horas_exposicao: float) -> float:
    """Proxy de envelhecimento UV: proporcional à dose (I*t)."""
    return max(0.0, intensidade_relativa) * horas_exposicao
