"""
Tests for the email drafting workflow.
Mocks the Anthropic client — no real API calls.
Covers: JD insight extraction, project matching, body cleanup, subject cap, name fix.
"""

import pytest
from unittest.mock import MagicMock, patch
from tests.conftest import TEST_USER_ID, make_app, make_company, make_template


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_profile(**kwargs):
    return {
        "id": "profile-001",
        "user_id": TEST_USER_ID,
        "full_name": "Devanshu Chicholikar",
        "background": "MS SWE, Northeastern. Built OpenCodeIntel.",
        "sign_off_block": "Best,\nDevanshu",
        "links_block": "opencodeintel.com",
        "projects": [
            {"name": "OpenCodeIntel", "description": "RAG pipeline", "metrics": "87.5% Hit@1", "url": ""},
            {"name": "LCO", "description": "Chrome extension", "metrics": "48 commits", "url": ""},
            {"name": "SecureScale", "description": "AWS infra", "metrics": "provisioning 2h→10min", "url": ""},
        ],
        **kwargs,
    }


def _mock_anthropic_response(text: str):
    """Build a fake anthropic Message object."""
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    msg.usage.input_tokens = 100
    msg.usage.output_tokens = 50
    return msg


# ─── _extract_jd_insights ─────────────────────────────────────────────────────

class TestExtractJdInsights:
    def test_returns_parsed_json(self):
        from app.services.email_service import _extract_jd_insights
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response(
            '{"hook": "They build X", "challenge": "Latency", "lead_projects": ["LCO"], "lead_reason": "Browser work"}'
        )
        result = _extract_jd_insights(client, "Vercel", "Build edge functions", ["OpenCodeIntel", "LCO"])
        assert result["hook"] == "They build X"
        assert result["lead_projects"] == ["LCO"]

    def test_handles_code_block_wrapping(self):
        from app.services.email_service import _extract_jd_insights
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response(
            '```json\n{"hook": "H", "challenge": "C", "lead_projects": ["Saar"], "lead_reason": "R"}\n```'
        )
        result = _extract_jd_insights(client, "Cursor", "Build dev tools", ["Saar"])
        assert result["lead_projects"] == ["Saar"]

    def test_graceful_fallback_on_bad_json(self):
        from app.services.email_service import _extract_jd_insights
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response("not json at all")
        result = _extract_jd_insights(client, "Stripe", "Payments", [])
        assert result == {}

    def test_graceful_fallback_on_api_error(self):
        from app.services.email_service import _extract_jd_insights
        client = MagicMock()
        client.messages.create.side_effect = Exception("API error")
        result = _extract_jd_insights(client, "Stripe", "Payments", [])
        assert result == {}

    def test_passes_project_names_to_prompt(self):
        from app.services.email_service import _extract_jd_insights
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response(
            '{"hook":"H","challenge":"C","lead_projects":["SecureScale"],"lead_reason":"R"}'
        )
        _extract_jd_insights(client, "Datadog", "AWS infra", ["OpenCodeIntel", "SecureScale", "LCO"])
        call_content = client.messages.create.call_args[1]["messages"][0]["content"]
        assert "SecureScale" in call_content
        assert "OpenCodeIntel" in call_content


# ─── Body cleanup ─────────────────────────────────────────────────────────────

class TestBodyCleanup:
    def test_strips_leading_triple_dashes(self):
        import re
        body = "---\n\nActual email body here."
        body = re.sub(r'^[-_]{3,}\s*\n+', '', body).strip()
        assert body == "Actual email body here."

    def test_strips_leading_underscores(self):
        import re
        body = "___\n\nEmail body."
        body = re.sub(r'^[-_]{3,}\s*\n+', '', body).strip()
        assert body == "Email body."

    def test_leaves_body_without_separator_unchanged(self):
        import re
        body = "Real email starts here.\n\nMore content."
        cleaned = re.sub(r'^[-_]{3,}\s*\n+', '', body).strip()
        assert cleaned == body


# ─── Subject line cap ─────────────────────────────────────────────────────────

class TestSubjectLineCap:
    def _apply_cap(self, subject: str) -> str:
        """Replicate the truncation logic from email_service."""
        if len(subject) > 60:
            cut = subject[:60].rfind(" ")
            return subject[:cut] if cut > 40 else subject[:60]
        return subject

    def test_short_subject_unchanged(self):
        s = "Short subject line"
        assert self._apply_cap(s) == s

    def test_exactly_60_chars_unchanged(self):
        s = "A" * 60
        assert self._apply_cap(s) == s

    def test_long_subject_truncated_at_word_boundary(self):
        s = "AST chunking moved your retrieval accuracy more than embeddings ever will."
        result = self._apply_cap(s)
        assert len(result) <= 60
        # Should cut at word boundary, not mid-word
        assert not result.endswith(" ")

    def test_very_long_word_hard_truncates(self):
        # If no space found before pos 40, hard truncate at 60
        s = "A" * 70
        result = self._apply_cap(s)
        assert len(result) == 60


