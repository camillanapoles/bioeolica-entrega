"""core/json_store.py — espelho JSON do SQLite (SSOT espelho, P$0).

Mandato INPUT.md P$0: TODA variável/dado vive em documento JSON provido por SQLite.
Este módulo é o lado "JSON" do par: lê do SQLite e materializa um documento JSON
que serve como fonte de informação consultável por humanos/agentes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import Database

# Whitelist de tabelas permitidas no espelho SSOT (P$0: SELECT só sobre nomes validados).
ALLOWED_TABLES = frozenset({"materials", "ensaios", "results", "simulacoes"})


class JsonStore:
    """Materializa tabelas do SQLite num documento JSON (Single Source of Truth)."""

    def __init__(self, db: Database, path: Path | str) -> None:
        self.db = db
        self.path = Path(path)

    def dump(self, table: str | None = None) -> Path:
        tables = [table] if table else list(ALLOWED_TABLES)
        doc: dict[str, Any] = {}
        for t in tables:
            if t not in ALLOWED_TABLES:
                raise ValueError(f"Tabela não permitida no SSOT: {t!r}")
            rows = self.db.connection.execute(f"SELECT * FROM {t}").fetchall()
            doc[t] = [dict(r) for r in rows]
        doc["_meta"] = {
            "source": "sqlite",
            "tables": tables,
            "version": 1,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(doc, ensure_ascii=False, indent=2, default=str))
        return self.path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())
