#!/usr/bin/env python3
"""
scripts/migrate_unify_db.py — Consolidate SQLite databases into canonical data/bioeolica.db.

Usage:
    python scripts/migrate_unify_db.py --dry-run          # preview only
    python scripts/migrate_unify_db.py                     # execute migration
    python scripts/migrate_unify_db.py --backup-dir /tmp   # custom backup path
    python scripts/migrate_unify_db.py --force             # skip confirmation
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("migrate_unify_db")


CANONICAL = Path("data/bioeolica.db")
ORPHAN_CANDIDATES = [
    Path("bioeolica.db"),
    Path("data/database.db"),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate all SQLite databases into data/bioeolica.db."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be migrated without writing.",
    )
    parser.add_argument(
        "--backup-dir",
        default="data/backup/",
        help="Backup directory for pre-migration snapshots (default: data/backup/).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser.add_argument(
        "--restore",
        type=str,
        default=None,
        help="Restore from a backup snapshot path.",
    )
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detect_databases() -> list[Path]:
    found: list[Path] = []
    for p in ORPHAN_CANDIDATES:
        if p.exists() and p.stat().st_size > 0:
            found.append(p)
    return found


def get_table_info(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    info: dict[str, int] = {}
    for (tbl,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        info[tbl] = count
    conn.close()
    return info


def do_migration(dry_run: bool, backup_dir: Path, force: bool) -> int:
    canon = CANONICAL.resolve()
    if not canon.exists():
        log.error("Canonical DB not found: %s", canon)
        return 2

    orphans = detect_databases()
    if not orphans:
        log.info("No orphan databases found — nothing to migrate.")
        return 0

    log.info("Canonical: %s (%d bytes)", canon, canon.stat().st_size)
    canon_tables = get_table_info(canon)
    log.info("  Tables: %s", json.dumps(canon_tables, indent=2))

    for orphan in orphans:
        orphan = orphan.resolve()
        log.info("Orphan: %s (%d bytes)", orphan, orphan.stat().st_size)
        orphan_tables = get_table_info(orphan)
        log.info("  Tables: %s", json.dumps(orphan_tables, indent=2))

        for tbl, count in orphan_tables.items():
            if tbl in canon_tables:
                log.info("  Table [%s] exists in both — merge needed (%d + %d rows)", tbl, canon_tables[tbl], count)
            else:
                log.info("  Table [%s] new (%d rows) — will copy", tbl, count)

    if dry_run:
        log.info("DRY-RUN complete. No changes written.")
        return 0

    if not force:
        ans = input("Proceed with migration? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            log.info("Migration cancelled by user.")
            return 1

    # Backup canonical DB
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"bioeolica_pre_migration_{ts}.db"
    canon_hash_before = sha256(canon)
    backup_path.write_bytes(canon.read_bytes())
    log.info("Backup saved: %s", backup_path)

    # Attach and merge each orphan
    canon_conn = sqlite3.connect(str(canon))
    conflicts = 0
    for orphan in orphans:
        orphan = orphan.resolve()
        orphan_conn = sqlite3.connect(str(orphan))
        for (tbl,) in orphan_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            canon_cols = [col[1] for col in canon_conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
            orphan_cols = [col[1] for col in orphan_conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
            common_cols = [c for c in canon_cols if c in orphan_cols]
            if not common_cols:
                log.warning("  Table [%s] has no common columns — skipping", tbl)
                continue
            col_list = ", ".join(f"[{c}]" for c in common_cols)
            rows = orphan_conn.execute(f"SELECT {col_list} FROM [{tbl}]").fetchall()
            for row in rows:
                placeholders = ", ".join("?" for _ in common_cols)
                try:
                    canon_conn.execute(
                        f"INSERT INTO [{tbl}] ({col_list}) VALUES ({placeholders})",
                        row,
                    )
                except sqlite3.IntegrityError:
                    conflicts += 1
                    # Timestamp-based: try updating if updated_at column exists
                    if "updated_at" in common_cols:
                        idx = common_cols.index("updated_at")
                        canon_conn.execute(
                            f"DELETE FROM [{tbl}] WHERE rowid IN ("
                            f"  SELECT rowid FROM [{tbl}] WHERE updated_at < ?"
                            f")",
                            (row[idx],),
                        )
                        canon_conn.execute(
                            f"INSERT OR IGNORE INTO [{tbl}] ({col_list}) VALUES ({placeholders})",
                            row,
                        )
        orphan_conn.close()
    canon_conn.commit()
    canon_conn.close()

    canon_hash_after = sha256(canon)
    log.info("Migration complete. Conflicts resolved: %d", conflicts)
    log.info("SHA256 before: %s", canon_hash_before)
    log.info("SHA256 after : %s", canon_hash_after)

    result = {
        "migration_id": ts,
        "orphans": [str(o) for o in orphans],
        "backup": str(backup_path),
        "conflicts_resolved": conflicts,
        "checksum_before": canon_hash_before,
        "checksum_after": canon_hash_after,
        "status": "PASS",
    }
    (backup_dir / f"migration_{ts}.json").write_text(json.dumps(result, indent=2))
    log.info("Report: %s", backup_dir / f"migration_{ts}.json")

    # --- M5 WAL Integration ---
    try:
        sys.path.insert(0, 'workspaces/physics-m3/modules')
        from logging_wal import WALogger
        wal = WALogger(log_dir="data/logs/")
        wal.record(
            what="Database Unification Migration",
            why="Consolidate orphan DBs into canonical MapaUnico (Spec 008)",
            who="migrate_unify_db.py",
            where="data/bioeolica.db",
            how={"orphans_merged": len(orphans), "conflicts": conflicts},
            domain="infra",
            scale="macro"
        )
    except ImportError:
        log.warning("WALogger not found. Skipping M5 logging for migration.")

    return 0


def do_restore(restore_path: str) -> int:
    src = Path(restore_path)
    if not src.exists():
        log.error("Backup not found: %s", src)
        return 2
    canon = CANONICAL.resolve()
    canon.write_bytes(src.read_bytes())
    log.info("Restored %s from %s", canon, src)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.restore:
        return do_restore(args.restore)
    return do_migration(args.dry_run, Path(args.backup_dir), args.force)


if __name__ == "__main__":
    sys.exit(main())
