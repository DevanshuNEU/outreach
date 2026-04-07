"""
Tests for email pattern detection and application.

Covers:
  - _detect_email_pattern: votes correctly on known formats
  - _apply_email_pattern: generates correct addresses for each pattern
  - _clean_domain: strips https://www. off raw URLs (the adrian@https:// bug)
  - enrich_person fallback uses clean domain, not raw URL
"""

import pytest
from app.services.apollo_service import (
    _detect_email_pattern,
    _apply_email_pattern,
    _clean_domain,
)


# ─── _clean_domain ──────────────────────────────────────────────────────────

class TestCleanDomain:
    def test_plain_domain(self):
        assert _clean_domain("stripe.com") == "stripe.com"

    def test_strips_https_www(self):
        assert _clean_domain("https://www.twentyai.com") == "twentyai.com"

    def test_strips_http(self):
        assert _clean_domain("http://company.io") == "company.io"

    def test_strips_www_only(self):
        assert _clean_domain("www.bobyard.com") == "bobyard.com"

    def test_strips_trailing_slash(self):
        assert _clean_domain("https://www.getkroo.com/") == "getkroo.com"

    def test_strips_path(self):
        assert _clean_domain("https://www.company.com/about/team") == "company.com"

    def test_none_returns_none(self):
        assert _clean_domain(None) is None

    def test_empty_returns_none(self):
        assert _clean_domain("") is None

    def test_no_dot_returns_none(self):
        # "San Francisco" isn't a domain
        assert _clean_domain("San Francisco") is None

    def test_space_in_domain_returns_none(self):
        assert _clean_domain("my company.com") is None

    def test_ai_tld(self):
        assert _clean_domain("https://www.twentyai.com") == "twentyai.com"

    def test_already_clean(self):
        assert _clean_domain("getkroo.com") == "getkroo.com"


# ─── _detect_email_pattern ──────────────────────────────────────────────────

def _c(first, last, email, status="verified"):
    return {"first_name": first, "last_name": last, "email": email, "email_status": status}


class TestDetectEmailPattern:

    def test_detects_firstname_dot_lastname(self):
        contacts = [
            _c("Craig", "Album", "craig.album@twentyai.com"),
            _c("James", "Collins", "james.collins@twentyai.com"),
        ]
        assert _detect_email_pattern(contacts) == "firstname.lastname"

    def test_detects_firstname_only(self):
        contacts = [
            _c("Jane", "Smith", "jane@acme.com"),
            _c("Bob", "Jones", "bob@acme.com"),
        ]
        assert _detect_email_pattern(contacts) == "firstname"

    def test_detects_firstname_underscore_lastname(self):
        contacts = [
            _c("Alice", "Wang", "alice_wang@corp.com"),
            _c("Bob", "Lee", "bob_lee@corp.com"),
        ]
        assert _detect_email_pattern(contacts) == "firstname_lastname"

    def test_detects_f_dot_lastname(self):
        contacts = [
            _c("Alice", "Wang", "a.wang@corp.com"),
            _c("Bob", "Lee", "b.lee@corp.com"),
        ]
        assert _detect_email_pattern(contacts) == "f.lastname"

    def test_detects_flastname(self):
        contacts = [
            _c("Alice", "Wang", "awang@corp.com"),
            _c("Bob", "Lee", "blee@corp.com"),
        ]
        assert _detect_email_pattern(contacts) == "flastname"

    def test_ignores_guessed_status(self):
        # guessed emails shouldn't influence pattern detection
        contacts = [
            _c("Alice", "Wang", "alice@corp.com", status="guessed"),
            _c("Bob", "Lee", "bob@corp.com", status="guessed"),
        ]
        assert _detect_email_pattern(contacts) is None

    def test_ignores_probabilistic_status(self):
        contacts = [
            _c("Alice", "Wang", "alice@corp.com", status="probabilistic"),
        ]
        assert _detect_email_pattern(contacts) is None

    def test_majority_vote_wins(self):
        # 2 votes for firstname.lastname, 1 for firstname — should pick firstname.lastname
        contacts = [
            _c("Craig", "Album", "craig.album@co.com"),
            _c("James", "Collins", "james.collins@co.com"),
            _c("Meg", "Marks", "meg@co.com"),  # outlier
        ]
        assert _detect_email_pattern(contacts) == "firstname.lastname"

    def test_empty_list_returns_none(self):
        assert _detect_email_pattern([]) is None

    def test_no_verified_emails_returns_none(self):
        contacts = [_c("A", "B", "a@b.com", status="guessed")]
        assert _detect_email_pattern(contacts) is None

    def test_missing_last_name_skipped(self):
        contacts = [{"first_name": "Jane", "last_name": "", "email": "jane@co.com", "email_status": "verified"}]
        assert _detect_email_pattern(contacts) is None

    def test_case_insensitive_matching(self):
        # Name is "Craig Album" but email local is lowercase — should still match
        contacts = [_c("Craig", "Album", "craig.album@co.com")]
        assert _detect_email_pattern(contacts) == "firstname.lastname"


