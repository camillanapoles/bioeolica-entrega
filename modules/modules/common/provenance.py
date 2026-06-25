# =============================================================================
# Provenance Chain Module — Composite Biomaterial for Wind Energy
# Part of T014 — Phase 2 Foundational
# Reference: contracts/schema-core.sql (provenance table), data-model.md
# =============================================================================
"""
Provenance chain recording and verification (W3C PROV-inspired DAG).

Provides:
  - record_edge(): Record a directed provenance edge between two objects
  - get_upstream(): Trace backward to find all inputs/sources
  - get_downstream(): Trace forward to find all outputs/derivatives
  - verify_acyclic(): Check DAG integrity (no cycles)
  - get_chain(): Full provenance chain for an object

Usage:
    from src.common.provenance import record_edge, get_upstream, verify_acyclic
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from src.common.database import database, DatabaseError
from src.common.registry import object_exists, ObjectNotFound


class ProvenanceError(DatabaseError):
    """Raised on provenance integrity violations (cycle, missing refs)."""
    pass


def record_edge(
    source_id: str,
    target_id: str,
    transformation: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> str:
    """Record a directed provenance edge: source → target.

    Validated: both objects must exist, no self-references, no cycles.

    Args:
        source_id: UUID v4 of the input/upstream object.
        target_id: UUID v4 of the output/derived object.
        transformation: Operation applied (e.g. 'mechanical_test',
            'simulation_run', 'calibration', 'validation').
        parameters: Optional JSON-serializable parameters dict.

    Returns:
        UUID v4 string of the new provenance record.

    Raises:
        ObjectNotFound: If source_id or target_id does not exist.
        ProvenanceError: If self-reference or cycle would be created.
    """
    if source_id == target_id:
        raise ProvenanceError("Self-referencing provenance edge is not allowed")

    # Both objects must exist
    if not object_exists(source_id):
        raise ObjectNotFound(f"source_id '{source_id}' does not exist")
    if not object_exists(target_id):
        raise ObjectNotFound(f"target_id '{target_id}' does not exist")

    # Check for immediate cycle (would create a 2-node cycle)
    if _would_create_cycle(source_id, target_id):
        raise ProvenanceError(
            f"Edge {source_id} → {target_id} would create a cycle"
        )

    edge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    params_json = json.dumps(parameters) if parameters else None

    with database() as db:
        db.execute(
            """INSERT INTO provenance (id, source_id, target_id, transformation,
                                        parameters, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (edge_id, source_id, target_id, transformation, params_json, now),
        )
        db.commit()

    return edge_id


def _would_create_cycle(source_id: str, target_id: str) -> bool:
    """Check if target_id can already reach source_id in the DAG.

    Uses recursive CTE limited to depth 50.
    """
    with database() as db:
        row = db.execute(
            """WITH RECURSIVE reachable AS (
                   SELECT target_id AS node FROM provenance WHERE source_id = ?
                   UNION ALL
                   SELECT p.target_id
                   FROM provenance p
                   JOIN reachable r ON p.source_id = r.node
                   WHERE r.node IS NOT NULL
               )
               SELECT 1 AS found FROM reachable WHERE node = ? LIMIT 1""",
            (target_id, source_id),
        ).fetchone()
    return row is not None


def get_upstream(
    object_id: str,
    max_depth: int = 50,
) -> List[Dict[str, Any]]:
    """Trace provenance backward from object_id to find all inputs/sources.

    Args:
        object_id: UUID v4 of the object to trace.
        max_depth: Maximum recursion depth (prevents infinite loops).

    Returns:
        List of dicts with keys: source_id, target_id, transformation, depth.

    Raises:
        ObjectNotFound: If object_id does not exist.
    """
    if not object_exists(object_id):
        raise ObjectNotFound(f"Object '{object_id}' not found")

    with database() as db:
        rows = db.execute(
            """WITH RECURSIVE upstream AS (
                   SELECT source_id, target_id, transformation, 1 AS depth
                   FROM provenance WHERE target_id = ?
                   UNION ALL
                   SELECT p.source_id, p.target_id, p.transformation, u.depth + 1
                   FROM provenance p
                   JOIN upstream u ON p.target_id = u.source_id
                   WHERE u.depth < ?
               )
               SELECT DISTINCT * FROM upstream ORDER BY depth ASC""",
            (object_id, max_depth),
        ).fetchall()

    return [dict(r) for r in rows]


def get_downstream(
    object_id: str,
    max_depth: int = 50,
) -> List[Dict[str, Any]]:
    """Trace provenance forward from object_id to find all outputs/derivatives.

    Args:
        object_id: UUID v4 of the object to trace.
        max_depth: Maximum recursion depth.

    Returns:
        List of dicts with keys: source_id, target_id, transformation, depth.

    Raises:
        ObjectNotFound: If object_id does not exist.
    """
    if not object_exists(object_id):
        raise ObjectNotFound(f"Object '{object_id}' not found")

    with database() as db:
        rows = db.execute(
            """WITH RECURSIVE downstream AS (
                   SELECT source_id, target_id, transformation, 1 AS depth
                   FROM provenance WHERE source_id = ?
                   UNION ALL
                   SELECT p.source_id, p.target_id, p.transformation, d.depth + 1
                   FROM provenance p
                   JOIN downstream d ON p.source_id = d.target_id
                   WHERE d.depth < ?
               )
               SELECT DISTINCT * FROM downstream ORDER BY depth ASC""",
            (object_id, max_depth),
        ).fetchall()

    return [dict(r) for r in rows]


def get_chain(object_id: str, max_depth: int = 50) -> Dict[str, Any]:
    """Get full provenance chain (upstream + downstream) for an object.

    Args:
        object_id: UUID v4 of the object.
        max_depth: Maximum recursion depth.

    Returns:
        Dict with keys:
            - object_id: the queried object
            - upstream: list of upstream edges
            - downstream: list of downstream edges
            - upstream_count: count of unique upstream sources
            - downstream_count: count of unique downstream targets
    """
    up = get_upstream(object_id, max_depth)
    down = get_downstream(object_id, max_depth)

    return {
        "object_id": object_id,
        "upstream": up,
        "downstream": down,
        "upstream_count": len({e["source_id"] for e in up}),
        "downstream_count": len({e["target_id"] for e in down}),
    }


def verify_acyclic() -> Dict[str, Any]:
    """Verify the entire provenance DAG is acyclic.

    Uses the v_provenance_cycles view to detect any cycles.

    Returns:
        Dict with keys:
            - ok: True if no cycles detected
            - cycles: list of cycle dicts (empty if ok)
            - total_edges: total provenance edge count
    """
    with database() as db:
        cycles = db.execute("SELECT * FROM v_provenance_cycles").fetchall()
        total_edges = db.execute("SELECT COUNT(*) AS cnt FROM provenance").fetchone()["cnt"]

    return {
        "ok": len(cycles) == 0,
        "cycles": [dict(c) for c in cycles],
        "total_edges": total_edges,
    }


def verify_orphans() -> Dict[str, Any]:
    """Check for orphaned provenance references.

    Uses the v_provenance_orphans view.

    Returns:
        Dict with keys:
            - ok: True if no orphans
            - orphans: list of orphan dicts (empty if ok)
    """
    with database() as db:
        orphans = db.execute("SELECT * FROM v_provenance_orphans").fetchall()

    return {
        "ok": len(orphans) == 0,
        "orphans": [dict(o) for o in orphans],
    }
