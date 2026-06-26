"""economico/viabilidade.py — custo, payback, VPL, escalabilidade comunitária.

Foco: substituir fibra de vidro em pás de gerador eólico para pequenas comunidades
do Nordeste/CO. Métricas: custo/kg, payback anos, VPL, custo-benefício vs baseline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class CustoComposicao:
    custo_matriz_brl_kg: float
    custo_carga_brl_kg: float
    fracao_vol_carga: float
    rho_matriz: float
    rho_carga: float
    custo_processo_brl_kg: float = 5.0


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
        taxa_desconto: float = 0.10) -> float:
    """VPL: -I + sum(economia/(1+r)^t)."""
    if anos <= 0:
        return -investimento_brl
    pv = 0.0
    for t in range(1, anos + 1):
        pv += economia_anual_brl / ((1 + taxa_desconto) ** t)
    return pv - investimento_brl


def escalabilidade_comunitaria(custo_kg: float, massa_pa_kg: float, n_pas: int,
                               custo_baseline_pa: float = 50.0) -> dict:
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
                            biodegradabilidade: float = 0.8) -> float:
    """Índice agregado em [0,1]: custo baixo + baixa densidade + baixa energia + bio."""
    c = math.exp(-custo_kg / 20.0)            # barato sobe
    d = math.exp(-(densidade_kg_m3 - 400) / 1000.0)
    e = math.exp(-energia_fabricacao_kWh_kg / 30.0)
    return max(0.0, min(1.0, 0.3 * c + 0.2 * d + 0.2 * e + 0.3 * biodegradabilidade))