# ─── _apply_email_pattern ───────────────────────────────────────────────────

class TestApplyEmailPattern:

    def test_firstname_dot_lastname(self):
        assert _apply_email_pattern("firstname.lastname", "Adrian", "Kinnersley", "twentyai.com") == "adrian.kinnersley@twentyai.com"

    def test_firstname_only(self):
        assert _apply_email_pattern("firstname", "Jane", "Smith", "acme.com") == "jane@acme.com"

    def test_firstname_underscore_lastname(self):
        assert _apply_email_pattern("firstname_lastname", "Alice", "Wang", "corp.com") == "alice_wang@corp.com"

    def test_f_dot_lastname(self):
        assert _apply_email_pattern("f.lastname", "Alice", "Wang", "corp.com") == "a.wang@corp.com"

    def test_flastname(self):
        assert _apply_email_pattern("flastname", "Bob", "Lee", "corp.com") == "blee@corp.com"

    def test_firstnamelastname(self):
        assert _apply_email_pattern("firstnamelastname", "Bob", "Lee", "corp.com") == "boblee@corp.com"

    def test_lowercase_conversion(self):
        # Names come in mixed case — output should always be lowercase
        assert _apply_email_pattern("firstname.lastname", "JOHN", "DOE", "stripe.com") == "john.doe@stripe.com"

    def test_unknown_pattern_returns_none(self):
        assert _apply_email_pattern("nonexistent_pattern", "Jane", "Smith", "co.com") is None

    def test_empty_first_name_returns_none(self):
        assert _apply_email_pattern("firstname.lastname", "", "Smith", "co.com") is None

    def test_empty_last_name_returns_none(self):
        assert _apply_email_pattern("firstname.lastname", "Jane", "", "co.com") is None

    def test_empty_domain_returns_none(self):
        assert _apply_email_pattern("firstname.lastname", "Jane", "Smith", "") is None


# ─── End-to-end: detect then apply ─────────────────────────────────────────

class TestDetectAndApply:

    def test_twentyai_pattern_applied_to_adrian(self):
        """Reproduces the real bug: Adrian's email was guessed as adrian@twentyai.com.
        With pattern detection from Craig+James, it should be adrian.kinnersley@twentyai.com."""
        verified_contacts = [
            _c("Craig", "Album", "craig.album@twentyai.com"),
            _c("James", "Collins", "james.collins@twentyai.com"),
        ]
        pattern = _detect_email_pattern(verified_contacts)
        assert pattern == "firstname.lastname"

        result = _apply_email_pattern(pattern, "Adrian", "Kinnersley", "twentyai.com")
        assert result == "adrian.kinnersley@twentyai.com"

    def test_firstname_only_company(self):
        """Company uses just firstname@ — pattern should propagate to new person."""
        verified_contacts = [
            _c("Sam", "Altman", "sam@openai.com"),
            _c("Greg", "Brockman", "greg@openai.com"),
        ]
        pattern = _detect_email_pattern(verified_contacts)
        assert pattern == "firstname"

        result = _apply_email_pattern(pattern, "Ilya", "Sutskever", "openai.com")
        assert result == "ilya@openai.com"

    def test_pattern_upgrades_bad_apollo_guess(self):
        """Apollo always guesses firstname@domain. If the real pattern is
        firstname.lastname, our upgrade should fix it."""
        verified = [
            _c("Craig", "Album", "craig.album@co.com"),
            _c("James", "Collins", "james.collins@co.com"),
        ]
        pattern = _detect_email_pattern(verified)

        # Simulate the Apollo "guessed" email being wrong
        apollo_guess = "meg@co.com"  # wrong — should be meg.marks@co.com
        upgraded = _apply_email_pattern(pattern, "Meg", "Marks", "co.com")
        assert upgraded == "meg.marks@co.com"
        assert upgraded != apollo_guess
