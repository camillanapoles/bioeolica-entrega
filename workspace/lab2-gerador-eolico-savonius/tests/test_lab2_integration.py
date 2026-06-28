"""TDD: cobertura dos módulos de integração Lab2→Lab1 (0% → cobertos).

- l2_gerador.lab_orchestrator.Lab2Orchestrator: persiste curva de potência no SQLite (Lab1.core).
- l2_economico.viabilidade_lab1: ponte DRY que re-exporta Lab1.economico.viabilidade.
"""
import json


# ---------------------------------------------------------------- Lab2Orchestrator
def test_lab2_orchestrator_registra_curva_potencia(tmp_path):
    from core.db import Database
    from l2_gerador.lab_orchestrator import Lab2Orchestrator

    db = Database(":memory:")
    orch = Lab2Orchestrator(db, tmp_path / "ssot_lab2.json")
    v_list = [3.0, 6.0, 9.0]
    dados = [{"v": v, "p_w": v ** 3} for v in v_list]

    sid = orch.registrar_curva_potencia(v_list, dados)

    assert sid > 0
    # simulacoes persistidas?
    rows = db.connection.execute("SELECT * FROM simulacoes WHERE id=?", (sid,)).fetchone()
    assert rows is not None
    saida = json.loads(dict(rows)["saida_json"])
    assert len(saida) == 3
    # espelho JSON atualizado (P$0 SSOT)
    doc = json.loads((tmp_path / "ssot_lab2.json").read_text())
    assert "simulacoes" in doc


def test_lab2_orchestrator_tipo_macro_e_nome(tmp_path):
    from core.db import Database
    from l2_gerador.lab_orchestrator import Lab2Orchestrator

    db = Database(":memory:")
    orch = Lab2Orchestrator(db, tmp_path / "ssot.json")
    sid = orch.registrar_curva_potencia([5.0], [{"v": 5.0, "p_w": 125.0}])
    row = dict(db.connection.execute(
        "SELECT nome, tipo FROM simulacoes WHERE id=?", (sid,)).fetchone())
    assert row["nome"] == "curva_potencia_savonius"
    assert row["tipo"] == "macro"


# ------------------------------------------------------ ponte viabilidade_lab1 (DRY)
def test_ponte_viabilidade_lab1_reexporta_api():
    """A ponte re-exporta a API pública de Lab1.economico.viabilidade sem quebrar."""
    from l2_economico import viabilidade_lab1 as bridge

    assert callable(bridge.custo_por_kg)
    assert callable(bridge.payback_simples)
    assert callable(bridge.vpl)
    assert callable(bridge.escalabilidade_comunitaria)
    assert callable(bridge.indice_sustentabilidade)
    assert hasattr(bridge, "CustoComposicao")


def test_ponte_viabilidade_lab1_executa_calculo():
    """E2E: a ponte executa o mesmo cálculo do Lab1 (DRY não é só alias)."""
    from l2_economico.viabilidade_lab1 import (
        CustoComposicao,
        custo_por_kg,
        escalabilidade_comunitaria,
        payback_simples,
    )

    c = CustoComposicao(
        custo_matriz_brl_kg=2.0,
        custo_carga_brl_kg=15.0,
        fracao_vol_carga=0.15,
        rho_matriz=600.0,
        rho_carga=2200.0,
    )
    ck = custo_por_kg(c)
    assert ck > 0
    # payback: investimento 1000, economia 250/ano -> 4 anos
    assert abs(payback_simples(1000.0, 250.0) - 4.0) < 1e-9
    # escalabilidade: compósito mais barato que baseline -> viável
    esc = escalabilidade_comunitaria(ck, massa_pa_kg=2.0, n_pas=3)
    assert "viavel" in esc and "economia_brl" in esc
