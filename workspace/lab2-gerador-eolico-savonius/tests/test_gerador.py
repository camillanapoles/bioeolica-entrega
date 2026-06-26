"""TDD: gerador/pmg.py + integrador.py."""
from l2_gerador.pmg import PMGParams, fem, corrente, potencia_saida, eficiencia
from l2_gerador.integrador import SistemaEolico, varrer_vento


def test_fem_linear():
    p = PMGParams(Ke=1.0, R_interno_ohm=0.5)
    assert abs(fem(10.0, p) - 10.0) < 1e-9


def test_potencia_saida_positiva():
    # Ke=1.0, R=0.5, T=2Nm -> I=2A, perdas=2W, Pin=40W -> Pout=33W
    p = PMGParams(Ke=1.0, R_interno_ohm=0.5, perdas_constantes_w=5.0)
    P = potencia_saida(torque_nm=2.0, omega_rad_s=20.0, p=p)
    assert P > 0
    assert abs(P - (40.0 - 4.0*0.5 - 5.0)) < 1e-9
    e = eficiencia(2.0, 20.0, p)
    assert 0 < e <= 1.0


def test_corrente_e_perdas():
    p = PMGParams(Ke=1.0, R_interno_ohm=0.5)
    assert abs(corrente(3.0, p) - 3.0) < 1e-9


def test_varrer_vento_curva():
    # PMG com Ke razoável para não saturar perdas
    from l2_gerador.pmg import PMGParams
    s = SistemaEolico(pmg=PMGParams(Ke=1.5, R_interno_ohm=0.5))
    dados = varrer_vento(s, [3.0, 5.0, 8.0, 10.0])
    assert len(dados) == 4
    assert all(d["p_turbina_w"] >= 0 for d in dados)
    assert dados[3]["p_turbina_w"] > dados[0]["p_turbina_w"]
