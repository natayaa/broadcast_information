"""Recipient persistence and broadcast lookups."""

from __future__ import annotations

import math

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.db.models import Recipient
from app.schemas.recipients import RecipientCreate


def _paginate(total: int, page: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size)) if total else 1


def list_recipients(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    q: str | None = None,
    division: str | None = None,
) -> tuple[list[Recipient], int, int]:
    page = max(1, page)
    page_size = max(1, min(page_size, settings.max_page_size))

    stmt = select(Recipient)
    count_stmt = select(func.count()).select_from(Recipient)

    if q:
        pattern = f"%{q.strip()}%"
        condition = Recipient.email.ilike(pattern) | Recipient.name.ilike(pattern)
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if division:
        stmt = stmt.where(Recipient.division == division)
        count_stmt = count_stmt.where(Recipient.division == division)

    total = db.scalar(count_stmt) or 0
    items = list(
        db.scalars(
            stmt.order_by(Recipient.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total, _paginate(total, page, page_size)


def create_recipient(db: Session, payload: RecipientCreate) -> Recipient:
    email = str(payload.email)
    duplicate = db.scalar(select(Recipient.id).where(Recipient.email == email))
    if duplicate:
        raise ConflictError(f"Recipient '{email}' is already registered")

    recipient = Recipient(
        email=email,
        name=payload.name.strip(),
        division=payload.division.strip(),
        category=payload.category,
    )
    db.add(recipient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"Recipient '{email}' is already registered") from exc
    db.refresh(recipient)
    return recipient


def delete_recipient(db: Session, recipient_id: int) -> None:
    recipient = db.get(Recipient, recipient_id)
    if not recipient:
        raise NotFoundError("Recipient not found")
    db.delete(recipient)
    db.commit()


def emails_for_divisions(db: Session, divisions: list[str], category: str) -> list[str]:
    """Return unique recipient e-mails for the given divisions and category."""
    if not divisions:
        return []
    rows = db.scalars(
        select(Recipient.email)
        .where(Recipient.division.in_(divisions), Recipient.category == category)
        .order_by(Recipient.id)
    ).all()

    seen: set[str] = set()
    result: list[str] = []
    for email in rows:
        if not email:
            continue
        normalised = email.strip()
        key = normalised.lower()
        if not normalised or key in seen:
            continue
        seen.add(key)
        result.append(normalised)
    return result
