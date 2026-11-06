"""Authentication and authorisation behaviour."""

from __future__ import annotations

from tests.helpers import ADMIN_PASSWORD, ADMIN_USERNAME, login


def test_root_redirects_to_dashboard(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app"


def test_dashboard_requires_login(client):
    response = client.get("/app", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_login_sets_session_and_renders_dashboard(client, admin):
    response = login(client)
    assert response.status_code == 303
    assert response.headers["location"] == "/app"

    dashboard = client.get("/app")
    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text
    assert "Ada Admin" in dashboard.text


def test_login_rejects_bad_password(client, admin):
    response = client.post(
        "/login",
        data={"username": ADMIN_USERNAME, "password": "wrong-password"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.text


def test_logout_clears_session(client, admin):
    login(client)
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    dashboard = client.get("/app", follow_redirects=False)
    assert dashboard.status_code == 303


def test_token_endpoint_and_me(client, admin):
    response = client.post(
        "/api/auth/token",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    tokens = response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == ADMIN_USERNAME

    refresh = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_api_requires_token_or_session(client, admin):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/documents").status_code == 401

    login(client)
    assert client.get("/api/documents").status_code == 200


def test_bootstrap_registration_creates_admin(client, db):
    page = client.get("/register")
    assert page.status_code == 200

    response = client.post(
        "/register",
        data={
            "username": "first",
            "password": "firstpass",
            "email": "first@example.com",
            "firstname": "First",
            "lastname": "User",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text

    from app.db.models import User

    created = db.query(User).filter(User.username == "first").one()
    assert created.is_admin is True


def test_users_page_is_admin_only(client, user):
    login(client, username="member", password="member123")
    assert client.get("/app/users").status_code == 403
    assert client.get("/app").status_code == 200
