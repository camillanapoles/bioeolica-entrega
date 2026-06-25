#!/usr/bin/env python3
"""
M4 — Mapa de Informação Única (Single Source of Truth).

Gerencia o índice central de dados, artefatos, versões e proveniência.
Conforme INSTRUCTIONS.md KDI mandate M4:
  - Estrutura de diretórios versionada
  - master_index.json com índice [MAPA]
  - Link entre resultado, log, fonte e validação

Usage:
    from mapa_unico import MapaUnico, DataRegistry

    mapa = MapaUnico(project="PRODUTO-COMPOSITE-001")
    mapa.register("material", "paper_mache_pva", {"E1": 3.5})
    mapa.register("simulation", "bem_analysis", {"TSR": 4.2})
    print(mapa.summary())
"""

import json
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class DataEntry:
    """Single entry in the Mapa Unico."""
    domain: str
    name: str
    data_type: str  # material, simulation, test, geometry, result
    data: Dict[str, Any]
    entry_id: str = ""
    source: str = ""
    version: str = "1.0.0"
    created_at: str = ""
    parent_id: Optional[str] = None
    validation_status: str = "PENDING"
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.entry_id:
            self.entry_id = f"MAP-{uuid.uuid4().hex[:12]}"


class MapaUnico:
    """Single Source of Truth — project-level data registry."""

    def __init__(self, project: str = "PRODUTO-COMPOSITE-001",
                 base_path: str = "data"):
        self.project = project
        self.base_path = base_path
        self.entries: Dict[str, DataEntry] = {}
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create directory structure per M4 spec."""
        dirs = ["materials", "geometry", "mesh", "results", "logs", "knowledge"]
        for d in dirs:
            os.makedirs(f"{self.base_path}/{d}", exist_ok=True)

    def register(self, domain: str, name: str, data: Dict,
                 source: str = "", data_type: str = "result",
                 parent_id: Optional[str] = None,
                 tags: Optional[List[str]] = None) -> str:
        """Register a data entry."""
        entry = DataEntry(
            domain=domain,
            name=name,
            data_type=data_type,
            data=data,
            source=source,
            parent_id=parent_id,
            tags=tags or [],
        )
        self.entries[entry.entry_id] = entry
        self._save_index()
        return entry.entry_id

    def get(self, entry_id: str) -> Optional[DataEntry]:
        return self.entries.get(entry_id)

    def query(self, domain: Optional[str] = None,
              data_type: Optional[str] = None,
              tag: Optional[str] = None) -> List[DataEntry]:
        """Query entries by domain, type, or tag."""
        results = []
        for e in self.entries.values():
            if domain and e.domain != domain:
                continue
            if data_type and e.data_type != data_type:
                continue
            if tag and tag not in e.tags:
                continue
            results.append(e)
        return results

    def validate(self, entry_id: str, status: str = "PASS") -> None:
        """Set validation status for an entry."""
        if entry_id in self.entries:
            self.entries[entry_id].validation_status = status
            self._save_index()

    def _save_index(self):
        """Save master index as JSON."""
        index = {
            "project": self.project,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": {
                eid: {
                    "id": e.entry_id,
                    "domain": e.domain,
                    "name": e.name,
                    "data_type": e.data_type,
                    "version": e.version,
                    "created_at": e.created_at,
                    "parent_id": e.parent_id,
                    "validation_status": e.validation_status,
                    "tags": e.tags,
                }
                for eid, e in self.entries.items()
            },
        }
        with open(f"{self.base_path}/master_index.json", "w") as f:
            json.dump(index, f, indent=2)

    def summary(self) -> Dict:
        domains = {}
        for e in self.entries.values():
            domains[e.domain] = domains.get(e.domain, 0) + 1
        return {
            "project": self.project,
            "total_entries": len(self.entries),
            "domains": domains,
            "index_path": f"{self.base_path}/master_index.json",
        }
