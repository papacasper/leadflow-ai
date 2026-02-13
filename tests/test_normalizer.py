"""Tests for lead normalization functions."""

from leadflow.models import Lead
from leadflow.processing.normalizer import (
    normalize_company,
    normalize_email,
    normalize_lead,
    normalize_name,
    normalize_phone,
)


class TestNormalizeEmail:
    def test_lowercase(self):
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_strip_whitespace(self):
        assert normalize_email("  user@example.com  ") == "user@example.com"

    def test_combined(self):
        assert normalize_email("  USER@Example.COM  ") == "user@example.com"

    def test_empty(self):
        assert normalize_email("") == ""

    def test_already_clean(self):
        assert normalize_email("user@example.com") == "user@example.com"


class TestNormalizeName:
    def test_title_case(self):
        assert normalize_name("sarah chen") == "Sarah Chen"

    def test_all_caps(self):
        assert normalize_name("JAMES WRIGHT") == "James Wright"

    def test_collapse_whitespace(self):
        assert normalize_name("  marcus   JOHNSON  ") == "Marcus Johnson"

    def test_preserve_apostrophe(self):
        assert normalize_name("robert o'brien") == "Robert O'Brien"

    def test_empty(self):
        assert normalize_name("") == ""

    def test_single_name(self):
        assert normalize_name("madonna") == "Madonna"


class TestNormalizePhone:
    def test_strip_parens_and_dashes(self):
        assert normalize_phone("(555) 123-4567") == "5551234567"

    def test_preserve_plus(self):
        assert normalize_phone("+1-555-987-6543") == "+15559876543"

    def test_dots(self):
        assert normalize_phone("555.222.3333") == "5552223333"

    def test_spaces_and_parens(self):
        assert normalize_phone("+1 (555) 666-7777") == "+15556667777"

    def test_empty(self):
        assert normalize_phone("") == ""

    def test_already_digits(self):
        assert normalize_phone("5551234567") == "5551234567"


class TestNormalizeCompany:
    def test_strip_whitespace(self):
        assert normalize_company("  Blue Ridge  ") == "Blue Ridge"

    def test_collapse_spaces(self):
        assert normalize_company("Blue  Ridge   Design") == "Blue Ridge Design"

    def test_empty(self):
        assert normalize_company("") == ""


class TestNormalizeLead:
    def test_full_normalization(self):
        lead = Lead(
            name="  sarah CHEN  ",
            email="  SARAH@EXAMPLE.COM ",
            phone="(555) 123-4567",
            company="  Blue  Ridge  ",
            notes="  some notes  ",
        )
        result = normalize_lead(lead)

        assert result.name == "Sarah Chen"
        assert result.email == "sarah@example.com"
        assert result.phone == "5551234567"
        assert result.company == "Blue Ridge"
        assert result.notes == "some notes"

    def test_immutability(self):
        lead = Lead(name="sarah chen", email="SARAH@EXAMPLE.COM")
        result = normalize_lead(lead)
        # Original should be unchanged
        assert lead.name == "sarah chen"
        assert lead.email == "SARAH@EXAMPLE.COM"
        # Result should be normalized
        assert result.name == "Sarah Chen"
        assert result.email == "sarah@example.com"
