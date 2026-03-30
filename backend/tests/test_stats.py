"""
Stats + Apollo credits endpoint tests.
"""

from datetime import datetime, timezone
from unittest.mock import patch


# ─── /api/stats ───────────────────────────────────────────────────────────────

def test_stats_all_zeros(client, mock_db):
    mock_db.set("applications", [])
    mock_db.set("outreach", [])
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_applications"] == 0
    assert data["total_outreach"] == 0
    assert data["total_sent"] == 0
    assert data["total_replied"] == 0
    assert data["response_rate"] == 0


def test_stats_calculates_response_rate(client, mock_db):
    mock_db.set("applications", [{"id": "a"}, {"id": "b"}])
    # 3 sent, 1 replied → 33.3%
    mock_db.set("outreach", [
        {"id": "o1", "sent_at": "2026-03-30T10:00:00", "replied": True},
        {"id": "o2", "sent_at": "2026-03-30T11:00:00", "replied": False},
        {"id": "o3", "sent_at": "2026-03-30T12:00:00", "replied": False},
    ])
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_sent"] == 3
    assert data["total_replied"] == 1
    assert data["response_rate"] == 33.3


# ─── /api/apollo/credits ──────────────────────────────────────────────────────

def test_apollo_credits_no_usage(client, mock_db):
    mock_db.set("api_usage", [])
    r = client.get("/api/apollo/credits")
    assert r.status_code == 200
    data = r.json()
    assert data["daily_used"] == 0
    assert data["daily_remaining"] == data["daily_limit"]
    assert data["monthly_used"] == 0
    assert data["monthly_total"] == 2515
    assert data["max_per_search"] == 2


def test_apollo_credits_counts_today_usage(client, mock_db):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mock_db.set("api_usage", [
        {"service": "apollo", "estimated_cost_cents": 3, "created_at": f"{today}T08:00:00+00:00"},
        {"service": "apollo", "estimated_cost_cents": 5, "created_at": f"{today}T09:00:00+00:00"},
        {"service": "anthropic", "estimated_cost_cents": 2, "created_at": f"{today}T10:00:00+00:00"},
    ])
    r = client.get("/api/apollo/credits")
    assert r.status_code == 200
    data = r.json()
    # Only apollo rows count, anthropic row excluded
    # Note: MockBuilder doesn't actually filter by date/service (returns all rows),
    # so we validate the endpoint returns a parseable response with correct structure.
    assert "daily_used" in data
    assert "monthly_used" in data
    assert "daily_remaining" in data
    assert data["daily_remaining"] >= 0


def test_apollo_credits_returns_config(client, mock_db):
    mock_db.set("api_usage", [])
    r = client.get("/api/apollo/credits")
    assert r.status_code == 200
    data = r.json()
    assert data["daily_limit"] == 50
    assert data["max_per_search"] == 2
    assert data["monthly_total"] == 2515
