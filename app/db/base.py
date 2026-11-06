"""Database engine, session factory and FastAPI dependency."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

if settings.is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - driver hook
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Yield a short-lived session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create missing tables/columns and prepare the upload directory."""
    from app.db import models  # noqa: F401  (register metadata)

    Base.metadata.create_all(bind=engine)

    from app.db.migrations import run_migrations

    run_migrations(engine)

    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    if settings.is_sqlite:
        with engine.begin() as connection:
            connection.execute(text("PRAGMA journal_mode=WAL"))

    logger.info("Database ready at %s", settings.database_url)
