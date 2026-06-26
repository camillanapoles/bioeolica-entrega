"""TDD: aerodinamica/savonius.py — modelo de potência + Betz."""
import math

from l2_aerodinamica.savonius import (SavoniusCurve, BETZ, potencia_disponivel,
                                   coeficiente_potencia, potencia_turbina,
                                   area_varrida_savonius)
from l2_aerodinamica.perfil import cp_arquimedes, ArquimedesCurve


def test_betz_limite():
    assert math.isclose(BETZ, 16.0/27.0, rel_tol=1e-9)


def test_potencia_disponivel_cubica():
    p1 = potencia_disponivel(1.225, 2.0, 5.0)
    p2 = potencia_disponivel(1.225, 2.0, 10.0)
    assert p2 / p1 == 8.0  # dobra v -> x8 potência


def test_cp_limitado_por_betz_e_cmax():
    curve = SavoniusCurve(Cp_max=0.25, lambda_opt=0.8)
    for tsr in [0.3, 0.5, 0.8, 1.0, 1.5]:
        cp = coeficiente_potencia(tsr, curve)
        assert 0 <= cp <= BETZ
    # pico próximo de lambda_opt
    cp_opt = coeficiente_potencia(0.8, curve)
    cp_off = coeficiente_potencia(0.3, curve)
    assert cp_opt >= cp_off


def test_potencia_turbina_integrada():
    curve = SavoniusCurve()
    p = potencia_turbina(1.225, 2.0, 8.0, tsr=0.8, curve=curve)
    assert p > 0
    assert p < potencia_disponivel(1.225, 2.0, 8.0)


def test_area_varrida():
    A = area_varrida_savonius(1.0, 1.5)
    assert math.isclose(A, 1.5)


def test_cp_arquimedes_pico_em_opt():
    curve = ArquimedesCurve()
    assert cp_arquimedes(2.5, curve) > cp_arquimedes(5.0, curve)
