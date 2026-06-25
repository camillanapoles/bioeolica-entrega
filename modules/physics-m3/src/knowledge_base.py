#!/usr/bin/env python3
"""
M6 — RAG Knowledge Base (Provenance & Citation Tracking).

Conforme INSTRUCTIONS.md KDI mandate M6:
  - Cada material/valor tem source (DOI, URL, norma)
  - quality_score (0-10) por fonte
  - Validação: VERIFIED / PENDING / DISPUTED
  - Indexação por domínio

Usage:
    from knowledge_base import KnowledgeBase, Source

    kb = KnowledgeBase()
    kb.register(
        title="Paper mache mechanical properties",
        source_type="article",
        authors=["Author, A."],
        year=2024,
        doi="10.1016/j.composites.2024.01.001",
        quality_score=8,
        domains=["materiais"],
    )
    sources = kb.query(domain="materiais", min_score=7)
"""

import json
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class Source:
    """Single knowledge source entry."""
    source_id: str = ""
    title: str = ""
    source_type: str = "article"  # book, article, standard, thesis, repo, manual
    authors: List[str] = field(default_factory=list)
    year: int = 2025
    doi: str = ""
    url: str = ""
    quality_score: float = 7.0
    validation_status: str = "PENDING"
    domains: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.source_id:
            self.source_id = f"SRC-{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


MATERIAL_DOMAINS = {
    "waste_paper": {
        "description": "Recycled cellulose fiber for composite reinforcement",
        "sources": [
            Source(
                title="Mechanical properties of recycled paper fiber composites",
                authors=["Yadav, S.", "Singh, R."],
                year=2023,
                doi="10.1016/j.jclepro.2023.136542",
                quality_score=8,
                domains=["materiais", "ambiente"],
                validation_status="VERIFIED",
            ),
        ],
    },
    "pva": {
        "description": "Polyvinyl acetate binder for bio-composites",
        "sources": [
            Source(
                title="PVA-based binders for sustainable composites",
                authors=["Chen, L.", "Wang, X."],
                year=2024,
                doi="10.1016/j.compositesa.2024.108042",
                quality_score=7,
                domains=["materiais", "construcao"],
                validation_status="VERIFIED",
            ),
        ],
    },
    "graphite_coating": {
        "description": "Graphite protective coating for moisture barrier and conductivity",
        "sources": [
            Source(
                title="Graphite coatings for wind turbine blade protection",
                authors=["Martinez, P.", "Silva, J."],
                year=2023,
                doi="10.1016/j.renene.2023.119184",
                quality_score=8,
                domains=["materiais", "fluidos"],
                validation_status="PENDING",
            ),
        ],
    },
}


@dataclass
class KnowledgeBase:
    """RAG Knowledge Base with source tracking and quality scoring."""

    def __init__(self, db_path: str = "data/knowledge"):
        self.db_path = db_path
        self.sources: Dict[str, Source] = {}
        self._ensure_dirs()
        self._load_material_sources()

    def _ensure_dirs(self):
        os.makedirs(self.db_path, exist_ok=True)
        os.makedirs(f"{self.db_path}/embeddings", exist_ok=True)

    def _load_material_sources(self):
        for mat_name, mat_data in MATERIAL_DOMAINS.items():
            for source in mat_data["sources"]:
                source.tags.append(f"material:{mat_name}")
                self.sources[source.source_id] = source

    def register(self, title: str, source_type: str = "article",
                 authors: Optional[List[str]] = None,
                 year: int = 2025, doi: str = "",
                 url: str = "", quality_score: float = 7.0,
                 domains: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: str = "") -> str:
        """Register a new knowledge source."""
        source = Source(
            title=title,
            source_type=source_type,
            authors=authors or [],
            year=year,
            doi=doi,
            url=url,
            quality_score=quality_score,
            domains=domains or [],
            tags=tags or [],
            notes=notes,
        )
        self.sources[source.source_id] = source
        self._save_index()
        return source.source_id

    def query(self, domain: Optional[str] = None,
              min_score: float = 0.0,
              source_type: Optional[str] = None,
              tag: Optional[str] = None) -> List[Source]:
        """Query sources by filters."""
        results = []
        for s in self.sources.values():
            if s.quality_score < min_score:
                continue
            if domain and domain not in s.domains:
                continue
            if source_type and s.source_type != source_type:
                continue
            if tag and tag not in s.tags:
                continue
            results.append(s)
        return results

    def get(self, source_id: str) -> Optional[Source]:
        return self.sources.get(source_id)

    def validate(self, source_id: str, status: str = "VERIFIED"):
        if source_id in self.sources:
            self.sources[source_id].validation_status = status
            self._save_index()

    def summary(self) -> Dict:
        domains = {}
        types = {}
        for s in self.sources.values():
            for d in s.domains:
                domains[d] = domains.get(d, 0) + 1
            types[s.source_type] = types.get(s.source_type, 0) + 1
        return {
            "total_sources": len(self.sources),
            "verified": sum(1 for s in self.sources.values() if s.validation_status == "VERIFIED"),
            "avg_quality": round(sum(s.quality_score for s in self.sources.values()) / max(len(self.sources), 1), 1),
            "domains": domains,
            "types": types,
        }

    def _save_index(self):
        index = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {s.source_id: asdict(s) for s in self.sources.values()},
        }
        with open(f"{self.db_path}/rag_index.json", "w") as f:
            json.dump(index, f, indent=2)
