"""Server-rendered HTML routes."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import AdminUser, CurrentUser
from app.core.errors import AppError
from app.core.flash import flash
from app.core.templating import render
from app.db.base import get_db
from app.schemas.auth import UserCreate
from app.schemas.recipients import RecipientCreate
from app.services import documents as documents_service
from app.services import recipients as recipients_service
from app.services import users as users_service
from app.services.catalog import DIVISIONS, DOCUMENT_TYPES, RECIPIENT_CATEGORIES, SMTP_SERVER_LABELS

pages = APIRouter()


@pages.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/app")


@pages.get("/app", include_in_schema=False)
def dashboard(request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    _, recipient_total, _ = recipients_service.list_recipients(db, page=1, page_size=1)
    return render(
        request,
        "dashboard.html",
        user=user,
        active_page="dashboard",
        document_count=documents_service.count_documents(db),
        recipient_count=recipient_total,
        user_count=users_service.count_users(db),
        recent_documents=documents_service.recent_documents(db, limit=5),
        document_types=DOCUMENT_TYPES,
        divisions=DIVISIONS,
        smtp_servers=SMTP_SERVER_LABELS,
        page_title="Dashboard",
    )


@pages.get("/app/documents", include_in_schema=False)
def documents_page(
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    perpage: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    q: str | None = Query(None),
):
    items, total, pages = documents_service.list_documents(db, page=page, page_size=perpage, q=q)
    return render(
        request,
        "documents.html",
        user=user,
        active_page="documents",
        documents=items,
        total=total,
        page=page,
        page_size=perpage,
        total_pages=pages,
        q=q or "",
        page_title="Documents",
    )


@pages.get("/app/documents/{document_no}/file", include_in_schema=False)
def document_file(document_no: str, user: CurrentUser, db: Session = Depends(get_db)):
    document = documents_service.require_document(db, document_no)
    payload = documents_service.open_document(document)
    disposition = f'inline; filename="{quote(payload.filename)}"'

    if payload.path is not None:
        return FileResponse(
            path=payload.path,
            media_type=payload.media_type,
            headers={"Content-Disposition": disposition},
        )
    return Response(
        content=payload.data or b"",
        media_type=payload.media_type,
        headers={"Content-Disposition": disposition},
    )


@pages.get("/app/upload", include_in_schema=False)
def upload_page(request: Request, user: CurrentUser):
    return render(
        request,
        "upload_document.html",
        user=user,
        active_page="upload",
        document_types=DOCUMENT_TYPES,
        divisions=DIVISIONS,
        max_upload_mb=settings.max_upload_mb,
        page_title="Upload document",
    )


@pages.get("/app/recipients", include_in_schema=False)
def recipients_page(
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    perpage: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    q: str | None = Query(None),
):
    items, total, pages = recipients_service.list_recipients(db, page=page, page_size=perpage, q=q)
    return render(
        request,
        "recipients.html",
        user=user,
        active_page="recipients",
        recipients=items,
        total=total,
        page=page,
        page_size=perpage,
        total_pages=pages,
        q=q or "",
        divisions=DIVISIONS,
        categories=RECIPIENT_CATEGORIES,
        page_title="Recipients",
    )


@pages.post("/app/recipients", include_in_schema=False)
def create_recipient_form(
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
    email: str = Form(...),
    name: str = Form(...),
    division: str = Form(...),
    category: str = Form("Direct"),
):
    try:
        payload = RecipientCreate(email=email, name=name, division=division, category=category)
        recipients_service.create_recipient(db, payload)
        flash(request, f"Recipient {payload.email} registered", "success")
    except PydanticValidationError as exc:
        flash(request, _first_error(exc), "danger")
    except AppError as exc:
        flash(request, exc.message, "danger")
    return RedirectResponse("/app/recipients", status_code=status.HTTP_303_SEE_OTHER)


@pages.get("/app/users", include_in_schema=False)
def users_page(request: Request, user: AdminUser, db: Session = Depends(get_db)):
    return render(
        request,
        "users.html",
        user=user,
        active_page="users",
        users=users_service.list_users(db),
        page_title="Users",
    )


@pages.post("/app/users", include_in_schema=False)
def create_user_form(
    request: Request,
    user: AdminUser,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    firstname: str = Form(""),
    lastname: str = Form(""),
    mail_password: str = Form(""),
    is_admin: str | None = Form(None),
):
    try:
        payload = UserCreate(
            username=username,
            password=password,
            email=email,
            firstname=firstname or None,
            lastname=lastname or None,
            mail_password=mail_password or None,
            is_admin=is_admin is not None,
        )
        created = users_service.create_user(db, payload)
        flash(request, f"User {created.username} created", "success")
    except PydanticValidationError as exc:
        flash(request, _first_error(exc), "danger")
    except AppError as exc:
        flash(request, exc.message, "danger")
    return RedirectResponse("/app/users", status_code=status.HTTP_303_SEE_OTHER)


def _first_error(error: PydanticValidationError) -> str:
    details = error.errors()
    if not details:
        return "Invalid input"
    first = details[0]
    field = ".".join(str(part) for part in first.get("loc", []))
    return f"{field}: {first.get('msg', 'invalid value')}"
