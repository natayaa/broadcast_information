"""Broadcast orchestration with a stubbed SMTP layer."""

from __future__ import annotations

from tests.helpers import create_document, create_recipient


def _stub_mailer(monkeypatch):
    calls = []

    def fake_send_broadcast(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("app.services.mail.send_broadcast", fake_send_broadcast)
    return calls


def test_broadcast_sends_to_direct_and_cc(logged_in_client, monkeypatch):
    calls = _stub_mailer(monkeypatch)

    assert create_recipient(
        logged_in_client, email="direct@example.com", division="Marketing", category="Direct"
    ).status_code == 201
    assert create_recipient(
        logged_in_client, email="cc@example.com", division="Marketing", category="CC"
    ).status_code == 201
    assert create_document(logged_in_client, document_no="DOC-B1", divisions=["Marketing"]).status_code == 201

    response = logged_in_client.post(
        "/api/broadcast",
        json={"document_no": "DOC-B1", "server": "sharp"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["direct_recipients"] == 1
    assert body["cc_recipients"] == 1
    assert body["recipients"] == 2

    assert len(calls) == 1
    call = calls[0]
    assert call["to"] == ["direct@example.com"]
    assert call["cc"] == ["cc@example.com"]
    assert call["server_key"] == "sharp"
    assert "[Reminder]" in call["subject"]
    assert "http://testserver/app/documents/DOC-B1/file" in call["body"]

    detail = logged_in_client.get("/api/documents/DOC-B1").json()
    assert detail["last_broadcast_at"] is not None


def test_broadcast_without_direct_recipients_is_rejected(logged_in_client, monkeypatch):
    calls = _stub_mailer(monkeypatch)
    assert create_recipient(
        logged_in_client, email="cc-only@example.com", division="Marketing", category="CC"
    ).status_code == 201
    assert create_document(logged_in_client, document_no="DOC-B2", divisions=["Marketing"]).status_code == 201

    response = logged_in_client.post("/api/broadcast", json={"document_no": "DOC-B2", "server": "office"})
    assert response.status_code == 422
    assert "No direct recipients" in response.json()["detail"]
    assert calls == []


def test_broadcast_unknown_document(logged_in_client, monkeypatch):
    _stub_mailer(monkeypatch)
    response = logged_in_client.post("/api/broadcast", json={"document_no": "MISSING", "server": "sharp"})
    assert response.status_code == 404


def test_broadcast_requires_authentication(client, monkeypatch):
    _stub_mailer(monkeypatch)
    response = client.post("/api/broadcast", json={"document_no": "DOC", "server": "sharp"})
    assert response.status_code == 401
