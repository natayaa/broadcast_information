"""Broadcast endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import ApiUser
from app.db.base import get_db
from app.schemas.documents import BroadcastRequest, BroadcastResult
from app.services import broadcast as broadcast_service

broadcast = APIRouter(prefix="/api/broadcast", tags=["Broadcast"])


@broadcast.post("", response_model=BroadcastResult)
def broadcast_document(payload: BroadcastRequest, user: ApiUser, db: Session = Depends(get_db)):
    outcome = broadcast_service.broadcast_document(
        db,
        document_no=payload.document_no,
        server_key=payload.server,
        user=user,
    )
    return BroadcastResult(
        success=True,
        message="Mail delivered",
        document_no=outcome.document_no,
        recipients=outcome.direct_count + outcome.cc_count,
        direct_recipients=outcome.direct_count,
        cc_recipients=outcome.cc_count,
    )
