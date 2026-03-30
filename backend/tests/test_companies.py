"""
Companies — create (with dedup) and list tests.
"""

from tests.conftest import make_company


def test_list_companies_empty(client, mock_db):
    mock_db.set("companies", [])
    r = client.get("/api/companies")
    assert r.status_code == 200
    assert r.json() == []


def test_list_companies_returns_all(client, mock_db):
    mock_db.set("companies", [make_company(), make_company(id="company-002", name="Notion")])
    r = client.get("/api/companies")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_create_company_new(client, mock_db):
    mock_db.set("companies", [])  # no existing company → insert path
    r = client.post("/api/companies", json={"name": "Stripe", "location": "San Francisco, CA"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Stripe"


def test_create_company_dedup_returns_existing(client, mock_db):
    existing = make_company()
    mock_db.set("companies", [existing])  # company already exists
    r = client.post("/api/companies", json={"name": "Stripe", "location": "San Francisco, CA"})
    assert r.status_code == 200
    assert r.json()["id"] == "company-001"  # returned existing, not new
