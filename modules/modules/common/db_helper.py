#!/usr/bin/env python3
# =============================================================================
# Database Helper — Convenience Queries for Bioeolica
# Part of T003 — Phase 2 Foundational
# Dependencies: src/common/database.py (get_connection, database, DB_PATH)
# =============================================================================
"""
Convenience layer over database.py for introspection and bulk queries.

Does NOT replace database.py — it complements it with ergonomic helpers.
For transaction-safe object registration, use src.common.registry.
For provenance DAG operations, use src.common.provenance.

Usage:
    from src.common.db_helper import table_exists, get_all_row_counts

    if table_exists("objects"):
        counts = get_all_row_counts()
        print(f"Total objects: {counts['objects']}")
"""
import os
import sys
from typing import Any, Dict, List, Optional

_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.common.database import database, DatabaseError


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------


def get_tables() -> List[str]:
    """List all user tables in the database (excludes sqlite_* internal)."""
    with database() as db:
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]


def get_views() -> List[str]:
    """List all views in the database."""
    with database() as db:
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]


def get_table_info(table: str) -> List[Dict[str, Any]]:
    """Get column schema for a table.

    Args:
        table: Table name (validated via table_exists).

    Returns:
        List of dicts with keys: cid, name, type, notnull, dflt_value, pk.

    Raises:
        ValueError: If table does not exist.
    """
    if not table_exists(table):
        raise ValueError(f"Table '{table}' does not exist")
    with database() as db:
        rows = db.execute(f"PRAGMA table_info({_safe_table(table)})").fetchall()
    return [dict(r) for r in rows]


def table_exists(table: str) -> bool:
    """Check if a table exists in the database.

    Args:
        table: Table name to check.

    Returns:
        True if the table exists.
    """
    with database() as db:
        row = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
    return row is not None


def table_row_count(table: str) -> int:
    """Get row count for a table.

    Args:
        table: Table name (validated via table_exists).

    Returns:
        Row count.

    Raises:
        ValueError: If table does not exist.
    """
    if not table_exists(table):
        raise ValueError(f"Table '{table}' does not exist")
    with database() as db:
        row = db.execute(
            f"SELECT COUNT(*) AS cnt FROM {_safe_table(table)}"
        ).fetchone()
    return row["cnt"]


def get_all_row_counts() -> Dict[str, int]:
    """Get row counts for all user tables.

    Returns:
        Dict mapping table name -> row count.
    """
    counts = {}
    for table in get_tables():
        try:
            counts[table] = table_row_count(table)
        except Exception as e:
            counts[table] = -1
    return counts


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------


def foreign_key_check() -> List[Dict[str, Any]]:
    """Check foreign key integrity across all tables.

    Returns:
        List of FK violation dicts (empty list if all clean).
        Each dict has keys: table, rowid, parent, fkid.
    """
    with database() as db:
        rows = db.execute("PRAGMA foreign_key_check").fetchall()
    return [dict(r) for r in rows]


def integrity_check() -> List[str]:
    """Run PRAGMA integrity_check.

    Returns:
        List of strings. 'ok' means database is intact.
        Any other string indicates a corruption.
    """
    with database() as db:
        rows = db.execute("PRAGMA integrity_check").fetchall()
    return [r["integrity_check"] for r in rows]


def quick_check() -> Dict[str, Any]:
    """Run a quick database health check.

    Returns:
        Dict with keys:
            - database_ok: True if integrity_check returns 'ok'
            - table_count: number of user tables
            - view_count: number of views
            - row_counts: dict of table -> row count
            - fk_violations: number of FK violations
            - fk_details: list of FK violation dicts
    """
    integrity = integrity_check()
    fk = foreign_key_check()
    return {
        "database_ok": all(i == "ok" for i in integrity),
        "integrity_details": integrity,
        "table_count": len(get_tables()),
        "view_count": len(get_views()),
        "row_counts": get_all_row_counts(),
        "fk_violations": len(fk),
        "fk_details": fk,
    }


# ---------------------------------------------------------------------------
# Query helper
# ---------------------------------------------------------------------------


def run_query(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Run a SELECT query and return results as dicts.

    Args:
        sql: SELECT SQL statement.
        params: Optional list of parameters for parameterized query.

    Returns:
        List of row dicts.

    Raises:
        DatabaseError: If query fails or is not a SELECT.
    """
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT") and not stripped.startswith("PRAGMA"):
        raise DatabaseError("run_query only supports SELECT and PRAGMA statements")
    with database() as db:
        try:
            rows = db.execute(sql, params or []).fetchall()
        except Exception as e:
            raise DatabaseError(f"Query failed: {e}") from e
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Schema migration helpers
# ---------------------------------------------------------------------------


def get_applied_migrations() -> List[Dict[str, Any]]:
    """List all applied schema migrations.

    Returns:
        List of dicts from schema_migrations table.
    """
    with database() as db:
        rows = db.execute(
            "SELECT * FROM schema_migrations ORDER BY version ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_database_size() -> str:
    """Get the database file size in human-readable format."""
    from src.common.database import DB_PATH

    if not os.path.exists(DB_PATH):
        return "N/A"
    size = os.path.getsize(DB_PATH)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ---------------------------------------------------------------------------
# Sanitisation helper
# ---------------------------------------------------------------------------


def _safe_table(name: str) -> str:
    """Quote a table name for safe SQL interpolation.

    Only table/column names, never user data. This prevents injection
    from table names while allowing dynamic introspection.
    """
    return f'"{name}"'
