"""Document upload, listing, download and deletion."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.db.models import Document
from tests.helpers import create_document


def test_upload_list_and_download(logged_in_client, db):
    response = create_document(logged_in_client, document_no="DOC-100", payload=b"%PDF-1.7 hello")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["document_no"] == "DOC-100"
    assert body["distributed_to"] == ["Marketing"]
    assert body["uploader"] == "Ada Admin"
    assert body["file_size"] == len(b"%PDF-1.7 hello")

    stored = Path(settings.storage_dir) / db.query(Document).one().stored_filename
    assert stored.exists()

    numbers = logged_in_client.get("/api/documents/numbers")
    assert numbers.json()["items"] == ["DOC-100"]

    listing = logged_in_client.get("/api/documents?page=1&page_size=5")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    detail = logged_in_client.get("/api/documents/DOC-100")
    assert detail.status_code == 200
    assert detail.json()["document_subject"] == "Test subject"

    download = logged_in_client.get("/app/documents/DOC-100/file")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.content == b"%PDF-1.7 hello"


def test_upload_via_bearer_token(client, admin):
    token = client.post(
        "/api/auth/token",
        data={"username": "admin", "password": "secret123"},
    ).json()["access_token"]

    response = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "document_no": "DOC-BEARER",
            "document_type": "ECN",
            "subject": "Bearer upload",
            "distributed_to": ["Production"],
        },
        files={"file": ("bearer.pdf", b"%PDF-1.4 bearer", "application/pdf")},
    )
    assert response.status_code == 201, response.text


def test_upload_rejects_duplicate_and_invalid_files(logged_in_client):
    assert create_document(logged_in_client, document_no="DOC-200").status_code == 201

    duplicate = create_document(logged_in_client, document_no="DOC-200")
    assert duplicate.status_code == 409

    not_pdf = create_document(logged_in_client, document_no="DOC-201", payload=b"plain text")
    assert not_pdf.status_code == 422
    assert "PDF" in not_pdf.json()["detail"]

    invalid_number = create_document(logged_in_client, document_no="../escape")
    assert invalid_number.status_code == 422


def test_upload_requires_destination(logged_in_client):
    response = create_document(logged_in_client, document_no="DOC-300", divisions=["Unknown Division"])
    assert response.status_code == 422


def test_delete_document_removes_file(logged_in_client, db):
    assert create_document(logged_in_client, document_no="DOC-400").status_code == 201
    stored = Path(settings.storage_dir) / db.query(Document).one().stored_filename
    assert stored.exists()

    response = logged_in_client.delete("/api/documents/DOC-400")
    assert response.status_code == 200
    assert not stored.exists()
    assert logged_in_client.get("/api/documents/DOC-400").status_code == 404


def test_documents_page_renders(logged_in_client):
    create_document(logged_in_client, document_no="DOC-500")
    page = logged_in_client.get("/app/documents")
    assert page.status_code == 200
    assert "DOC-500" in page.text
