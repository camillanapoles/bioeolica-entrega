"""materials/loader.py — carrega catalog.json para dentro do SQLite (P$0)."""
from __future__ import annotations

import json
from pathlib import Path

from core.db import Database

DEFAULT_CATALOG = Path(__file__).parent / "catalog.json"


def load_catalog(db: Database, catalog_path: Path | None = None) -> int:
    """Insere todos os materiais do catalog no SQLite. Retorna o número inserido."""
    p = catalog_path or DEFAULT_CATALOG
    doc = json.loads(p.read_text())
    n = 0
    for m in doc["materiais"]:
        try:
            db.insert_material(m)
            n += 1
        except Exception as exc:  # noqa: BLE001
            # código duplicado -> skip; não quebra o setup
            existing = db.connection.execute(
                "SELECT id FROM materials WHERE codigo=?", (m["codigo"],)
            ).fetchone()
            if existing:
                continue
            raise
    return n


def get_by_codigo(db: Database, codigo: str) -> dict | None:
    r = db.connection.execute(
        "SELECT * FROM materials WHERE codigo=?", (codigo,)
    ).fetchone()
    return dict(r) if r else None
