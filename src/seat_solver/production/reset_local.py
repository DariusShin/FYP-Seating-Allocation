"""Back up and clear local seating state; registration/layout JSON stays intact.

Stop app servers and solver processes first. Without --apply this is read-only.
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from seat_solver.production.policy import ROOT

TABLES = ("workspace_reviews", "workspace_versions", "workspaces", "audit", "events", "plans")


def reset_local(database, apply=False):
    path = Path(database).expanduser().resolve(strict=True)
    uri = path.as_uri()
    with sqlite3.connect(uri + "?mode=ro", uri=True) as reader:
        existing = {row[0] for row in reader.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        if existing - set(TABLES):
            raise ValueError(f"Refusing reset: unknown tables {sorted(existing - set(TABLES))}")
        counts = {table: reader.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                  for table in TABLES if table in existing}
        if not apply:
            return {"database": str(path), "counts": counts, "applied": False}

    # The write lock prevents changes between backup and deletion. A separate read
    # connection backs up the last committed snapshot while this lock is held.
    with sqlite3.connect(uri + "?mode=rw", uri=True, timeout=10) as writer:
        writer.execute("BEGIN IMMEDIATE")
        existing_now = {row[0] for row in writer.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        if existing_now != existing:
            raise ValueError("Database schema changed during reset; retry after stopping writers")
        counts = {table: writer.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                  for table in TABLES if table in existing}
        backup_dir = path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = backup_dir / f"{path.stem}-before-reset-{stamp}{path.suffix}"
        backup_path.touch(exist_ok=False)
        with sqlite3.connect(uri + "?mode=ro", uri=True) as reader:
            with sqlite3.connect(backup_path) as backup:
                reader.backup(backup)
                if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Backup integrity check failed; reset aborted")
        for table in TABLES:
            if table in existing:
                writer.execute(f'DELETE FROM "{table}"')
        if "sqlite_sequence" in {r[0] for r in writer.execute("SELECT name FROM sqlite_master")}:
            writer.execute("DELETE FROM sqlite_sequence")
        remaining = {table: writer.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                     for table in counts}
        if any(remaining.values()):
            raise ValueError("Reset verification failed; transaction rolled back")
    return {"database": str(path), "backup": str(backup_path), "counts_before": counts,
            "counts_after": remaining, "applied": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=os.environ.get("SEAT_PLAN_DB", str(ROOT / "output/paid-seats-v4.sqlite3")))
    parser.add_argument("--apply", action="store_true", help="Back up and clear all local plan data")
    args = parser.parse_args()
    print(json.dumps(reset_local(args.database, args.apply), indent=2))


if __name__ == "__main__":
    main()
