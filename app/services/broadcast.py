"""Broadcast orchestration: document -> recipients -> SMTP delivery."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import ValidationError
from app.db.models import User, now
from app.services import mail
from app.services.documents import require_document
from app.services.recipients import emails_for_divisions


@dataclass
class BroadcastOutcome:
    document_no: str
    direct_count: int
    cc_count: int


def build_body(document, download_url: str) -> str:
    description = (document.document_description or "").strip()
    lines = [description] if description else []
    lines.extend(
        [
            "",
            "The document is available at the following link:",
            download_url,
        ]
    )
    return "\n".join(lines)


def broadcast_document(db: Session, *, document_no: str, server_key: str, user: User) -> BroadcastOutcome:
    document = require_document(db, document_no)

    direct = emails_for_divisions(db, document.divisions, "Direct")
    cc = emails_for_divisions(db, document.divisions, "CC")

    if not direct:
        raise ValidationError(
            "No direct recipients are registered for the selected divisions. "
            "Register recipients first or change the document destinations."
        )

    base_url = settings.public_base_url.rstrip("/")
    download_url = f"{base_url}/app/documents/{quote(document.document_no, safe='')}/file"
    subject = f"[Reminder] {document.document_subject or document.document_no}"
    body = build_body(document, download_url)

    sender_email, sender_password = mail.resolve_sender(user)
    mail.send_broadcast(
        server_key=server_key,
        sender_email=sender_email,
        sender_password=sender_password,
        to=direct,
        cc=cc,
        subject=subject,
        body=body,
    )

    document.last_broadcast_at = now()
    db.commit()

    return BroadcastOutcome(document_no=document.document_no, direct_count=len(direct), cc_count=len(cc))
