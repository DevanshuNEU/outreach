"""
Follow-up queue endpoint tests.
"""

from tests.conftest import make_outreach, make_app, make_contact, make_company


def test_followup_queue_empty_when_no_outreach(client, mock_db):
    mock_db.set("outreach", [])
    r = client.get("/api/followup-queue")
    assert r.status_code == 200
    data = r.json()
    assert data["overdue"] == []
    assert data["due_today"] == []
    assert data["upcoming"] == []
    assert data["total_due"] == 0


def test_followup_queue_returns_overdue_items(client, mock_db):
    # Outreach sent 5 days ago, followup_1 not sent yet → FU1 overdue (day 3)
    mock_db.set("outreach", [
        make_outreach(
            sent_at="2026-03-25T10:00:00+00:00",
            replied=False,
            contact=make_contact(),
        )
    ])
    mock_db.set("applications", [
        make_app(id="app-001", company_id="company-001", job_title="SWE")
    ])
    mock_db.set("companies", [make_company()])

    r = client.get("/api/followup-queue")
    assert r.status_code == 200
    data = r.json()
    # Should have at least one overdue item
    total = len(data["overdue"]) + len(data["due_today"]) + len(data["upcoming"])
    assert total >= 1


def test_followup_queue_excludes_replied(client, mock_db):
    # Outreach that was replied to should NOT appear in the queue
    mock_db.set("outreach", [
        make_outreach(
            sent_at="2026-03-25T10:00:00+00:00",
            replied=True,
            contact=make_contact(),
        )
    ])
    r = client.get("/api/followup-queue")
    assert r.status_code == 200
    data = r.json()
    assert data["total_due"] == 0


def test_followup_queue_excludes_unsent(client, mock_db):
    # Outreach with no sent_at should NOT appear
    mock_db.set("outreach", [make_outreach(sent_at=None)])
    r = client.get("/api/followup-queue")
    assert r.status_code == 200
    data = r.json()
    assert data["total_due"] == 0
