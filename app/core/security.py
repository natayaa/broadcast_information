"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.config import settings

TokenType = Literal["access", "refresh"]


class InvalidTokenError(Exception):
    """Raised when a token is missing, malformed, expired or of the wrong type."""


def _password_bytes(password: str) -> bytes:
    # bcrypt only considers the first 72 bytes; truncate explicitly so the
    # library never raises on long passphrases.
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(subject: str, token_type: TokenType, expires_minutes: int, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, expires_minutes: int | None = None, extra: dict[str, Any] | None = None) -> str:
    return _create_token(
        subject,
        "access",
        expires_minutes or settings.access_token_expire_minutes,
        extra,
    )


def create_refresh_token(subject: str, expires_minutes: int | None = None) -> str:
    return _create_token(subject, "refresh", expires_minutes or settings.refresh_token_expire_minutes)


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # expired, bad signature, malformed...
        raise InvalidTokenError("Invalid or expired token") from exc

    if expected_type and payload.get("type") != expected_type:
        raise InvalidTokenError("Unexpected token type")
    if not payload.get("sub"):
        raise InvalidTokenError("Token is missing a subject")
    return payload
