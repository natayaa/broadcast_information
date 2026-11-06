"""Recipient API endpoints (JSON)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import ApiUser
from app.db.base import get_db
from app.schemas.recipients import RecipientCreate, RecipientOut, RecipientPage
from app.services import recipients as recipients_service

recipients = APIRouter(prefix="/api/recipients", tags=["Recipients"])


@recipients.get("", response_model=RecipientPage)
def list_recipients(
    user: ApiUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    q: str | None = Query(None, max_length=120),
    division: str | None = Query(None, max_length=120),
):
    items, total, pages = recipients_service.list_recipients(
        db, page=page, page_size=page_size, q=q, division=division
    )
    return RecipientPage(
        items=[RecipientOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@recipients.post("", response_model=RecipientOut, status_code=201)
def create_recipient(payload: RecipientCreate, user: ApiUser, db: Session = Depends(get_db)):
    return RecipientOut.model_validate(recipients_service.create_recipient(db, payload))


@recipients.delete("/{recipient_id}")
def delete_recipient(recipient_id: int, user: ApiUser, db: Session = Depends(get_db)):
    recipients_service.delete_recipient(db, recipient_id)
    return {"message": "Recipient deleted"}
