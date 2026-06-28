"""gerador/lab_orchestrator.py — pipeline Lab2: simulação -> SQLite (via Lab1.core) -> JSON SSOT."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# garantir import de core (Lab1) — conftest já prepara sys.path em pytest
_THIS = Path(__file__).resolve().parent
_LAB1 = _THIS.parents[0].parent / "lab1-material-papel-mache-grafite"
for p in (str(_LAB1), str(_THIS.parents[0])):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.db import Database  # noqa: E402
from core.json_store import JsonStore  # noqa: E402


class Lab2Orchestrator:
    """Persiste simulações do Lab2 (reusando core do Lab1)."""

    def __init__(self, db: Database, json_path: Path | str) -> None:
        self.db = db
        self.store = JsonStore(db, json_path)

    def registrar_curva_potencia(self, v_list, dados: list[dict]) -> int:
        sid = self.db.insert_simulacao({
            "nome": "curva_potencia_savonius",
            "tipo": "macro",
            "config_json": json.dumps({"v_list": list(v_list)}),
            "saida_json": json.dumps(dados, default=str),
        })
        self.store.dump()
        return sid
