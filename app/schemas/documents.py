"""Pydantic schemas for documents and broadcasts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SmtpServerKey = Literal["sharp", "office"]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_no: str
    document_type: str | None = None
    document_subject: str | None = None
    document_description: str | None = None
    model_tv: str | None = None
    filename: str | None = None
    content_type: str | None = None
    file_size: int | None = None
    distributed_to: list[str] = Field(default_factory=list)
    uploader: str | None = None
    datetime_upload: datetime | None = None
    last_broadcast_at: datetime | None = None

    @classmethod
    def from_document(cls, document) -> "DocumentOut":
        return cls(
            id=document.id,
            document_no=document.document_no,
            document_type=document.document_type,
            document_subject=document.document_subject,
            document_description=document.document_description,
            model_tv=document.model_tv,
            filename=document.filename,
            content_type=document.content_type,
            file_size=document.file_size,
            distributed_to=document.divisions,
            uploader=document.uploader,
            datetime_upload=document.datetime_upload,
            last_broadcast_at=document.last_broadcast_at,
        )


class DocumentPage(BaseModel):
    items: list[DocumentOut]
    total: int
    page: int
    page_size: int
    pages: int


class BroadcastRequest(BaseModel):
    document_no: str = Field(min_length=1, max_length=120)
    server: SmtpServerKey = "sharp"


class BroadcastResult(BaseModel):
    success: bool
    message: str
    document_no: str
    recipients: int = 0
    direct_recipients: int = 0
    cc_recipients: int = 0
