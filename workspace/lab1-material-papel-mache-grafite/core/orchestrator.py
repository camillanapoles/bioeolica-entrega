"""core/orchestrator.py — pipeline de laboratório: ensaio -> SQLite -> JSON SSOT.

Garante o par SQLite↔JSON (P$0) e rastreabilidade de cada resultado (M5, P$4 VVV).
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .db import Database
from .json_store import JsonStore


class LabOrchestrator:
    """Executa um ensaio virtual e persiste resultado no SQLite + espelho JSON."""

    def __init__(self, db: Database, json_path: Path | str) -> None:
        self.db = db
        self.store = JsonStore(db, json_path)

    def registrar_resultado(self, material_id: int, ensaio: str, metrica: str,
                            valor: float, unidade: str, config: dict | None = None) -> int:
        rid = self.db.insert_result({
            "material_id": material_id,
            "ensaio": ensaio,
            "metrica": metrica,
            "valor": valor,
            "unidade": unidade,
            "configuracao_json": json.dumps(config or {}, ensure_ascii=False),
        })
        self.store.dump()  # mantém espelho JSON sempre atualizado
        return rid

    def registrar_simulacao(self, nome: str, tipo: str,
                            config: dict, saida: dict) -> int:
        sid = self.db.insert_simulacao({
            "nome": nome,
            "tipo": tipo,
            "config_json": json.dumps(config, ensure_ascii=False, default=_default),
            "saida_json": json.dumps(saida, ensure_ascii=False, default=_default),
        })
        self.store.dump()
        return sid

    def exportar_ssot(self) -> Path:
        """Materializa o documento JSON completo (todas as tabelas)."""
        return self.store.dump()


def _default(o: Any) -> Any:
    if is_dataclass(o):
        return asdict(o)
    if isinstance(o, set):
        return list(o)
    return str(o)
