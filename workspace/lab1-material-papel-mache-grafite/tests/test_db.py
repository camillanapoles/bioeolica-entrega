"""TDD: core/db.py — SQLite com schema versionado (P$0, M1/M5)."""
import sqlite3
from pathlib import Path

import pytest


def test_db_abre_em_memoria_e_cria_schema():
    from core.db import Database
    db = Database(":memory:")
    assert db.connection is not None
    # tabela de materiais deve existir após init
    cur = db.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    assert "materials" in tables
    assert "ensaios" in tables
    assert "results" in tables


def test_db_user_version_incrementa():
    from core.db import Database
    db = Database(":memory:")
    v = db.connection.execute("PRAGMA user_version").fetchone()[0]
    assert v >= 1, "schema version deve ser >= 1"


def test_crud_material_roundtrip():
    from core.db import Database
    db = Database(":memory:")
    mat_id = db.insert_material({
        "codigo": "PM-001",
        "nome": "Papel-mache base",
        "densidade_kg_m3": 600.0,
        "modulo_young_pa": 2.5e9,
    })
    assert mat_id > 0
    rows = db.list_materials()
    assert any(r["codigo"] == "PM-001" for r in rows)
    fetched = db.get_material(mat_id)
    assert fetched["densidade_kg_m3"] == 600.0
    db.update_material(mat_id, {"densidade_kg_m3": 650.0})
    assert db.get_material(mat_id)["densidade_kg_m3"] == 650.0
    db.delete_material(mat_id)
    assert db.get_material(mat_id) is None


def test_crud_resultado_ensaio():
    from core.db import Database
    db = Database(":memory:")
    mid = db.insert_material({"codigo": "X", "nome": "X", "densidade_kg_m3": 1.0, "modulo_young_pa": 1.0})
    rid = db.insert_result({
        "material_id": mid,
        "ensaio": "tracao",
        "metrica": "tensao_ruptura_pa",
        "valor": 25e6,
        "unidade": "Pa",
    })
    rows = db.list_results(material_id=mid)
    assert len(rows) == 1
    assert rows[0]["valor"] == 25e6