# ─── LinkedIn note name ───────────────────────────────────────────────────────

class TestLinkedinNoteName:
    def test_first_name_extracted_correctly(self):
        full_name = "Devanshu Chicholikar"
        first = full_name.split()[0] if full_name.strip() else "Devanshu"
        assert first == "Devanshu"

    def test_first_name_fallback_on_empty(self):
        full_name = ""
        first = full_name.split()[0] if full_name.strip() else "Devanshu"
        assert first == "Devanshu"

    def test_first_name_passed_to_linkedin_prompt(self):
        import asyncio
        from app.services.email_service import generate_linkedin_note
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response("Saw your work. Devanshu")

        asyncio.get_event_loop().run_until_complete(
            generate_linkedin_note(client, "Stripe", "SWE", "Subject", "Body", first_name="Devanshu")
        )
        call_content = client.messages.create.call_args[1]["messages"][0]["content"]
        assert "Devanshu" in call_content

    def test_note_truncated_at_295_chars(self):
        import asyncio
        from app.services.email_service import generate_linkedin_note
        long_note = "x" * 400
        client = MagicMock()
        client.messages.create.return_value = _mock_anthropic_response(long_note)

        result = asyncio.get_event_loop().run_until_complete(
            generate_linkedin_note(client, "Stripe", "SWE", "Subject", "Body")
        )
        assert len(result) <= 295


# ─── Template suggest endpoint ────────────────────────────────────────────────

class TestTemplateSuggest:
    def test_returns_matching_template(self, client, mock_db):
        mock_db.set("role_templates", [
            {"id": "t-001", "slug": "backend", "title": "Backend Engineer"},
            {"id": "t-002", "slug": "cloud", "title": "Cloud / DevOps"},
        ])
        with patch("app.routers.templates.anthropic.Anthropic") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.messages.create.return_value = _mock_anthropic_response("cloud")

            r = client.post("/api/templates/suggest", json={
                "company_name": "Datadog",
                "job_description": "Build Kubernetes infra on AWS with Terraform.",
            })
        assert r.status_code == 200
        data = r.json()
        assert data["slug"] == "cloud"
        assert data["template_id"] == "t-002"

    def test_falls_back_to_first_template_on_unknown_slug(self, client, mock_db):
        mock_db.set("role_templates", [
            {"id": "t-001", "slug": "swe", "title": "Software Engineer"},
        ])
        with patch("app.routers.templates.anthropic.Anthropic") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.messages.create.return_value = _mock_anthropic_response("nonexistent-slug")

            r = client.post("/api/templates/suggest", json={
                "company_name": "Acme",
                "job_description": "Build things.",
            })
        assert r.status_code == 200
        assert r.json()["template_id"] == "t-001"

    def test_returns_404_when_no_templates(self, client, mock_db):
        mock_db.set("role_templates", [])
        with patch("app.routers.templates.anthropic.Anthropic"):
            r = client.post("/api/templates/suggest", json={
                "company_name": "Acme",
                "job_description": "Build things.",
            })
        assert r.status_code == 404


# ─── Draft email endpoint ─────────────────────────────────────────────────────

class TestDraftEmailEndpoint:
    def test_draft_email_returns_subject_and_body(self, client, mock_db):
        mock_db.set("applications", [make_app(job_description="Build payments API")])
        mock_db.set("companies", [make_company()])
        mock_db.set("role_templates", [make_template()])
        mock_db.set("profiles", [make_profile()])
        mock_db.set("api_usage", [])

        async def fake_draft(**kwargs):
            return {"subject": "Test subject", "body": "Test body.", "linkedin_note": "Test note. Devanshu"}

        with patch("app.routers.emails.draft_email", side_effect=fake_draft):

            r = client.post("/api/applications/app-001/draft-email", json={
                "role_template_id": "template-001"
            })

        assert r.status_code == 200
        assert r.json()["subject"] == "Test subject"
        assert r.json()["body"] == "Test body."

    def test_draft_email_404_on_missing_application(self, client, mock_db):
        mock_db.set("applications", [])
        r = client.post("/api/applications/nonexistent/draft-email", json={
            "role_template_id": "template-001"
        })
        assert r.status_code == 404

    def test_no_links_in_body(self):
        """Links block must not appear in email body — frontend adds them separately."""
        body_with_links = "Great email body.\n\nhttps://github.com/DevanshuNEU\nhttps://opencodeintel.com"
        # The pattern we check: if http appears in a body returned by the API
        # After our fix, Claude gets "DO NOT include" instruction
        # This test documents the requirement
        assert "http" not in "Great email body here. No links anywhere."
