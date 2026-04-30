import sqlite3
from pathlib import Path

from sqlmodel import create_engine

from app import database


def _init_sqlite_db(path: Path, value: str):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sample (value TEXT)")
        conn.execute("INSERT INTO sample(value) VALUES (?)", (value,))
        conn.commit()


def _read_sqlite_value(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT value FROM sample").fetchone()[0]


def test_export_database_snapshot_copies_current_database(monkeypatch, tmp_path):
    source_path = tmp_path / "source.db"
    target_path = tmp_path / "nested" / "snapshot.db"
    _init_sqlite_db(source_path, "from-source")
    monkeypatch.setattr(database, "DATABASE_PATH", source_path)

    database.export_database_snapshot(target_path)

    assert target_path.exists()
    assert _read_sqlite_value(target_path) == "from-source"


def test_replace_database_from_recreates_engine_and_copies_contents(monkeypatch, tmp_path):
    current_path = tmp_path / "current.db"
    source_path = tmp_path / "replacement.db"
    _init_sqlite_db(current_path, "old")
    _init_sqlite_db(source_path, "new")

    monkeypatch.setattr(database, "DATABASE_PATH", current_path)
    monkeypatch.setattr(database, "DATABASE_URL", f"sqlite:///{current_path}")
    old_engine = create_engine(f"sqlite:///{current_path}", echo=False)
    monkeypatch.setattr(database, "engine", old_engine)

    database.replace_database_from(source_path)

    assert database.engine is not old_engine
    assert _read_sqlite_value(current_path) == "new"
