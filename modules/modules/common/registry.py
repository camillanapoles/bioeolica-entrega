# =============================================================================
# UUID/Object Registration Helper — Composite Biomaterial for Wind Energy
# Part of T013 — Phase 2 Foundational
# Reference: contracts/schema-core.sql (objects table), data-model.md
# =============================================================================
"""
Object registration in the universal registry (objects table).

Every entity in the system gets a UUID v4 primary key and a corresponding
row in the objects table. This module provides creation, lookup, and
validation of registered objects.

Usage:
    from src.common.registry import create_object, get_object, ObjectNotFound
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.common.database import database, DatabaseError

VALID_OBJECT_TYPES = frozenset({
    "specimen", "test_result", "microstructure_image",
    "computational_model", "simulation_result",
    "blade_design", "wind_turbine_system",
    "energy_system", "community_profile", "validation_reference",
    "material", "sensitivity_analysis",
})

VALID_VALIDATION_STATUSES = frozenset({"PENDING", "PASS", "FAIL"})


class ObjectNotFound(DatabaseError):
    """Raised when a requested object ID does not exist."""
    pass


class ValidationError(DatabaseError):
    """Raised when object data violates schema constraints."""
    pass


def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())


def create_object(
    object_type: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    object_id: Optional[str] = None,
) -> str:
    """Register a new object in the universal registry.

    Args:
        object_type: One of VALID_OBJECT_TYPES.
        tags: Optional list of search/filter tags.
        metadata: Optional JSON-serializable metadata dict.
        object_id: Optional explicit UUID. Auto-generated if omitted.

    Returns:
        The UUID v4 string assigned to this object.

    Raises:
        ValidationError: If object_type is invalid.
        DatabaseError: If the database insert fails.
    """
    if object_type not in VALID_OBJECT_TYPES:
        raise ValidationError(
            f"Invalid object_type '{object_type}'. "
            f"Must be one of: {sorted(VALID_OBJECT_TYPES)}"
        )

    oid = object_id or generate_uuid()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tags_json = json.dumps(tags or [])
    metadata_json = json.dumps(metadata or {})

    with database() as db:
        try:
            db.execute(
                """INSERT INTO objects (id, object_type, created_at, updated_at,
                                        tags, metadata, quality_score, validation_status)
                   VALUES (?, ?, ?, ?, ?, ?, NULL, 'PENDING')""",
                (oid, object_type, now, now, tags_json, metadata_json),
            )
            db.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to create object '{oid}': {e}") from e

    return oid


def get_object(object_id: str) -> Dict[str, Any]:
    """Retrieve an object from the registry by UUID.

    Args:
        object_id: UUID v4 string.

    Returns:
        Dict with keys: id, object_type, created_at, updated_at,
        tags (list), metadata (dict), quality_score, validation_status.

    Raises:
        ObjectNotFound: If object_id does not exist.
    """
    with database() as db:
        row = db.execute(
            "SELECT * FROM objects WHERE id = ?", (object_id,)
        ).fetchone()

    if row is None:
        raise ObjectNotFound(f"Object '{object_id}' not found in registry")

    result = dict(row)
    # Parse JSON fields
    if isinstance(result.get("tags"), str):
        result["tags"] = json.loads(result["tags"])
    if isinstance(result.get("metadata"), str):
        result["metadata"] = json.loads(result["metadata"])
    return result


def update_validation_status(object_id: str, status: str) -> None:
    """Update the validation status of an object.

    Args:
        object_id: UUID v4 string.
        status: One of 'PENDING', 'PASS', 'FAIL'.

    Raises:
        ValidationError: If status is invalid.
        ObjectNotFound: If object_id does not exist.
    """
    if status not in VALID_VALIDATION_STATUSES:
        raise ValidationError(
            f"Invalid validation_status '{status}'. "
            f"Must be one of: {sorted(VALID_VALIDATION_STATUSES)}"
        )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with database() as db:
        cursor = db.execute(
            "UPDATE objects SET validation_status = ?, updated_at = ? WHERE id = ?",
            (status, now, object_id),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise ObjectNotFound(f"Object '{object_id}' not found")


def update_quality_score(object_id: str, score: float) -> None:
    """Update the aggregate PQMS quality_score on an object.

    Args:
        object_id: UUID v4 string.
        score: Aggregate PQMS score (0-10).

    Raises:
        ValidationError: If score is out of range.
        ObjectNotFound: If object_id does not exist.
    """
    if not (0 <= score <= 10):
        raise ValidationError(f"quality_score must be between 0 and 10, got {score}")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with database() as db:
        cursor = db.execute(
            "UPDATE objects SET quality_score = ?, updated_at = ? WHERE id = ?",
            (score, now, object_id),
        )
        db.commit()
        if cursor.rowcount == 0:
            raise ObjectNotFound(f"Object '{object_id}' not found")


def list_objects(
    object_type: Optional[str] = None,
    validation_status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List objects with optional filters.

    Args:
        object_type: Filter by type (None = all types).
        validation_status: Filter by status (None = all statuses).
        limit: Maximum results.

    Returns:
        List of object dicts sorted by created_at DESC.
    """
    conditions = []
    params = []

    if object_type:
        conditions.append("object_type = ?")
        params.append(object_type)
    if validation_status:
        conditions.append("validation_status = ?")
        params.append(validation_status)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM objects WHERE {where_clause} ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with database() as db:
        rows = db.execute(query, params).fetchall()

    results = []
    for row in rows:
        result = dict(row)
        if isinstance(result.get("tags"), str):
            result["tags"] = json.loads(result["tags"])
        if isinstance(result.get("metadata"), str):
            result["metadata"] = json.loads(result["metadata"])
        results.append(result)
    return results


def object_exists(object_id: str) -> bool:
    """Check if an object UUID exists in the registry.

    Args:
        object_id: UUID v4 string.

    Returns:
        True if the object exists.
    """
    with database() as db:
        row = db.execute(
            "SELECT 1 FROM objects WHERE id = ?", (object_id,)
        ).fetchone()
    return row is not None
