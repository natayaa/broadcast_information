"""SQLAlchemy ORM models.

Column names keep the historic database naming so existing SQLite files keep
working, while the Python attribute names are the cleaner, canonical ones.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def now() -> datetime:
    """Naive local timestamp, matching the historic ``datetime.now()`` values."""
    return datetime.now()


class User(Base):
    __tablename__ = "tb_users"

    id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column("user_email", String)
    password_hash: Mapped[str] = mapped_column("password", String, nullable=False)
    mail_password: Mapped[str | None] = mapped_column(String)
    firstname: Mapped[str | None] = mapped_column(String)
    lastname: Mapped[str | None] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=now)

    @property
    def display_name(self) -> str:
        full = " ".join(part for part in (self.firstname, self.lastname) if part)
        return full or self.username


class Document(Base):
    __tablename__ = "tb_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_no: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    document_type: Mapped[str | None] = mapped_column(String)
    document_subject: Mapped[str | None] = mapped_column(String)
    document_description: Mapped[str | None] = mapped_column(Text)
    model_tv: Mapped[str | None] = mapped_column(String)
    filename: Mapped[str | None] = mapped_column(String)
    stored_filename: Mapped[str | None] = mapped_column(String)
    content_type: Mapped[str | None] = mapped_column(String)
    file_size: Mapped[int | None] = mapped_column(Integer)
    # Legacy inline storage kept for documents uploaded before file storage existed.
    filename_upload: Mapped[bytes | None] = mapped_column(LargeBinary)
    distributed_to: Mapped[str | None] = mapped_column(String)
    uploader: Mapped[str | None] = mapped_column(String)
    uploader_id: Mapped[int | None] = mapped_column(Integer)
    datetime_upload: Mapped[datetime | None] = mapped_column(DateTime, default=now)
    last_broadcast_at: Mapped[datetime | None] = mapped_column(DateTime)

    @property
    def divisions(self) -> list[str]:
        if not self.distributed_to:
            return []
        return [item.strip() for item in self.distributed_to.split(";") if item.strip()]


class Recipient(Base):
    __tablename__ = "tb_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str | None] = mapped_column("recipient_mail", String, index=True)
    name: Mapped[str | None] = mapped_column("recipient_name", String)
    division: Mapped[str | None] = mapped_column("recipient_division", String, index=True)
    category: Mapped[str | None] = mapped_column("recipient_category", String, default="Direct")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=now)
