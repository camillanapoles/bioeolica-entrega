"""economico/viabilidade.py — custo, payback, VPL, escalabilidade comunitária.

Foco: substituir fibra de vidro em pás de gerador eólico para pequenas comunidades
do Nordeste/CO. Métricas: custo/kg, payback anos, VPL, custo-benefício vs baseline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.constants import get


@dataclass
class CustoComposicao:
    custo_matriz_brl_kg: float
    custo_carga_brl_kg: float
    fracao_vol_carga: float
    rho_matriz: float
    rho_carga: float
    custo_processo_brl_kg: float = field(default_factory=lambda: get("economico.custo_processo_brl_kg"))


def custo_por_kg(c: CustoComposicao) -> float:
    """Custo médio ponderado por fração mássica + processo."""
    # fração mássica a partir de fração volumétrica
    Vf = c.fracao_vol_carga
    Vm = 1 - Vf
    m_total = Vm * c.rho_matriz + Vf * c.rho_carga
    wf = (Vf * c.rho_carga) / m_total
    wm = (Vm * c.rho_matriz) / m_total
    return wm * c.custo_matriz_brl_kg + wf * c.custo_carga_brl_kg + c.custo_processo_brl_kg


def payback_simples(investimento_brl: float, economia_anual_brl: float) -> float:
    """Payback em anos. inf se economia <= 0."""
    if economia_anual_brl <= 0:
        return float("inf")
    return investimento_brl / economia_anual_brl


def vpl(investimento_brl: float, economia_anual_brl: float, anos: int,
        taxa_desconto: float = get("economico.taxa_desconto")) -> float:
    """VPL: -I + sum(economia/(1+r)^t)."""
    if anos <= 0:
        return -investimento_brl
    pv = 0.0
    for t in range(1, anos + 1):
        pv += economia_anual_brl / ((1 + taxa_desconto) ** t)
    return pv - investimento_brl


def escalabilidade_comunitaria(custo_kg: float, massa_pa_kg: float, n_pas: int,
                               custo_baseline_pa: float = get("economico.custo_baseline_pa_brl")) -> dict:
    """Compara custo total de pás em compósito vs baseline (fibra de vidro)."""
    custo_total = custo_kg * massa_pa_kg * n_pas
    baseline_total = custo_baseline_pa * n_pas
    return {
        "custo_total_brl": custo_total,
        "baseline_fibra_vidro_brl": baseline_total,
        "economia_brl": baseline_total - custo_total,
        "viavel": custo_total < baseline_total,
    }


def indice_sustentabilidade(custo_kg: float, densidade_kg_m3: float,
                            energia_fabricacao_kWh_kg: float,
                            biodegradabilidade: float = get("economico.biodegradabilidade")) -> float:
    """Índice agregado em [0,1]: custo baixo + baixa densidade + baixa energia + bio."""
    esc = get("economico.sustentabilidade")
    c = math.exp(-custo_kg / esc["escala_custo"])            # barato sobe
    d = math.exp(-(densidade_kg_m3 - esc["ref_densidade"]) / esc["escala_densidade"])
    e = math.exp(-energia_fabricacao_kWh_kg / esc["escala_energia"])
    return max(0.0, min(1.0,
                        esc["peso_custo"] * c + esc["peso_densidade"] * d
                        + esc["peso_energia"] * e + esc["peso_biodeg"] * biodegradabilidade))
