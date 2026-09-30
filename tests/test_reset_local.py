"""A local reset clears complete seating state and preserves a restorable backup."""
import sqlite3

import pytest

from seat_solver.production.plan_store import PlanStore
from seat_solver.production.workspace import WorkspaceStore
from seat_solver.production.reset_local import TABLES, reset_local


def populated(path):
    store = PlanStore(path)
    WorkspaceStore(store)
    with store.connection() as db:
        db.execute("INSERT INTO plans(id,event,body,hash,state,actor,created) VALUES('p','e','{}','h','DRAFT','staff','now')")
        db.execute("INSERT INTO events VALUES('e','p')")
        db.execute("INSERT INTO audit(event,plan,action,actor,at) VALUES('e','p','save','staff','now')")
        db.execute("INSERT INTO workspaces VALUES('e','p',1,'{}','now','staff')")
        db.execute("INSERT INTO workspace_reviews VALUES('e','p','{}')")
        db.execute("INSERT INTO workspace_versions VALUES('e','p','{}','now','staff')")
    return store


def counts(path):
    with sqlite3.connect(path) as db:
        return {table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in TABLES}


def test_reset_is_dry_run_by_default_and_backup_restores_every_table(tmp_path):
    path = tmp_path / 'plans.sqlite3'
    populated(path)
    preview = reset_local(path)
    assert preview['applied'] is False
    assert all(n == 1 for n in counts(path).values())
    assert not (tmp_path / 'backups').exists()
    result = reset_local(path, apply=True)
    assert all(n == 0 for n in counts(path).values())
    assert all(n == 1 for n in counts(result['backup']).values())
    assert PlanStore(path).latest('e') is None
    assert PlanStore(path).published('e') is None
    with sqlite3.connect(result['backup']) as source, sqlite3.connect(tmp_path / 'restored.sqlite3') as dest:
        source.backup(dest)
    assert counts(tmp_path / 'restored.sqlite3') == result['counts_before']


def test_unknown_database_tables_abort_without_deleting(tmp_path):
    path = tmp_path / 'unexpected.sqlite3'
    populated(path)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE other_data(id INTEGER)')
        db.execute('INSERT INTO other_data VALUES(1)')
    with pytest.raises(ValueError, match='unknown tables'):
        reset_local(path, apply=True)
    assert all(n == 1 for n in counts(path).values())


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path / 'missing.sqlite3'
    with pytest.raises(FileNotFoundError):
        reset_local(path, apply=True)
    assert not path.exists()
