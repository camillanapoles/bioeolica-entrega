# =============================================================================
# Unified MapaUnico using central registry and database.
# Task C7 – Unification of DB and Config.
# =============================================================================
"""
Mapa de Informação Única (Single Source of Truth) – unificado.

Em vez de criar diretórios e manter um índice JSON manual, este módulo
usa o registro universal (objects table) via `src.common.registry`.

Usage:
    from src.common.mapa_unico import MapaUnico

    mapa = MapaUnico(project="PRODUTO-COMPOSITE-001")
    mapa.register("material", "paper_mache_pva", {"E1": 3.5})
    mapa.register("simulation", "bem_analysis", {"TSR": 4.2})
    print(mapa.summary())
"""

from typing import Dict, List, Optional

from src.common.registry import (
    create_object,
    get_object,
    list_objects,
    ObjectNotFound,
)


class MapaUnico:
    """Single Source of Truth – project-level data registry backed by DB."""

    def __init__(self, project: str = "PRODUTO-COMPOSITE-001"):
        self.project = project

    def register(
        self,
        domain: str,
        name: str,
        data: Dict,
        source: str = "",
        data_type: str = "result",
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Register a data entry in the universal registry.

        Returns the UUID assigned to the object.
        """
        obj_id = create_object(
            object_type=data_type,
            tags=tags or [],
            metadata={
                "domain": domain,
                "name": name,
                "data": data,
                "source": source,
                "parent_id": parent_id,
            },
        )
        return obj_id

    def get(self, entry_id: str) -> Optional[Dict]:
        """Retrieve a data entry by UUID.

        Returns None if not found.
        """
        try:
            return get_object(entry_id)
        except ObjectNotFound:
            return None

    def query(
        self,
        domain: Optional[str] = None,
        data_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict]:
        """Query entries by domain, type, or tag.

        Uses the relational DB for filtering.
        """
        objs = list_objects(object_type=data_type if data_type else None)
        if domain:
            objs = [o for o in objs if o.get("metadata", {}).get("domain") == domain]
        if tag:
            objs = [o for o in objs if tag in o.get("tags", [])]
        return objs

    def summary(self) -> Dict:
        """Return a summary of all registered entries grouped by domain."""
        objs = list_objects(limit=1000)
        domains: Dict[str, int] = {}
        for o in objs:
            d = o.get("metadata", {}).get("domain", "unknown")
            domains[d] = domains.get(d, 0) + 1
        return {
            "project": self.project,
            "total_entries": len(objs),
            "domains": domains,
        }
