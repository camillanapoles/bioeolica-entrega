"""TDD: fabricacao/ — modelos de processo."""
from fabricacao.moldagem import grau_cura, pressao_recomendada
from fabricacao.extrusao import vazao_laminar, tensao_cisalhamento_parede
from fabricacao.sinterizacao import densificacao_relativa
from fabricacao.ultrassom import energia_volumetrica, indice_dispersao
from fabricacao.spray_grafite import espessura_depositada, fracao_vol_superficial


def test_grau_cura_mono_crescente():
    x1 = grau_cura(10.0, 300.0)
    x2 = grau_cura(1000.0, 400.0)
    assert 0 <= x1 <= 1
    assert 0 <= x2 <= 1
    assert x2 > x1, "maior tempo+T -> maior cura"


def test_pressao_recomendada():
    p = pressao_recomendada(820.0, 1100.0)
    assert p >= 0


def test_poiseuille():
    q = vazao_laminar(dP=1e5, mu=1e-3, L=1.0, r=1e-2)
    assert q > 0
    tau = tensao_cisalhamento_parede(1e5, 1e-2, 1.0)
    assert tau > 0


def test_sinterizacao_crescente():
    d0 = 0.6
    d1 = densificacao_relativa(60.0, 1200.0, d0)
    d2 = densificacao_relativa(3600.0, 1400.0, d0)
    assert d1 >= d0
    assert d2 >= d1
    assert d2 <= 1.0


def test_ultrassom():
    e = energia_volumetrica(1000.0, 1e-4, 60.0)
    assert e > 0
    idx = indice_dispersao(e, E_ref_J_m3=1e8)
    assert 0 <= idx <= 1


def test_spray_grafite():
    esp = espessura_depositada(0.01, 2200.0, 0.5)
    assert esp > 0
    f = fracao_vol_superficial(0.1e-3, 1e-3)
    assert 0 <= f <= 1
