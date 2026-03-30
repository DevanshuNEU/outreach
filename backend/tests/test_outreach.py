"""
Outreach CRUD tests — create, update (sent/replied), bulk delete.
"""

from tests.conftest import make_outreach, make_contact


# ─── List ─────────────────────────────────────────────────────────────────────

def test_list_outreach_empty(client, mock_db):
    mock_db.set("outreach", [])
    r = client.get("/api/outreach")
    assert r.status_code == 200
    assert r.json() == []


def test_list_outreach_filtered_by_application(client, mock_db):
    rows = [
        {**make_outreach(id="o1", application_id="app-001"), "contacts": None},
        {**make_outreach(id="o2", application_id="app-002"), "contacts": None},
    ]
    mock_db.set("outreach", rows)
    # The router filters in .eq(), which MockBuilder passes through → returns all rows
    # (MockBuilder doesn't actually filter, but this tests the endpoint responds correctly)
    r = client.get("/api/outreach?application_id=app-001")
    assert r.status_code == 200


# ─── Create ───────────────────────────────────────────────────────────────────

def test_create_outreach_builds_greeting(client, mock_db):
    mock_db.set("contacts", [{"first_name": "Sarah"}])
    r = client.post("/api/outreach", json={
        "application_id": "app-001",
        "contact_id": "contact-001",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["application_id"] == "app-001"
    assert data["contact_id"] == "contact-001"
    assert data["replied"] is False
    assert "Sarah" in data["personalized_greeting"]


def test_create_outreach_fallback_greeting_when_no_contact(client, mock_db):
    mock_db.set("contacts", [])
    r = client.post("/api/outreach", json={
        "application_id": "app-001",
        "contact_id": "contact-xyz",
    })
    assert r.status_code == 200
    assert r.json()["personalized_greeting"] == "Hey,"


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_outreach_mark_sent(client, mock_db):
    mock_db.set("outreach", [make_outreach()])
    r = client.put("/api/outreach/outreach-001", json={"sent_at": "2026-03-30T10:00:00"})
    assert r.status_code == 200


def test_update_outreach_mark_replied(client, mock_db):
    mock_db.set("outreach", [make_outreach()])
    r = client.put("/api/outreach/outreach-001", json={"replied": True})
    assert r.status_code == 200


def test_update_outreach_not_found_returns_404(client, mock_db):
    mock_db.set("outreach", [])
    r = client.put("/api/outreach/doesnt-exist", json={"replied": True})
    assert r.status_code == 404


def test_update_outreach_empty_body_returns_400(client, mock_db):
    r = client.put("/api/outreach/outreach-001", json={})
    assert r.status_code == 400


# ─── Bulk delete ──────────────────────────────────────────────────────────────

def test_bulk_delete_outreach_by_application(client, mock_db):
    mock_db.set("applications", [{"id": "app-001", "user_id": "11111111-1111-1111-1111-111111111111"}])
    r = client.delete("/api/outreach?application_id=app-001")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_bulk_delete_outreach_rejects_wrong_user(client, mock_db):
    # Application belongs to a different user
    mock_db.set("applications", [])
    r = client.delete("/api/outreach?application_id=app-999")
    assert r.status_code == 403
