"""User persistence and authentication service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.db.models import User
from app.schemas.auth import UserCreate


def count_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User)) or 0


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.username)).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, payload: UserCreate) -> User:
    if get_user_by_username(db, payload.username):
        raise ConflictError(f"Username '{payload.username}' is already registered")

    user = User(
        username=payload.username,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        firstname=payload.firstname,
        lastname=payload.lastname,
        mail_password=payload.mail_password,
        is_admin=payload.is_admin,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # race between the check and the insert
        db.rollback()
        raise ConflictError(f"Username '{payload.username}' is already registered") from exc
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def set_password(db: Session, user_id: int, new_password: str) -> None:
    user = get_user(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    user.password_hash = hash_password(new_password)
    db.commit()
