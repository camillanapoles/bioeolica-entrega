# =============================================================================
# Database Connection Module — Composite Biomaterial for Wind Energy
# Part of T010 — Phase 2 Foundational
# Reference: contracts/schema-core.sql, contracts/schema-entities.sql
# =============================================================================
"""
SQLite database connection and schema management.

Database location: data/bioeolica.db (WAL mode, foreign_keys ON)

Usage:
    with database() as db:
        db.execute("SELECT * FROM objects")
"""
import os
import sqlite3
import hashlib

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "bioeolica.db",
)

SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "specs",
    "001-composite-wind-energy",
    "contracts",
)

SCHEMA_FILES = [
    "schema-core.sql",
    "schema-entities.sql",
    "schema-validation.sql",
    "pqms-interface.sql",
]

REQUIRED_MIGRATIONS = {1, 2, 3, 4}  # Expected applied migration versions


class DatabaseError(Exception):
    """Raised on database-level failures (connection, schema mismatch, integrity)."""
    pass


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Create a configured connection to the project database.

    Args:
        db_path: Path to the SQLite database file.  If None (default)
            the module-level DB_PATH is used.

    Returns:
        sqlite3.Connection with WAL mode, foreign_keys enforcement,
        and 5-second busy timeout applied.

    Raises:
        DatabaseError: if the database file does not exist.
    """
    if db_path is None:
        db_path = DB_PATH
    if not os.path.exists(db_path):
        raise DatabaseError(
            f"Database not found at {db_path}. Run schema deployment first."
        )
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.row_factory = sqlite3.Row
    return conn


class database:
    """Context manager for safe, auto-closing database access.

    Example:
        with database() as db:
            cursor = db.execute("SELECT * FROM objects")
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def __enter__(self) -> sqlite3.Connection:
        if self.db_path is not None:
            self.conn = get_connection(db_path=self.db_path)
        else:
            # When no explicit path was given we rely on the module-level
            # DB_PATH (which may have been monkey‑patched by tests).  The
            # no‑argument form also preserves compatibility with test code
            # that replaces get_connection with a lambda that takes 0 arguments.
            self.conn = get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.conn.close()


def check_schema_version(db_path: str = None) -> dict:
    """Verify all required migrations are applied.

    Args:
        db_path: Path to the SQLite database file.  None uses DB_PATH.

    Returns:
        dict with keys:
            - applied: set of version ints found in schema_migrations
            - missing: set of versions in REQUIRED_MIGRATIONS not yet applied
            - expected: REQUIRED_MIGRATIONS (for reference)
            - ok: True if all required migrations are applied
    """
    try:
        if db_path is not None:
            with database(db_path) as db:
                rows = db.execute(
                    "SELECT version FROM schema_migrations WHERE status = 'APPLIED'"
                ).fetchall()
        else:
            with database() as db:
                rows = db.execute(
                    "SELECT version FROM schema_migrations WHERE status = 'APPLIED'"
                ).fetchall()
        applied = {r["version"] for r in rows}
    except Exception:
        return {
            "applied": set(),
            "missing": REQUIRED_MIGRATIONS,
            "expected": REQUIRED_MIGRATIONS,
            "ok": False,
        }

    missing = REQUIRED_MIGRATIONS - applied
    return {
        "applied": applied,
        "missing": missing,
        "expected": REQUIRED_MIGRATIONS,
        "ok": len(missing) == 0,
    }


def deploy_schema(
    create_db_if_missing: bool = True,
    db_path: str = None,
    schema_dir: str = None,
) -> dict:
    """Deploy all contract SQL files in dependency order.

    All files are concatenated into a single script that is executed
    inside a single transaction.  Each file's SHA-256 is recorded in
    schema_migrations after the whole script succeeds.  If *any* file
    fails the entire transaction is rolled back and the database file
    is deleted when it was created by this call.

    Args:
        create_db_if_missing: If True (default), create the database
            directory and empty database file before deployment.
        db_path: Path to the SQLite database file.  None uses DB_PATH.
        schema_dir: Directory containing the SQL schema files.
            None uses SCHEMA_DIR.

    Returns:
        dict with keys:
            - deployed: list of file names deployed
            - errors: list of (file, error_message) tuples on failure
            - ok: True if all files deployed without error

    Raises:
        DatabaseError: if create_db_if_missing is False and the database
            file does not exist.
    """
    if db_path is None:
        db_path = DB_PATH
    if schema_dir is None:
        schema_dir = SCHEMA_DIR

    # ------------------------------------------------------------------
    # 1.  Ensure the database file exists (or raise/return early)
    # ------------------------------------------------------------------
    db_dir = os.path.dirname(db_path)
    db_existed = os.path.exists(db_path)

    if create_db_if_missing:
        os.makedirs(db_dir, exist_ok=True)
        if not os.path.exists(db_path):
            sqlite3.connect(db_path).close()
    else:
        if not os.path.exists(db_path):
            raise DatabaseError(
                f"Database not found at {db_path} "
                "and create_db_if_missing=False"
            )

    # ------------------------------------------------------------------
    # 2.  Build the combined SQL script
    # ------------------------------------------------------------------
    checksums: dict[str, str] = {}
    full_script_parts: list[str] = []
    errors: list[tuple[str, str]] = []

    for sql_file in SCHEMA_FILES:
        filepath = os.path.join(schema_dir, sql_file)
        if not os.path.exists(filepath):
            errors.append(
                (sql_file, f"Schema file not found: {filepath}")
            )
            continue
        with open(filepath, "rb") as f:
            content = f.read()
        checksum = hashlib.sha256(content).hexdigest()
        checksums[sql_file] = checksum
        full_script_parts.append(content.decode("utf-8"))

    if not full_script_parts:
        errors.append(
            ("deploy", "No schema files found – cannot deploy")
        )
        return {
            "deployed": [],
            "errors": errors,
            "ok": False,
        }

    # Wrap everything in a single transaction so that any failure
    # rolls back the entire deployment atomically.
    full_script = "BEGIN;\n" + "\n".join(full_script_parts) + "\nCOMMIT;\n"

    # ------------------------------------------------------------------
    # 3.  Execute
    # ------------------------------------------------------------------
    conn = get_connection(db_path)
    deployed: list[str] = []
    _db_created_by_us = create_db_if_missing and not db_existed

    try:
        conn.executescript(full_script)

        # All files succeeded → record migration for each one
        conn.execute("BEGIN")
        for sql_file in SCHEMA_FILES:
            if sql_file not in checksums:
                continue
            chk = checksums[sql_file]
            conn.execute(
                """INSERT INTO schema_migrations
                       (description, applied_at, checksum, status)
                   VALUES (?, strftime('%Y-%m-%dT%H:%M:%SZ','now'), ?, 'APPLIED')""",
                (sql_file, chk),
            )
            deployed.append(sql_file)
        conn.commit()

    except Exception as e:
        # The internal transaction was rolled back by the error.
        errors.append(("deployment", str(e)))
        # If we created the database file ourselves, delete it to avoid
        # leaving an empty / partially-created file behind.
        if _db_created_by_us and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
    finally:
        conn.close()

    return {"deployed": deployed, "errors": errors, "ok": len(errors) == 0}
