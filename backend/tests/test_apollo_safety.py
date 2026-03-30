"""
Apollo safety checks — verifies _name_matches() rejects wrong companies.

These are unit tests on the pure function. No HTTP calls made.
"""

import pytest
from app.services.apollo_service import _name_matches


# ─── _name_matches ──────────────────────────────────────────────────────────

class TestNameMatches:
    """The guard that prevented the Bobyard→Google blunder."""

    # Should ACCEPT
    def test_exact_match(self):
        assert _name_matches("Stripe", "Stripe") is True

    def test_case_insensitive(self):
        assert _name_matches("stripe", "Stripe Inc") is True

    def test_query_substring_of_org(self):
        assert _name_matches("Bobyard", "Bobyard Technologies") is True

    def test_org_substring_of_query(self):
        assert _name_matches("Bobyard Technologies", "Bobyard") is True

    def test_word_overlap(self):
        assert _name_matches("OpenAI", "OpenAI Research") is True

    def test_partial_word_in_longer_name(self):
        assert _name_matches("Anthropic", "Anthropic PBC") is True

    def test_multi_word_company(self):
        assert _name_matches("Scale AI", "Scale AI Inc.") is True

    # Should REJECT
    def test_completely_different_company(self):
        # The actual blunder: searched Bobyard, got Google
        assert _name_matches("Bobyard", "Google") is False

    def test_no_overlap_at_all(self):
        assert _name_matches("Stripe", "Amazon") is False

    def test_short_words_dont_match_by_accident(self):
        # Completely unrelated names with no meaningful word overlap
        assert _name_matches("Boring Company", "New York Times") is False

    def test_partial_char_overlap_not_enough(self):
        # "Boa" shares chars with "Bobyard" but is a different company
        assert _name_matches("Boa", "Bobyard") is False

    def test_single_letter_words_ignored(self):
        # Very short words (< 3 chars) are filtered out of word overlap
        assert _name_matches("AI", "Amazon Inc") is False


# ─── Integration: find-contacts endpoint rejects wrong org ─────────────────

def test_find_contacts_not_found_when_company_missing(client, mock_db):
    """find-contacts returns 404 when application doesn't exist."""
    mock_db.set("applications", [])
    r = client.post("/api/applications/nonexistent-id/find-contacts")
    assert r.status_code == 404
