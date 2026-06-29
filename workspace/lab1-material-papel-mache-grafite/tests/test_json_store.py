"""TDD: core/json_store.py — JSON espelha SQLite (SSOT espelho, P$0)."""
import json


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


def test_json_store_reject_tabela_fora_whitelist(tmp_path):
    """P$0: dump() só aceita tabelas na whitelist (sem SELECT arbitrário)."""
    from core.db import Database
    from core.json_store import JsonStore
    db = Database(":memory:")
    store = JsonStore(db, tmp_path / "ssot.json")
    import pytest
    with pytest.raises(ValueError):
        store.dump(table="sqlite_master")  # tentativa de injeção fora da whitelist
