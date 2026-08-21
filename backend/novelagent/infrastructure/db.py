from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def make_engine(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", future=True)

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def run_migrations(db_path: Path) -> bool:
    """Execute Alembic upgrade head on target SQLite database."""
    try:
        from alembic import command
        from alembic.config import Config
        repo_root = Path(__file__).resolve().parents[3]
        ini_path = repo_root / "alembic.ini"
        if ini_path.exists():
            cfg = Config(str(ini_path))
            cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.resolve()}")
            cfg.set_main_option("script_location", str((repo_root / "alembic").resolve()))
            command.upgrade(cfg, "head")
            return True
    except Exception as e:
        logger.warning("Alembic upgrade failed, falling back to create_all: %s", e)
    return False


def make_session_factory(path: Path):
    engine = make_engine(path)
    if not run_migrations(path):
        Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
