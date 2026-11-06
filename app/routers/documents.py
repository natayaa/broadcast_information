"""Document API endpoints (JSON)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import ApiUser
from app.db.base import get_db
from app.schemas.documents import DocumentOut, DocumentPage
from app.services import documents as documents_service

documents = APIRouter(prefix="/api/documents", tags=["Documents"])


@documents.get("", response_model=DocumentPage)
def list_documents(
    user: ApiUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    q: str | None = Query(None, max_length=120),
):
    items, total, pages = documents_service.list_documents(db, page=page, page_size=page_size, q=q)
    return DocumentPage(
        items=[DocumentOut.from_document(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@documents.get("/numbers")
def list_document_numbers(user: ApiUser, db: Session = Depends(get_db)):
    return {"items": documents_service.document_numbers(db)}


@documents.get("/{document_no}", response_model=DocumentOut)
def get_document(document_no: str, user: ApiUser, db: Session = Depends(get_db)):
    return DocumentOut.from_document(documents_service.require_document(db, document_no))


@documents.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    user: ApiUser,
    db: Session = Depends(get_db),
    document_no: str = Form(...),
    document_type: str = Form(...),
    subject: str = Form(...),
    description: str = Form(""),
    model_tv: str = Form(""),
    distributed_to: Annotated[list[str], Form(...)] = ...,
    file: UploadFile = File(...),
):
    document = await documents_service.create_document_from_upload(
        db,
        upload=file,
        document_no=document_no,
        document_type=document_type,
        subject=subject,
        description=description,
        model_tv=model_tv,
        divisions=distributed_to,
        uploader=user,
    )
    return DocumentOut.from_document(document)


@documents.delete("/{document_no}")
def delete_document(document_no: str, user: ApiUser, db: Session = Depends(get_db)):
    documents_service.delete_document(db, document_no)
    return {"message": f"Document '{document_no}' deleted"}
