"""
Applications CRUD + contact_count aggregation tests.
"""

from tests.conftest import make_app, make_outreach


# ─── List ─────────────────────────────────────────────────────────────────────

def test_list_applications_empty(client, mock_db):
    mock_db.set("applications", [])
    r = client.get("/api/applications")
    assert r.status_code == 200
    assert r.json() == []


def test_list_applications_returns_data(client, mock_db):
    mock_db.set("applications", [make_app()])
    mock_db.set("outreach", [])
    r = client.get("/api/applications")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == "app-001"
    assert data[0]["status"] == "drafting"


def test_list_applications_aggregates_contact_count(client, mock_db):
    mock_db.set("applications", [make_app()])
    mock_db.set("outreach", [
        {"application_id": "app-001"},
        {"application_id": "app-001"},
        {"application_id": "app-001"},
    ])
    r = client.get("/api/applications")
    assert r.status_code == 200
    assert r.json()[0]["contact_count"] == 3


def test_list_applications_status_filter(client, mock_db):
    mock_db.set("applications", [make_app(status="replied")])
    mock_db.set("outreach", [])
    r = client.get("/api/applications?status=replied")
    assert r.status_code == 200
    assert r.json()[0]["status"] == "replied"


# ─── Create ───────────────────────────────────────────────────────────────────

def test_create_application_sets_defaults(client, mock_db):
    r = client.post("/api/applications", json={"company_id": "company-001"})
    assert r.status_code == 200
    data = r.json()
    assert data["company_id"] == "company-001"
    assert data["email_status"] == "draft"
    assert data["status"] == "drafting"
    assert data["user_id"] == "11111111-1111-1111-1111-111111111111"


def test_create_application_with_job_details(client, mock_db):
    r = client.post("/api/applications", json={
        "company_id": "company-001",
        "job_title": "Backend Engineer",
        "job_description": "Build APIs",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["job_title"] == "Backend Engineer"
    assert data["job_description"] == "Build APIs"


# ─── Get single ───────────────────────────────────────────────────────────────

def test_get_application_returns_correct_app(client, mock_db):
    mock_db.set("applications", [make_app()])
    r = client.get("/api/applications/app-001")
    assert r.status_code == 200
    assert r.json()["id"] == "app-001"


def test_get_application_not_found_returns_404(client, mock_db):
    mock_db.set("applications", [])
    r = client.get("/api/applications/doesnt-exist")
    assert r.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_application_status(client, mock_db):
    mock_db.set("applications", [make_app(status="replied")])
    r = client.put("/api/applications/app-001", json={"status": "replied"})
    assert r.status_code == 200
    assert r.json()["status"] == "replied"


def test_update_application_saves_linkedin_note(client, mock_db):
    note = "Saw your RAG work — sent you an email. Devanshu"
    mock_db.set("applications", [make_app(linkedin_note=note)])
    r = client.put("/api/applications/app-001", json={"linkedin_note": note})
    assert r.status_code == 200
    assert r.json()["linkedin_note"] == note


def test_update_application_empty_body_returns_400(client, mock_db):
    r = client.put("/api/applications/app-001", json={})
    assert r.status_code == 400


def test_update_application_not_found_returns_404(client, mock_db):
    mock_db.set("applications", [])
    r = client.put("/api/applications/app-001", json={"status": "replied"})
    assert r.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_application_returns_ok(client, mock_db):
    r = client.delete("/api/applications/app-001")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
