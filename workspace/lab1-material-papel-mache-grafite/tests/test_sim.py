"""TDD: sim/ — análise M3 + envelhecimento Monte Carlo."""

from sim.envelhecimento import EnvelhecimentoConfig, simular_vida_util
from sim.m3 import AnaliseM3, EscalaAnalise, analise_material_m3
from sim.macro import ciclos_termicos_anuais, fator_envelhecimento_uv


def test_m3_cobertura():
    props = {"densidade": 820.0, "modulo_young": 3.4e9, "resistencia": 30e6}
    a = analise_material_m3(props)
    dmap = a.domain_map()
    assert dmap["micro"]["coverage"] > 0
    assert 0 <= a.cobertura_total() <= 1.0


def test_m3_cobertura_vazia():
    a = AnaliseM3(macro=EscalaAnalise("macro"), meso=EscalaAnalise("meso"),
                  micro=EscalaAnalise("micro"))
    assert a.cobertura_total() == 0.0


def test_envelhecimento_montecarlo_determinismo():
    cfg = EnvelhecimentoConfig(E0=3.4e9, limiar_frac=0.7, n_amostras=500, seed=123)
    r1 = simular_vida_util(cfg)
    r2 = simular_vida_util(cfg)
    assert r1["media_ciclos"] == r2["media_ciclos"], "seed fixa => determinístico"
    assert r1["media_ciclos"] > 0
    assert 0 <= r1["frac_falha_antes_max"] <= 1


def test_macro_ciclos_uv():
    c = ciclos_termicos_anuais(15.0)
    assert c > 0
    f = fator_envelhecimento_uv(1.0, 1000.0)
    assert f > 0
