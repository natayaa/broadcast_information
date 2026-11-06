"""Very small, idempotent schema migrations for existing SQLite deployments.

The project historically relied on ``create_all`` only, so new columns were
never added to an existing database.  This module adds the missing columns
without destroying data and normalises the legacy date strings.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import Engine, inspect, text

logger = logging.getLogger(__name__)

_ADDED_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("tb_users", "is_admin", "BOOLEAN NOT NULL DEFAULT 0"),
    ("tb_users", "is_active", "BOOLEAN NOT NULL DEFAULT 1"),
    ("tb_users", "created_at", "DATETIME"),
    ("tb_documents", "stored_filename", "VARCHAR"),
    ("tb_documents", "content_type", "VARCHAR"),
    ("tb_documents", "file_size", "INTEGER"),
    ("tb_documents", "uploader_id", "INTEGER"),
    ("tb_documents", "last_broadcast_at", "DATETIME"),
    ("tb_recipients", "created_at", "DATETIME"),
)

_LEGACY_DATE_FORMATS = ("%d %B %Y, %H:%M", "%d %b %Y, %H:%M", "%Y-%m-%d %H:%M:%S")


def _column_names(engine: Engine, table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def _add_missing_columns(engine: Engine, table: str, columns: list[tuple[str, str]]) -> bool:
    existing = _column_names(engine, table)
    changed = False
    with engine.begin() as connection:
        for name, ddl in columns:
            if name in existing:
                continue
            connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {ddl}'))
            logger.info("Added column %s.%s", table, name)
            changed = True
    return changed


def _ensure_an_admin(engine: Engine) -> None:
    with engine.begin() as connection:
        total = connection.execute(text("SELECT COUNT(*) FROM tb_users")).scalar_one()
        if not total:
            return
        admins = connection.execute(text("SELECT COUNT(*) FROM tb_users WHERE is_admin = 1")).scalar_one()
        if admins:
            return
        connection.execute(
            text("UPDATE tb_users SET is_admin = 1 WHERE user_id = (SELECT MIN(user_id) FROM tb_users)")
        )
        logger.info("Promoted the first user account to administrator")


def _normalise_document_dates(engine: Engine) -> None:
    """Convert ``"20 October 2023, 09:47"`` strings to SQLAlchemy-friendly ISO."""
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT id, datetime_upload FROM tb_documents")).all()

    updates: list[tuple[int, str | None]] = []
    for row_id, raw_value in rows:
        if raw_value is None or isinstance(raw_value, datetime):
            continue
        if not isinstance(raw_value, str):
            continue
        parsed: datetime | None = None
        for fmt in _LEGACY_DATE_FORMATS:
            try:
                parsed = datetime.strptime(raw_value, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(raw_value)
            except ValueError:
                logger.warning("Unparseable upload date for document %s: %r", row_id, raw_value)
                continue
        normalised = parsed.strftime("%Y-%m-%d %H:%M:%S")
        if normalised != raw_value:
            updates.append((row_id, normalised))

    if not updates:
        return

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE tb_documents SET datetime_upload = :value WHERE id = :id"),
            [{"id": row_id, "value": value} for row_id, value in updates],
        )
    logger.info("Normalised %d legacy document date(s)", len(updates))


def run_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    for table in {table for table, _, _ in _ADDED_COLUMNS}:
        if table not in tables:
            continue
        columns = [(name, ddl) for tbl, name, ddl in _ADDED_COLUMNS if tbl == table]
        _add_missing_columns(engine, table, columns)

    if "tb_users" in tables:
        _ensure_an_admin(engine)
    if "tb_documents" in tables:
        _normalise_document_dates(engine)
