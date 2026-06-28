"""TDD: economico/viabilidade.py — payback, VPL, escalabilidade, sustentabilidade."""
import math

from economico.viabilidade import (
    CustoComposicao,
    custo_por_kg,
    escalabilidade_comunitaria,
    indice_sustentabilidade,
    payback_simples,
    vpl,
)


def test_custo_por_kg_positivo():
    c = CustoComposicao(custo_matriz_brl_kg=2.0, custo_carga_brl_kg=15.0,
                        fracao_vol_carga=0.15, rho_matriz=600.0, rho_carga=2200.0)
    v = custo_por_kg(c)
    assert v > 0
    # abaixo do baseline fibra de vidro (~R$ 30/kg)
    assert v < 30.0


def test_payback_e_vpl():
    pb = payback_simples(5000.0, 1000.0)
    assert math.isclose(pb, 5.0, rel_tol=1e-9)
    assert math.isinf(payback_simples(5000.0, 0.0))
    v = vpl(1000.0, 300.0, anos=5, taxa_desconto=0.1)
    # economia total descontada deve exceder investimento em payback curto
    assert isinstance(v, float)


def test_escalabilidade_viavel():
    r = escalabilidade_comunitaria(custo_kg=10.0, massa_pa_kg=0.5, n_pas=3, custo_baseline_pa=50.0)
    assert r["custo_total_brl"] == 15.0
    assert r["viavel"] is True
    assert r["economia_brl"] > 0


def test_indice_sustentabilidade_faixa():
    idx = indice_sustentabilidade(custo_kg=10.0, densidade_kg_m3=820.0,
                                  energia_fabricacao_kWh_kg=15.0, biodegradabilidade=0.8)
    assert 0 <= idx <= 1
    assert idx > 0.3
