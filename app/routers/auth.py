"""Login, logout, registration and token endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import ApiUser, get_optional_user, user_payload
from app.core.errors import AppError, ConflictError
from app.core.flash import flash
from app.core.security import InvalidTokenError, create_access_token, create_refresh_token, decode_token
from app.core.templating import render
from app.db.base import get_db
from app.schemas.auth import RefreshRequest, TokenResponse, UserCreate
from app.services import users as users_service

auth = APIRouter()


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return "/app"


@auth.get("/login", include_in_schema=False)
def login_page(request: Request, next: str | None = None, db: Session = Depends(get_db)):
    if get_optional_user(request, db):
        return RedirectResponse("/app")
    return render(request, "login.html", page_title="Sign in", next_url=_safe_next(next))


@auth.post("/login", include_in_schema=False)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = users_service.authenticate(db, username=username.strip(), password=password)
    if not user:
        return render(
            request,
            "login.html",
            status_code=status.HTTP_401_UNAUTHORIZED,
            page_title="Sign in",
            error="Incorrect username or password",
            username=username,
            next_url=_safe_next(next),
        )

    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Welcome back, {user.display_name}", "success")
    return RedirectResponse(_safe_next(next), status_code=status.HTTP_303_SEE_OTHER)


@auth.post("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    flash(request, "You have been signed out", "info")
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@auth.get("/register", include_in_schema=False)
def register_page(request: Request, db: Session = Depends(get_db)):
    bootstrap = users_service.count_users(db) == 0
    user = get_optional_user(request, db)
    if not bootstrap and (not user or not user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can add users")

    return render(
        request,
        "register.html",
        user=user,
        page_title="Create account",
        bootstrap=bootstrap,
        is_admin_form=user is not None and user.is_admin,
    )


@auth.post("/register", include_in_schema=False)
def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    firstname: str = Form(""),
    lastname: str = Form(""),
    mail_password: str = Form(""),
    is_admin: str | None = Form(None),
    db: Session = Depends(get_db),
):
    bootstrap = users_service.count_users(db) == 0
    current = get_optional_user(request, db)
    if not bootstrap and (not current or not current.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can add users")

    try:
        payload = UserCreate(
            username=username.strip(),
            password=password,
            email=email.strip(),
            firstname=(firstname or "").strip() or None,
            lastname=(lastname or "").strip() or None,
            mail_password=(mail_password or "").strip() or None,
            is_admin=bootstrap or (is_admin is not None and current is not None and current.is_admin),
        )
        created = users_service.create_user(db, payload)
    except (PydanticValidationError, ConflictError, AppError) as exc:
        if isinstance(exc, PydanticValidationError):
            errors = exc.errors()
            message = errors[0].get("msg", "Invalid input") if errors else "Invalid input"
        else:
            message = exc.message
        return render(
            request,
            "register.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            user=current,
            page_title="Create account",
            bootstrap=bootstrap,
            is_admin_form=current is not None and current.is_admin,
            error=message,
            form={"username": username, "email": email, "firstname": firstname, "lastname": lastname},
        )

    flash(request, f"Account {created.username} created", "success")
    if bootstrap or current is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/app/users", status_code=status.HTTP_303_SEE_OTHER)


@auth.post("/api/auth/token", response_model=TokenResponse, tags=["Authentication"])
def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = users_service.authenticate(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@auth.post("/api/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = users_service.get_user_by_username(db, decoded["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is no longer active")

    return TokenResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@auth.get("/api/auth/me", tags=["Authentication"])
def me(user: ApiUser):
    return user_payload(user)
