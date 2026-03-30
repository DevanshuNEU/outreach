"""
Analytics endpoint tests.
"""

from tests.conftest import make_outreach, make_app, make_contact, make_company, make_template


def test_analytics_empty_data(client, mock_db):
    mock_db.set("outreach", [])
    mock_db.set("applications", [])
    mock_db.set("contacts", [])
    mock_db.set("companies", [])
    mock_db.set("role_templates", [])

    r = client.get("/api/analytics")
    assert r.status_code == 200
    data = r.json()

    assert data["totals"]["total_sent"] == 0
    assert data["totals"]["total_replied"] == 0
    assert data["totals"]["response_rate"] == 0
    assert data["by_company_size"] == []
    assert data["by_template"] == []
    assert data["time_to_reply"]["count"] == 0
    assert data["pipeline_funnel"] is not None


def test_analytics_returns_all_10_metrics(client, mock_db):
    mock_db.set("outreach", [
        make_outreach(
            id="o1",
            sent_at="2026-03-28T10:00:00+00:00",
            replied=True,
            reply_date="2026-03-29T10:00:00+00:00",
        ),
        make_outreach(
            id="o2",
            contact_id="contact-002",
            sent_at="2026-03-28T12:00:00+00:00",
            replied=False,
        ),
    ])
    mock_db.set("applications", [make_app()])
    mock_db.set("contacts", [
        make_contact(),
        make_contact(id="contact-002", seniority="director"),
    ])
    mock_db.set("companies", [make_company(employee_count=150)])
    mock_db.set("role_templates", [make_template()])

    r = client.get("/api/analytics")
    assert r.status_code == 200
    data = r.json()

    # All 10 metric keys present
    assert "by_company_size" in data
    assert "by_template" in data
    assert "by_seniority" in data
    assert "time_to_reply" in data
    assert "followup_effectiveness" in data
    assert "optimal_contacts" in data
    assert "weekly_activity" in data
    assert "best_day" in data
    assert "pipeline_funnel" in data
    assert "monthly_trends" in data
    assert "totals" in data

    # Totals are correct
    assert data["totals"]["total_sent"] == 2
    assert data["totals"]["total_replied"] == 1
    assert data["totals"]["response_rate"] == 50.0


def test_analytics_pipeline_funnel_counts(client, mock_db):
    mock_db.set("outreach", [])
    mock_db.set("applications", [
        make_app(id="a1", status="drafting"),
        make_app(id="a2", status="drafting"),
        make_app(id="a3", status="replied"),
    ])
    mock_db.set("contacts", [])
    mock_db.set("companies", [])
    mock_db.set("role_templates", [])

    r = client.get("/api/analytics")
    data = r.json()

    funnel = {f["stage"]: f["count"] for f in data["pipeline_funnel"]}
    assert funnel["Drafting"] == 2
    assert funnel["Replied"] == 1


def test_analytics_followup_effectiveness(client, mock_db):
    mock_db.set("outreach", [
        make_outreach(
            id="o1",
            sent_at="2026-03-20T10:00:00+00:00",
            followup_1_sent_at="2026-03-23T10:00:00+00:00",
            replied=True,
            reply_date="2026-03-24T10:00:00+00:00",
        ),
        make_outreach(
            id="o2",
            contact_id="c2",
            sent_at="2026-03-20T10:00:00+00:00",
            replied=True,
            reply_date="2026-03-21T10:00:00+00:00",
        ),
    ])
    mock_db.set("applications", [make_app()])
    mock_db.set("contacts", [make_contact()])
    mock_db.set("companies", [make_company()])
    mock_db.set("role_templates", [])

    r = client.get("/api/analytics")
    data = r.json()

    fu = {f["stage"]: f["replies"] for f in data["followup_effectiveness"]}
    assert fu["Followup 1"] == 1  # o1 replied after FU1
    assert fu["Initial"] == 1     # o2 replied without any follow-up
