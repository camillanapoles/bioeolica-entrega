"""economico/orcamento.py — orçamento do gerador: 3 pás em compósito vs fibra de vidro.

Reusa economico.viabilidade do Lab1 e estrutural.pa do Lab2.
"""
from __future__ import annotations

from dataclasses import dataclass

from l2_estrutural.pa import PaCompuesto, massa_pa


@dataclass
class OrcamentoGerador:
    n_pas: int = 3
    custo_kg_composito: float = 12.0
    custo_kg_fibra: float = 30.0
    custo_pmg_brl: float = 800.0
    custo_estrutura_brl: float = 600.0


def custo_total(pa: PaCompuesto, o: OrcamentoGerador) -> dict:
    m_pa = massa_pa(pa)
    m_total = m_pa * o.n_pas
    custo_compos = m_total * o.custo_kg_composito + o.custo_pmg_brl + o.custo_estrutura_brl
    custo_fibra = m_total * (o.custo_kg_composito + o.custo_kg_fibra) + o.custo_pmg_brl + o.custo_estrutura_brl
    # baseline: tudo em fibra de vidro (densidade ~2550)
    m_fibra = pa.comprimento_m * pa.corda_m * pa.espessura_m * 2550.0 * o.n_pas
    custo_baseline = m_fibra * o.custo_kg_fibra + o.custo_pmg_brl + o.custo_estrutura_brl
    return {
        "massa_total_pas_kg": m_total,
        "custo_total_composito_brl": custo_compos,
        "custo_total_baseline_fibra_brl": custo_baseline,
        "economia_brl": custo_baseline - custo_compos,
        "economia_pct": (custo_baseline - custo_compos) / custo_baseline if custo_baseline > 0 else 0.0,
        "reducao_massa_pct": (m_fibra - m_total) / m_fibra if m_fibra > 0 else 0.0,
    }
