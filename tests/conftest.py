"""Test fixtures: isolated SQLite database, storage directory and accounts."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="broadcast-tests-"))
os.environ.update(
    {
        "DATABASE_URL": f"sqlite:///{(_TEMP_ROOT / 'test.sqlite').as_posix()}",
        "STORAGE_DIR": str(_TEMP_ROOT / "storage"),
        "SECRET_KEY": "test-secret-key",
        "SESSION_SECRET_KEY": "test-session-secret",
        "SMTP_SENDER_EMAIL": "sender@example.com",
        "SMTP_SENDER_PASSWORD": "sender-password",
        "PUBLIC_BASE_URL": "http://testserver",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    }
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.db.base import SessionLocal, init_db
from app.db.models import Document, Recipient, User
from app.main import app
from tests.helpers import ADMIN_PASSWORD, ADMIN_USERNAME

init_db()



@pytest.fixture(scope="session", autouse=True)
def _cleanup_temp_root():
    yield
    shutil.rmtree(_TEMP_ROOT, ignore_errors=True)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with SessionLocal() as session:
        session.execute(delete(Document))
        session.execute(delete(Recipient))
        session.execute(delete(User))
        session.commit()

    storage = Path(os.environ["STORAGE_DIR"])
    shutil.rmtree(storage, ignore_errors=True)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin(db):
    user = User(
        username=ADMIN_USERNAME,
        email="admin@example.com",
        password_hash=hash_password(ADMIN_PASSWORD),
        firstname="Ada",
        lastname="Admin",
        is_admin=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user(db):
    account = User(
        username="member",
        email="member@example.com",
        password_hash=hash_password("member123"),
        is_admin=False,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def logged_in_client(client, admin):
    response = client.post(
        "/login",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    return client
