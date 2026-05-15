from collections.abc import Generator
import shutil
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from app.config import BACKEND_ROOT, DATABASE_PATH, DATABASE_URL


def create_database_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or DATABASE_URL, echo=False)


engine = create_database_engine()


def get_engine() -> Engine:
    return engine


def configure_engine(database_url: str | None = None) -> Engine:
    global engine
    engine = create_database_engine(database_url)
    return engine


def get_alembic_config(database_url: str | None = None) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url or DATABASE_URL)
    return config


def run_alembic_migrations(db_engine: Engine | None = None) -> None:
    config = get_alembic_config()
    if db_engine is None:
        command.upgrade(config, "head")
        return

    with db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def init_db(db_engine: Engine | None = None) -> None:
    active_engine = db_engine or get_engine()
    run_alembic_migrations(active_engine)


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
    new_engine = configure_engine(DATABASE_URL)
    run_alembic_migrations(new_engine)
