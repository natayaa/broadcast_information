"""Document persistence, upload validation and file serving."""

from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.db.models import Document, User
from app.services.catalog import DIVISIONS, DOCUMENT_TYPES

DOCUMENT_NO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PDF_MAGIC = b"%PDF-"


@dataclass
class DocumentFile:
    path: Path | None
    data: bytes | None
    filename: str
    media_type: str


def _pages(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size)) if total else 1


def list_documents(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    q: str | None = None,
) -> tuple[list[Document], int, int]:
    page = max(1, page)
    page_size = max(1, min(page_size, settings.max_page_size))

    stmt = select(Document)
    count_stmt = select(func.count()).select_from(Document)

    if q:
        pattern = f"%{q.strip()}%"
        condition = or_(
            Document.document_no.ilike(pattern),
            Document.document_subject.ilike(pattern),
            Document.model_tv.ilike(pattern),
            Document.uploader.ilike(pattern),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.scalar(count_stmt) or 0
    items = list(
        db.scalars(
            stmt.order_by(Document.datetime_upload.desc(), Document.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total, _pages(total, page_size)


def count_documents(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Document)) or 0


def recent_documents(db: Session, limit: int = 5) -> list[Document]:
    return list(
        db.scalars(
            select(Document).order_by(Document.datetime_upload.desc(), Document.id.desc()).limit(limit)
        ).all()
    )


def get_document(db: Session, document_no: str) -> Document | None:
    return db.scalar(select(Document).where(Document.document_no == document_no))


def require_document(db: Session, document_no: str) -> Document:
    document = get_document(db, document_no)
    if not document:
        raise NotFoundError(f"Document '{document_no}' was not found")
    return document


def document_numbers(db: Session) -> list[str]:
    return list(
        db.scalars(
            select(Document.document_no).order_by(Document.datetime_upload.desc(), Document.id.desc())
        ).all()
    )


def _validate_document_no(document_no: str) -> str:
    value = (document_no or "").strip()
    if not value or not DOCUMENT_NO_PATTERN.match(value):
        raise ValidationError(
            "Document number may only contain letters, digits, dots, dashes and underscores"
        )
    return value


def _validate_divisions(divisions: list[str]) -> list[str]:
    cleaned: list[str] = []
    for division in divisions:
        value = (division or "").strip()
        if not value:
            continue
        if value not in DIVISIONS:
            raise ValidationError(f"Unknown division '{value}'")
        if value not in cleaned:
            cleaned.append(value)
    if not cleaned:
        raise ValidationError("Select at least one destination division")
    return cleaned


async def create_document_from_upload(
    db: Session,
    *,
    upload: UploadFile,
    document_no: str,
    document_type: str,
    subject: str,
    description: str,
    model_tv: str,
    divisions: list[str],
    uploader: User,
) -> Document:
    document_no = _validate_document_no(document_no)
    divisions = _validate_divisions(divisions)

    document_type = (document_type or "").strip()
    if document_type not in DOCUMENT_TYPES:
        raise ValidationError(f"Unknown document type '{document_type}'")

    subject = (subject or "").strip()
    description = (description or "").strip()
    model_tv = (model_tv or "").strip()
    if not subject:
        raise ValidationError("Document subject is required")
    if len(subject) > 200:
        raise ValidationError("Document subject must be 200 characters or fewer")
    if len(model_tv) > 120:
        raise ValidationError("TV model must be 120 characters or fewer")
    if len(description) > 5000:
        raise ValidationError("Mail content must be 5000 characters or fewer")

    if get_document(db, document_no):
        raise ConflictError(f"Document number '{document_no}' already exists")

    payload = await upload.read(settings.max_upload_bytes + 1)
    if not payload:
        raise ValidationError("The uploaded file is empty")
    if len(payload) > settings.max_upload_bytes:
        raise ValidationError(f"File is larger than the {settings.max_upload_mb} MB limit")
    if not payload.startswith(PDF_MAGIC):
        raise ValidationError("Only PDF documents are accepted")

    original_name = Path(upload.filename or "document.pdf").name[:200]
    stored_name = f"{uuid.uuid4().hex}.pdf"
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    target = settings.storage_dir / stored_name
    await run_in_threadpool(target.write_bytes, payload)

    document = Document(
        document_no=document_no,
        document_type=document_type.strip(),
        document_subject=subject.strip(),
        document_description=description.strip(),
        model_tv=model_tv.strip(),
        filename=original_name,
        stored_filename=stored_name,
        content_type="application/pdf",
        file_size=len(payload),
        distributed_to=";".join(divisions),
        uploader=uploader.display_name,
        uploader_id=uploader.id,
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        target.unlink(missing_ok=True)
        raise ConflictError(f"Document number '{document_no}' already exists") from exc
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    db.refresh(document)
    return document


def delete_document(db: Session, document_no: str) -> None:
    document = require_document(db, document_no)
    stored_name = document.stored_filename
    db.delete(document)
    db.commit()

    if stored_name:
        (settings.storage_dir / stored_name).unlink(missing_ok=True)


def open_document(document: Document) -> DocumentFile:
    if document.stored_filename:
        path = settings.storage_dir / document.stored_filename
        if path.exists():
            return DocumentFile(
                path=path,
                data=None,
                filename=document.filename or f"{document.document_no}.pdf",
                media_type=document.content_type or "application/pdf",
            )

    if document.filename_upload:
        return DocumentFile(
            path=None,
            data=document.filename_upload,
            filename=document.filename or f"{document.document_no}.pdf",
            media_type=document.content_type or "application/pdf",
        )

    raise NotFoundError("The stored file for this document is missing")
