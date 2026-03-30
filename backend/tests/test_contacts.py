"""
Contacts — manual contact creation test.
(Apollo find-contacts is tested separately with full mocks of httpx.)
"""

from tests.conftest import make_company, make_contact


def test_create_manual_contact(client, mock_db):
    mock_db.set("companies", [make_company()])
    r = client.post("/api/contacts/manual", json={
        "company_id": "company-001",
        "first_name": "Sarah",
        "last_name": "Connor",
        "title": "Engineering Manager",
        "email": "sarah@stripe.com",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["first_name"] == "Sarah"
    assert data["email"] == "sarah@stripe.com"
    assert data["email_status"] == "manual"


def test_create_manual_contact_requires_email(client, mock_db):
    # Missing email → Pydantic validation error → 422
    r = client.post("/api/contacts/manual", json={
        "company_id": "company-001",
        "first_name": "Sarah",
    })
    assert r.status_code == 422


def test_list_contacts_for_company(client, mock_db):
    mock_db.set("contacts", [make_contact(), make_contact(id="c2", email="bob@stripe.com")])
    r = client.get("/api/contacts?company_id=company-001")
    assert r.status_code == 200
    assert len(r.json()) == 2
