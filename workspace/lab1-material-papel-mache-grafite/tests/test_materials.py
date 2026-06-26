"""TDD: materials/loader.py — carga do catalog JSON no SQLite."""
from pathlib import Path

from core.db import Database
from materials.loader import load_catalog, get_by_codigo


def test_load_catalog_insere_materiais():
    db = Database(":memory:")
    n = load_catalog(db)
    assert n >= 4  # PM-MATRIZ, GRAFITE, COMPOS, VIDRO-REF
    mats = db.list_materials()
    codigos = {m["codigo"] for m in mats}
    assert "PM-MATRIZ-001" in codigos
    assert "GRAFITE-PO-001" in codigos
    assert "PM-COMPOS-15G" in codigos


def test_load_catalog_idempotente():
    db = Database(":memory:")
    n1 = load_catalog(db)
    n2 = load_catalog(db)  # segunda vez: nenhum novo (códigos já existem)
    assert n1 >= 4
    assert n2 == 0


def test_get_by_codigo():
    db = Database(":memory:")
    load_catalog(db)
    m = get_by_codigo(db, "PM-COMPOS-15G")
    assert m is not None
    assert m["densidade_kg_m3"] == 820.0
    assert get_by_codigo(db, "INEXISTENTE") is None
