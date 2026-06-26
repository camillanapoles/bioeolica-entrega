"""TDD: economico/orcamento.py — viabilidade compósito vs fibra."""
from l2_estrutural.pa import PaCompuesto
from l2_economico.orcamento import OrcamentoGerador, custo_total


def test_orcamento_economia():
    pa = PaCompuesto(comprimento_m=0.6, corda_m=0.2, espessura_m=0.02,
                     densidade_kg_m3=820.0, resistencia_pa=30e6)
    o = OrcamentoGerador()
    r = custo_total(pa, o)
    assert r["custo_total_composito_brl"] > 0
    assert r["custo_total_baseline_fibra_brl"] > 0
    assert r["economia_brl"] > 0
    assert 0 < r["reducao_massa_pct"] < 1
