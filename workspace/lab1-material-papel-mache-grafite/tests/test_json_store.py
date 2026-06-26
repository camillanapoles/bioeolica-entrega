"""TDD: core/json_store.py — JSON espelha SQLite (SSOT espelho, P$0)."""
import json
from pathlib import Path


def test_json_store_dump_espelha_tabela(tmp_path):
    from core.db import Database
    from core.json_store import JsonStore
    db = Database(":memory:")
    db.insert_material({"codigo": "A", "nome": "A", "densidade_kg_m3": 10.0, "modulo_young_pa": 1e9})
    db.insert_material({"codigo": "B", "nome": "B", "densidade_kg_m3": 20.0, "modulo_young_pa": 2e9})
    store = JsonStore(db, tmp_path / "ssot.json")
    store.dump(table="materials")
    doc = json.loads((tmp_path / "ssot.json").read_text())
    assert "materials" in doc
    assert len(doc["materials"]) == 2
    assert {m["codigo"] for m in doc["materials"]} == {"A", "B"}


def test_json_store_load_para_dict(tmp_path):
    from core.db import Database
    from core.json_store import JsonStore
    db = Database(":memory:")
    store = JsonStore(db, tmp_path / "ssot.json")
    store.dump(table="materials")
    data = store.load()
    assert "materials" in data
