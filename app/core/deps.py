"""Shared FastAPI dependencies for authentication and authorisation."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_token
from app.db.base import get_db
from app.db.models import User

bearer_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
BearerToken = Annotated[str | None, Depends(bearer_scheme)]


def _load_active_user(db: Session, user_id: int) -> User | None:
    user = db.get(User, user_id)
    if user and user.is_active:
        return user
    return None


def get_optional_user(request: Request, db: Session) -> User | None:
    """User from the signed session cookie, if present and valid."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return _load_active_user(db, int(user_id))


def require_user(request: Request, db: DbSession) -> User:
    user = get_optional_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(require_user)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def get_api_user(
    request: Request,
    db: DbSession,
    token: BearerToken = None,
) -> User:
    """Authenticate an API call via bearer token, falling back to the session.

    The fallback lets the same JSON endpoints be used by the server-rendered UI
    without duplicating routes.
    """
    if token:
        try:
            payload = decode_token(token, expected_type="access")
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user = db.scalar(select(User).where(User.username == payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists or is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    user = get_optional_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


ApiUser = Annotated[User, Depends(get_api_user)]


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "is_admin": user.is_admin,
    }
