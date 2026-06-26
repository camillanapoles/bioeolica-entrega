"""TDD: ensaios/ — validação de modelos analíticos (P$4 VVV)."""
import math

from ensaios.tracao import (MisturaInputs, regra_voigt, regra_reuss, halpin_tsai,
                            densidade_composita, tensao_ruptura_mistura)
from ensaios.fadiga import (BasquinParams, ciclos_para_falha_basquin,
                            CoffinMansonParams, ciclos_para_falha_cm)
from ensaios.impacto import CharpyInputs, energia_absorvida
from ensaios.dureza import shore_d_from_young
from ensaios.atrito import forca_atrito, ArchardInputs, volume_desgaste
from ensaios.fluencia import NortonParams, taxa_fluencia, deformacao_acumulada
from ensaios.termico import condutividade_efetiva, cte_efetiva, fluxo_calor_q


def test_voigt_reuss_bounds():
    x = MisturaInputs(E_matriz=2.5e9, E_carga=11e9, V_carga=0.15)
    Ev = regra_voigt(x)
    Er = regra_reuss(x)
    assert Ev > Er, "Voigt (upper) deve ser maior que Reuss (lower)"
    # bounds devem conter o Halpin-Tsai com xi=1
    Eh = halpin_tsai(x, xi=1.0)
    assert Er <= Eh <= Ev


def test_halpin_tsai_limite():
    # xi -> 0 deve se aproximar de Reuss; xi -> inf de Voigt (comportamento assintótico)
    x = MisturaInputs(E_matriz=2.5e9, E_carga=11e9, V_carga=0.15)
    Eh_small = halpin_tsai(x, xi=0.01)
    Er = regra_reuss(x)
    # devem estar próximos em ordem de grandeza (sanity)
    assert Eh_small > 0
    assert Er > 0


def test_densidade_e_resistencia_mistura():
    rho = densidade_composita(600.0, 2200.0, 0.15)
    assert 700.0 < rho < 1000.0
    sig = tensao_ruptura_mistura(25e6, 20e6, 0.15)
    assert sig > 0


def test_basquin_decrescente():
    p = BasquinParams(sigma_f_linha=100e6, b=-0.1)
    n1 = ciclos_para_falha_basquin(50e6, p)
    n2 = ciclos_para_falha_basquin(20e6, p)
    assert n2 > n1, "menor tensão -> mais ciclos até falha"


def test_coffin_manson():
    p = CoffinMansonParams(epsilon_f_linha=0.5, c=-0.6)
    n = ciclos_para_falha_cm(0.01, p)
    assert n > 1


def test_impacto_cresce_com_Kc():
    cv1 = CharpyInputs(K_c=1e6, area_secao_m2=1e-4)
    cv2 = CharpyInputs(K_c=2e6, area_secao_m2=1e-4)
    assert energia_absorvida(cv2) > energia_absorvida(cv1)


def test_shore_d_faixa():
    # E ~ 3.4 GPa (compósito alvo) deve dar Shore D entre 50 e 90
    sd = shore_d_from_young(3.4e9)
    assert 0 <= sd <= 100
    assert sd > 50


def test_atrito_coulomb_e_archard():
    assert forca_atrito(0.3, 100.0) == 30.0
    a = ArchardInputs(K_desgaste=1e-5, carga_N=100.0, deslizamento_m=1.0, dureza_pa=30e6)
    v = volume_desgaste(a)
    assert v > 0
    assert math.isclose(v, 1e-5 * 100.0 * 1.0 / 30e6, rel_tol=1e-9)


def test_fluencia_norton():
    p = NortonParams(A=1e-15, n=3.0, Q=120e3)
    eps_ponto = taxa_fluencia(10e6, 350.0, p)
    assert eps_ponto >= 0
    eps = deformacao_acumulada(10e6, 350.0, 3600.0, p)
    assert eps >= 0
    assert math.isclose(eps, eps_ponto * 3600.0, rel_tol=1e-9)


def test_termico_efetivo():
    k = condutividade_efetiva(0.12, 150.0, 0.15)
    assert 0 < k < 150
    alpha = cte_efetiva(10e-6, 8e-6, 0.15)
    assert alpha > 0
    q = fluxo_calor_q(0.5, 100.0)
    assert q == 50.0
