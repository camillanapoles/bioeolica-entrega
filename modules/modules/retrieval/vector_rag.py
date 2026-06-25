"""
vector_rag.py — Lightweight Vector RAG for engineering knowledge retrieval.

Uses TF-IDF + cosine similarity (scikit-learn) for semantic search.
Swappable to external vector DB (ChromaDB, Pinecone) via the same interface.

Knowledge entries are stored as JSON in data/knowledge/ and indexed at load time.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class KnowledgeEntry:
    """A single knowledge entry in the RAG system."""

    id: str
    title: str
    content: str
    source: str = ""
    domain: str = "general"
    tags: list[str] = field(default_factory=list)
    quality_score: float = 7.0
    year: int = 2025

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:200],
            "source": self.source,
            "domain": self.domain,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "year": self.year,
        }


@dataclass
class SearchResult:
    """A search result with relevance score."""

    entry: KnowledgeEntry
    score: float


# Built-in knowledge entries for engineering domains
BUILTIN_KNOWLEDGE: list[KnowledgeEntry] = [
    # Mecânica
    KnowledgeEntry("K001", "Shaft Torsion", "d = (16*T/pi/tau)^(1/3) — ASME B106.1M",
                   "ASME B106.1M", "mecanica", ["shaft", "torsion"], 9.0),
    KnowledgeEntry("K002", "Fatigue S-N Curve", "S_f = a*N^b — Basquin equation for high-cycle fatigue",
                   "ASTM E739", "mecanica", ["fatigue", "SN"], 8.5),
    # Fluidos
    KnowledgeEntry("K003", "Bernoulli Equation", "P + 0.5*rho*v^2 + rho*g*h = constant",
                   "Euler 1757", "fluidos", ["bernoulli", "energy"], 9.5),
    KnowledgeEntry("K004", "Pump Power", "P = rho*g*Q*H/eta — hydraulic power",
                   "ISO 9906", "fluidos", ["pump", "hydraulic"], 8.5),
    # Termo
    KnowledgeEntry("K005", "Fourier's Law", "q = -k*dT/dx — heat conduction",
                   "Fourier 1822", "termo", ["conduction", "heat"], 9.5),
    KnowledgeEntry("K006", "Thermal Expansion", "delta_L = L0*alpha*delta_T — linear thermal expansion",
                   "ASTM E831", "termo", ["expansion", "CTE"], 8.5),
    # Energia
    KnowledgeEntry("K007", "Battery Capacity", "C = P*t/(V*DoD) — lead-acid sizing",
                   "IEEE 485", "energia", ["battery", "storage"], 8.0),
    # Eletricidade
    KnowledgeEntry("K008", "Stator Scaling", "D ≈ 250*P^0.4*(1500/n)^0.25 — empirical",
                   "IEC 60034", "eletricidade", ["stator", "motor"], 7.5),
    # Materiais
    KnowledgeEntry("K009", "Steel 4340", "E=205GPa, sigma_y=710MPa, density=7850kg/m³",
                   "SAE J404", "materiais", ["steel", "alloy"], 9.0),
    KnowledgeEntry("K010", "Aluminum 6061", "E=69GPa, sigma_y=276MPa, density=2700kg/m³",
                   "ASTM B209", "materiais", ["aluminum"], 8.5),
    # Construção
    KnowledgeEntry("K011", "Bolt Pretension", "F = 0.75*sigma_y*A_t — recommended preload",
                   "ASME PCC-1", "construcao", ["bolt", "fastener"], 8.5),
    # Ambiente
    KnowledgeEntry("K012", "Wind Load", "F = 0.5*rho*v^2*Cd*A — drag force",
                   "ASCE 7-22", "ambiente", ["wind", "drag"], 8.5),
    # Normativo
    KnowledgeEntry("K013", "Safety Factor", "FS = sigma_yield / sigma_applied — FoS ≥ 1.5",
                   "ASME BPVC VIII", "normativo", ["safety", "FoS"], 9.0),
    # Econômico
    KnowledgeEntry("K014", "LCC Formula", "LCC = C0 + Σ(Ct/(1+r)^t) — life cycle cost",
                   "ISO 15686", "economico", ["cost", "LCC"], 7.5),
]


class VectorRAG:
    """Lightweight Vector RAG using TF-IDF + cosine similarity.

    Usage:
        rag = VectorRAG()
        rag.index_knowledge()
        results = rag.search("shaft torsion")
    """

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.entries: list[KnowledgeEntry] = []
        self._vectorizer = None
        self._tfidf_matrix = None

    def add_entry(self, entry: KnowledgeEntry):
        """Add a single knowledge entry."""
        self.entries.append(entry)
        self._tfidf_matrix = None  # invalidate cache

    def add_builtin(self):
        """Add built-in knowledge entries."""
        for entry in BUILTIN_KNOWLEDGE:
            self.add_entry(entry)

    def load_from_directory(self) -> int:
        """Load .json knowledge files from directory. Returns count loaded."""
        count = 0
        if self.knowledge_dir.exists():
            for fpath in self.knowledge_dir.glob("*.json"):
                try:
                    data = json.loads(fpath.read_text())
                    if isinstance(data, list):
                        for item in data:
                            self.add_entry(KnowledgeEntry(**item))
                            count += 1
                except (json.JSONDecodeError, TypeError):
                    continue
        return count

    def index_knowledge(self):
        """Build TF-IDF index from current entries."""
        if not self.entries:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(stop_words="english")
            self._tfidf_matrix = self._vectorizer.fit_transform([""])
            return

        texts = [
            f"{e.title} {e.content} {' '.join(e.tags)} {e.domain}"
            for e in self.entries
        ]
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._tfidf_matrix = self._vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5,
               domain: str | None = None) -> list[SearchResult]:
        """Search knowledge base by semantic similarity.

        Parameters
        ----------
        query : str
            Search query.
        top_k : int
            Number of results to return.
        domain : str or None
            Filter by domain.

        Returns
        -------
        list[SearchResult]
            Ranked results with relevance scores.
        """
        if self._vectorizer is None or self._tfidf_matrix is None:
            self.index_knowledge()

        if self._vectorizer is None or self._tfidf_matrix is None:
            return []

        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        # Filter by domain if specified
        candidates = list(enumerate(scores))
        if domain:
            candidates = [
                (i, s) for i, s in candidates
                if self.entries[i].domain == domain
            ]

        candidates.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, s in candidates[:top_k]:
            if s > 0:
                results.append(SearchResult(entry=self.entries[i], score=round(float(s), 4)))
        return results

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Retrieve entry by ID."""
        for e in self.entries:
            if e.id == entry_id:
                return e
        return None

    def list_domains(self) -> list[str]:
        """List all available domains."""
        return sorted(set(e.domain for e in self.entries))
