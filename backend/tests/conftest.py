"""
Shared fixtures for all backend tests.

Key insight: router endpoints call get_db() directly (not via FastAPI Depends),
so dependency_overrides doesn't work. Instead, we monkeypatch the get_db name
in each router module so the patched version is called during tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.deps import get_current_user

# ─── Test identity ─────────────────────────────────────────────────────────────

TEST_USER_ID = "11111111-1111-1111-1111-111111111111"
TEST_USER = {"id": TEST_USER_ID, "username": "testuser"}


# ─── Supabase mock ─────────────────────────────────────────────────────────────

class MockBuilder:
    """
    Mimics Supabase's fluent chained query builder.

    All filter/order methods return self so chains like:
      db.table("x").select("*").eq("id", v).order("created_at").execute()
    all call the same execute() which returns the pre-configured data.

    Special mutations:
      insert(data)  → new builder whose execute() returns [data]
      delete()      → new builder whose execute() returns []
      update(data)  → returns self (execute returns current table data)
    """

    def __init__(self, data=None):
        self._data = list(data) if data else []

    # ── filters (return self) ─────────────────────────────────────────────────
    def select(self, *a, **kw): return self
    def eq(self, *a, **kw): return self
    def neq(self, *a, **kw): return self
    def in_(self, *a, **kw): return self
    def not_(self, *a, **kw): return self
    def order(self, *a, **kw): return self
    def limit(self, *a, **kw): return self
    def offset(self, *a, **kw): return self
    def gte(self, *a, **kw): return self
    def lte(self, *a, **kw): return self

    # ── mutations ─────────────────────────────────────────────────────────────
    def insert(self, data):
        items = [data] if isinstance(data, dict) else list(data)
        return MockBuilder(items)

    def update(self, data):
        return self  # execute() returns current _data

    def delete(self):
        return MockBuilder([])

    # ── terminal ──────────────────────────────────────────────────────────────
    def execute(self):
        class _R:
            pass
        r = _R()
        r.data = self._data
        r.count = len(self._data)
        return r


class MockDB:
    """
    Configurable mock Supabase client.

    Usage in tests:
        mock_db.set("applications", [make_app()])
        mock_db.set("outreach", [])
    """

    def __init__(self):
        self._tables: dict[str, list] = {}

    def set(self, name: str, data: list) -> "MockDB":
        self._tables[name] = data
        return self

    def table(self, name: str) -> MockBuilder:
        return MockBuilder(self._tables.get(name, []))


# ─── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture(autouse=True)
def _patch_get_db(mock_db, monkeypatch):
    """
    Patch get_db() in every router module so no real Supabase connection is made.
    This is autouse=True so it applies to ALL tests automatically.
    """
    import app.routers.applications
    import app.routers.outreach
    import app.routers.companies
    import app.routers.contacts
    import app.routers.stats
    import app.routers.profiles
    import app.routers.templates
    import app.routers.emails
    import app.auth.router as _auth_router

    _db = mock_db  # capture reference

    for mod in [
        app.routers.applications,
        app.routers.outreach,
        app.routers.companies,
        app.routers.contacts,
        app.routers.stats,
        app.routers.profiles,
        app.routers.templates,
        app.routers.emails,
        _auth_router,
    ]:
        if hasattr(mod, "get_db"):
            monkeypatch.setattr(mod, "get_db", lambda db=_db: db)


@pytest.fixture
def client(mock_db):
    """Authenticated client — get_current_user bypassed, get_db mocked."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def raw_client():
    """
    Client with NO dependency overrides.
    Used for auth tests that need the real get_current_user logic.
    get_db is still patched via the autouse _patch_get_db fixture.
    """
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Test-data factories ───────────────────────────────────────────────────────

def make_app(**kwargs):
    return {
        "id": "app-001",
        "user_id": TEST_USER_ID,
        "company_id": "company-001",
        "role_template_id": None,
        "job_title": "Software Engineer",
        "job_description": "Write great software",
        "email_subject": "Let's talk",
        "email_body": "I built things.",
        "email_status": "draft",
        "status": "drafting",
        "notes": None,
        "linkedin_note": None,
        "contact_count": 0,
        "created_at": "2026-03-30T00:00:00",
        "updated_at": "2026-03-30T00:00:00",
        **kwargs,
    }


def make_company(**kwargs):
    return {
        "id": "company-001",
        "name": "Stripe",
        "domain": "stripe.com",
        "location": "San Francisco, CA",
        "apollo_org_id": None,
        "employee_count": None,
        "industry": None,
        "website": None,
        **kwargs,
    }


def make_outreach(**kwargs):
    return {
        "id": "outreach-001",
        "application_id": "app-001",
        "contact_id": "contact-001",
        "user_id": TEST_USER_ID,
        "personalized_greeting": "Hey John,",
        "sent_at": None,
        "followup_1_sent_at": None,
        "followup_2_sent_at": None,
        "replied": False,
        "reply_date": None,
        "notes": None,
        "created_at": "2026-03-30T00:00:00",
        "contact": None,
        **kwargs,
    }


def make_contact(**kwargs):
    return {
        "id": "contact-001",
        "company_id": "company-001",
        "apollo_person_id": None,
        "first_name": "John",
        "last_name": "Doe",
        "title": "Engineering Manager",
        "seniority": "manager",
        "email": "john@stripe.com",
        "email_status": "verified",
        "linkedin_url": None,
        **kwargs,
    }


def make_template(**kwargs):
    return {
        "id": "template-001",
        "user_id": TEST_USER_ID,
        "slug": "swe",
        "title": "Software Engineer",
        "color": "#3b82f6",
        "tagline": "Eval framework first.",
        "system_prompt": "",
        "role_prompt_addition": "ROLE: SWE",
        "example_email": None,
        "sort_order": 0,
        **kwargs,
    }
