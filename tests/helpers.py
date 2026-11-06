"""Small helpers shared by tests."""

from __future__ import annotations

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secret123"


def create_document(
    client,
    *,
    document_no: str = "DOC-001",
    divisions: list[str] | None = None,
    payload: bytes = b"%PDF-1.4 test document",
):
    return client.post(
        "/api/documents",
        data={
            "document_no": document_no,
            "document_type": "Technical report",
            "subject": "Test subject",
            "description": "Test description",
            "model_tv": "2T-TEST",
            "distributed_to": divisions or ["Marketing"],
        },
        files={"file": ("test.pdf", payload, "application/pdf")},
    )


def create_recipient(client, *, email: str = "marketing@example.com", division: str = "Marketing", category: str = "Direct"):
    return client.post(
        "/api/recipients",
        json={"email": email, "name": "Marketing Team", "division": division, "category": category},
    )


def login(client, username: str = "admin", password: str = "secret123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
