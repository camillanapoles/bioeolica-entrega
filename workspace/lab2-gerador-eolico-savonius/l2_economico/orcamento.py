"""economico/orcamento.py — orçamento do gerador: 3 pás em compósito vs fibra de vidro.

Reusa economico.viabilidade do Lab1 e estrutural.pa do Lab2.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import get
from l2_estrutural.pa import PaCompuesto, massa_pa


@dataclass
class OrcamentoGerador:
    n_pas: int = field(default_factory=lambda: get("lab2.orcamento.n_pas"))
    custo_kg_composito: float = field(default_factory=lambda: get("lab2.orcamento.custo_kg_composito"))
    custo_kg_fibra: float = field(default_factory=lambda: get("lab2.orcamento.custo_kg_fibra"))
    custo_pmg_brl: float = field(default_factory=lambda: get("lab2.orcamento.custo_pmg_brl"))
    custo_estrutura_brl: float = field(default_factory=lambda: get("lab2.orcamento.custo_estrutura_brl"))


def custo_total(pa: PaCompuesto, o: OrcamentoGerador) -> dict:
    m_pa = massa_pa(pa)
    m_total = m_pa * o.n_pas
    custo_compos = m_total * o.custo_kg_composito + o.custo_pmg_brl + o.custo_estrutura_brl
    # baseline: tudo em fibra de vidro
    rho_fibra = get("lab2.orcamento.densidade_fibra_vidro")
    m_fibra = pa.comprimento_m * pa.corda_m * pa.espessura_m * rho_fibra * o.n_pas
    custo_baseline = m_fibra * o.custo_kg_fibra + o.custo_pmg_brl + o.custo_estrutura_brl
    return {
        "massa_total_pas_kg": m_total,
        "custo_total_composito_brl": custo_compos,
        "custo_total_baseline_fibra_brl": custo_baseline,
        "economia_brl": custo_baseline - custo_compos,
        "economia_pct": (custo_baseline - custo_compos) / custo_baseline if custo_baseline > 0 else 0.0,
        "reducao_massa_pct": (m_fibra - m_total) / m_fibra if m_fibra > 0 else 0.0,
    }
