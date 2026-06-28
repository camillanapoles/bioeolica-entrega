"""TDD: estrutural/pa.py — pá em compósito."""
from l2_estrutural.pa import PaCompuesto, fator_seguranca, massa_pa, tensao_flap


def test_massa_pa():
    pa = PaCompuesto(comprimento_m=0.6, corda_m=0.2, espessura_m=0.02,
                     densidade_kg_m3=820.0, resistencia_pa=30e6)
    m = massa_pa(pa)
    assert abs(m - (0.6*0.2*0.02*820.0)) < 1e-6


def test_tensao_e_fs():
    pa = PaCompuesto(comprimento_m=0.6, corda_m=0.2, espessura_m=0.02,
                     densidade_kg_m3=820.0, resistencia_pa=30e6)
    sigma = tensao_flap(pa, forca_n=50.0)
    fs = fator_seguranca(pa, forca_n=50.0)
    assert sigma > 0
    assert fs > 0
    # FS cai com força crescente
    assert fator_seguranca(pa, 500.0) < fs


def test_fs_infinito_forca_zero():
    pa = PaCompuesto(0.6, 0.2, 0.02, 820.0, 30e6)
    assert fator_seguranca(pa, 0.0) == float("inf")
