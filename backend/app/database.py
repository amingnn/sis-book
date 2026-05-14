from collections.abc import Generator
import shutil
import sqlite3
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_PATH, DATABASE_URL
from app.migrations import run_migrations


def create_database_engine(database_url: str = DATABASE_URL) -> Engine:
    return create_engine(database_url, echo=False)


engine = create_database_engine()


def get_engine() -> Engine:
    return engine


def configure_engine(database_url: str = DATABASE_URL) -> Engine:
    global engine
    engine = create_database_engine(database_url)
    return engine


def init_db(db_engine: Engine | None = None) -> None:
    active_engine = db_engine or get_engine()
    SQLModel.metadata.create_all(active_engine)
    run_migrations(active_engine)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def export_database_snapshot(target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as source_conn, sqlite3.connect(target_path) as target_conn:
        source_conn.backup(target_conn)


def replace_database_from(source_path: Path) -> None:
    engine.dispose()
    shutil.copy2(source_path, DATABASE_PATH)
    configure_engine(DATABASE_URL)
