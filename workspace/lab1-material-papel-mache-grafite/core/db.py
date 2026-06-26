"""core/db.py — camada SQLite com schema versionado (P$0).

Princípios:
- P$0: SQLite é o backing-store; JSON espelha este (SSOT) via core.json_store.
- P$1: nada hardcoded; caminho do schema é injetável.
- M1/M5: cada função tem teste.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
DEFAULT_SCHEMA = Path(__file__).parent / "schema.sql"


class Database:
    """Wrapper SQLite com CRUD genérico para as tabelas do laboratório."""

    def __init__(self, path: str = ":memory:", schema_path: Path | None = None) -> None:
        self.path = path
        self.schema_path = schema_path or DEFAULT_SCHEMA
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        sql = self.schema_path.read_text()
        self.connection.executescript(sql)
        # garante user_version explicitamente (defensivo)
        cur = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if cur < SCHEMA_VERSION:
            self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self.connection.commit()

    # ---- materials CRUD -------------------------------------------------
    def insert_material(self, m: dict[str, Any]) -> int:
        cols = ("codigo", "nome", "categoria", "densidade_kg_m3", "modulo_young_pa",
                "poisson", "condutiv_termica_w_mK", "calor_especifico_j_kgK",
                "resistencia_pa", "observacoes")
        vals = {c: m.get(c) for c in cols}
        placeholders = ", ".join("?" for _ in vals)
        cur = self.connection.execute(
            f"INSERT INTO materials ({', '.join(vals)}) VALUES ({placeholders})",
            tuple(vals.values()),
        )
        self.connection.commit()
        return cur.lastrowid

    def get_material(self, mid: int) -> dict[str, Any] | None:
        r = self.connection.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        return dict(r) if r else None

    def list_materials(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.connection.execute("SELECT * FROM materials ORDER BY id")]

    def update_material(self, mid: int, patch: dict[str, Any]) -> None:
        allowed = ("codigo", "nome", "categoria", "densidade_kg_m3", "modulo_young_pa",
                   "poisson", "condutiv_termica_w_mK", "calor_especifico_j_kgK",
                   "resistencia_pa", "observacoes")
        sets = []
        vals: list[Any] = []
        for k, v in patch.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return
        sets.append("atualizado_em=datetime('now')")
        vals.append(mid)
        self.connection.execute(f"UPDATE materials SET {', '.join(sets)} WHERE id=?", tuple(vals))
        self.connection.commit()

    def delete_material(self, mid: int) -> None:
        self.connection.execute("DELETE FROM materials WHERE id=?", (mid,))
        self.connection.commit()

    # ---- results CRUD ---------------------------------------------------
    def insert_result(self, r: dict[str, Any]) -> int:
        cols = ("material_id", "ensaio", "metrica", "valor", "unidade", "configuracao_json")
        vals = {c: r.get(c) for c in cols}
        placeholders = ", ".join("?" for _ in vals)
        cur = self.connection.execute(
            f"INSERT INTO results ({', '.join(vals)}) VALUES ({placeholders})",
            tuple(vals.values()),
        )
        self.connection.commit()
        return cur.lastrowid

    def list_results(self, material_id: int | None = None) -> list[dict[str, Any]]:
        if material_id is None:
            rows = self.connection.execute("SELECT * FROM results ORDER BY id")
        else:
            rows = self.connection.execute(
                "SELECT * FROM results WHERE material_id=? ORDER BY id", (material_id,)
            )
        return [dict(r) for r in rows]

    # ---- simulacoes CRUD ------------------------------------------------
    def insert_simulacao(self, s: dict[str, Any]) -> int:
        cols = ("nome", "tipo", "config_json", "saida_json")
        vals = {c: s.get(c) for c in cols}
        placeholders = ", ".join("?" for _ in vals)
        cur = self.connection.execute(
            f"INSERT INTO simulacoes ({', '.join(vals)}) VALUES ({placeholders})",
            tuple(vals.values()),
        )
        self.connection.commit()
        return cur.lastrowid

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
