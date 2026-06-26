"""TDD: core/orchestrator.py — persistência SQLite + espelho JSON SSOT."""
import json

from core.db import Database
from core.orchestrator import LabOrchestrator
from materials.loader import load_catalog
from ensaios.tracao import MisturaInputs, halpin_tsai


def test_pipeline_ensaio_persiste_e_espelha(tmp_path):
    db = Database(":memory:")
    load_catalog(db)
    orch = LabOrchestrator(db, tmp_path / "ssot.json")
    mat = db.connection.execute("SELECT id FROM materials WHERE codigo='PM-COMPOS-15G'").fetchone()
    mid = mat["id"]
    cfg = {"modelo": "halpin_tsai", "xi": 2.0, "V_carga": 0.15}
    E = halpin_tsai(MisturaInputs(E_matriz=2.5e9, E_carga=11e9, V_carga=0.15), xi=2.0)
    rid = orch.registrar_resultado(mid, "tracao", "modulo_young_pa", E, "Pa", cfg)
    assert rid > 0
    # espelho JSON existe e contém o resultado
    doc = json.loads((tmp_path / "ssot.json").read_text())
    assert "results" in doc
    assert any(r["metrica"] == "modulo_young_pa" for r in doc["results"])


def test_pipeline_simulacao_persiste(tmp_path):
    db = Database(":memory:")
    orch = LabOrchestrator(db, tmp_path / "ssot.json")
    sid = orch.registrar_simulacao("vida_util_mc", "envelhecimento",
                                    {"n_amostras": 100}, {"media_ciclos": 1e6})
    assert sid > 0
    doc = json.loads((tmp_path / "ssot.json").read_text())
    assert any(s["nome"] == "vida_util_mc" for s in doc["simulacoes"])


def test_exportar_ssot_completo(tmp_path):
    db = Database(":memory:")
    load_catalog(db)
    orch = LabOrchestrator(db, tmp_path / "ssot.json")
    p = orch.exportar_ssot()
    assert p.exists()
    doc = json.loads(p.read_text())
    assert "materials" in doc and len(doc["materials"]) >= 4
    assert "_meta" in doc
