"""Recipient API behaviour."""

from __future__ import annotations

from tests.helpers import create_recipient


def test_recipient_crud(logged_in_client):
    created = create_recipient(logged_in_client)
    assert created.status_code == 201, created.text
    recipient = created.json()
    assert recipient["division"] == "Marketing"
    assert recipient["category"] == "Direct"

    listing = logged_in_client.get("/api/recipients?page=1&page_size=10")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    duplicate = create_recipient(logged_in_client)
    assert duplicate.status_code == 409

    deleted = logged_in_client.delete(f"/api/recipients/{recipient['id']}")
    assert deleted.status_code == 200

    listing = logged_in_client.get("/api/recipients")
    assert listing.json()["total"] == 0


def test_recipient_validation(logged_in_client):
    invalid_email = logged_in_client.post(
        "/api/recipients",
        json={"email": "not-an-email", "name": "X", "division": "Marketing", "category": "Direct"},
    )
    assert invalid_email.status_code == 422

    invalid_division = create_recipient(logged_in_client, division="Unknown Division")
    assert invalid_division.status_code == 422


def test_recipients_page_and_form(logged_in_client):
    response = logged_in_client.post(
        "/app/recipients",
        data={"email": "line@example.com", "name": "QC Line", "division": "QC Line", "category": "CC"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/app/recipients"

    page = logged_in_client.get("/app/recipients")
    assert page.status_code == 200
    assert "line@example.com" in page.text
