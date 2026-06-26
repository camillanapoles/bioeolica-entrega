"""TDD end-to-end: Lab1+Lab2 -> SQLite -> SSOT JSON consolidado (P$0, Mandato 2)."""
import json
import sys
from pathlib import Path

LAB2 = Path(__file__).resolve().parents[1].parent / "lab2-gerador-eolico-savonius"
if str(LAB2) not in sys.path:
    sys.path.insert(0, str(LAB2))

from core.db import Database
from core.orchestrator import LabOrchestrator
from core.build_ssot import build_ssot
from materials.loader import load_catalog
from ensaios.tracao import MisturaInputs, halpin_tsai
from ensaios.fadiga import BasquinParams, ciclos_para_falha_basquin
from ensaios.termico import condutividade_efetiva
from sim.envelhecimento import simular_vida_util, EnvelhecimentoConfig
from economico.viabilidade import CustoComposicao, custo_por_kg, escalabilidade_comunitaria
from l2_gerador.integrador import SistemaEolico, varrer_vento
from l2_estrutural.pa import PaCompuesto, massa_pa
from l2_economico.orcamento import OrcamentoGerador, custo_total


def test_pipeline_completo_lab1_lab2(tmp_path):
    # === Lab1 ===
    db1_path = str(tmp_path / "lab1.db")
    db1 = Database(db1_path)
    load_catalog(db1)
    orch1 = LabOrchestrator(db1, tmp_path / "lab1_ssot.json")

    mid = db1.connection.execute(
        "SELECT id FROM materials WHERE codigo='PM-COMPOS-15G'"
    ).fetchone()["id"]
    x = MisturaInputs(E_matriz=2.5e9, E_carga=11e9, V_carga=0.15)
    E = halpin_tsai(x, xi=2.0)
    orch1.registrar_resultado(mid, "tracao", "modulo_young_pa", E, "Pa",
                              {"modelo": "halpin_tsai", "xi": 2.0})
    nf = ciclos_para_falha_basquin(15e6, BasquinParams(sigma_f_linha=100e6, b=-0.1))
    orch1.registrar_resultado(mid, "fadiga", "ciclos_falha", nf, "ciclos")
    k = condutividade_efetiva(0.12, 150.0, 0.15)
    orch1.registrar_resultado(mid, "termico", "condutividade_w_mK", k, "W/m.K")
    mc = simular_vida_util(EnvelhecimentoConfig(E0=E, limiar_frac=0.7, n_amostras=200, seed=7))
    orch1.registrar_simulacao("vida_util_mc", "envelhecimento", {"n": 200, "seed": 7}, mc)
    custo = custo_por_kg(CustoComposicao(custo_matriz_brl_kg=2.0, custo_carga_brl_kg=15.0,
                                         fracao_vol_carga=0.15, rho_matriz=600.0, rho_carga=2200.0))
    esc = escalabilidade_comunitaria(custo_kg=custo, massa_pa_kg=0.5, n_pas=3)
    orch1.registrar_simulacao("escalabilidade", "economico", {"custo_kg": custo}, esc)
    db1.close()

    # === Lab2 ===
    db2_path = str(tmp_path / "lab2.db")
    db2 = Database(db2_path)
    orch2 = LabOrchestrator(db2, tmp_path / "lab2_ssot.json")
    dados = varrer_vento(SistemaEolico(), [3.0, 5.0, 8.0])
    orch2.registrar_simulacao("curva_potencia", "macro", {"v": [3, 5, 8]}, dados)
    pa = PaCompuesto(comprimento_m=0.6, corda_m=0.2, espessura_m=0.02,
                     densidade_kg_m3=820.0, resistencia_pa=30e6)
    orc = custo_total(pa, OrcamentoGerador())
    orch2.registrar_simulacao("orcamento_pa", "economico", {}, orc)
    db2.close()

    # === SSOT consolidado ===
    ssot = build_ssot(db1_path, db2_path, tmp_path / "ssot_consolidado.json")
    assert "lab1" in ssot and "lab2" in ssot
    assert len(ssot["lab1"]["results"]) >= 3
    assert len(ssot["lab1"]["simulacoes"]) >= 2
    assert len(ssot["lab2"]["simulacoes"]) >= 2
    doc = json.loads((tmp_path / "ssot_consolidado.json").read_text())
    assert doc["lab1"]["results"][0]["ensaio"] == "tracao"
