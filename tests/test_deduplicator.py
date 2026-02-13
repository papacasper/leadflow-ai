"""Tests for the deduplication module."""

from leadflow.models import Lead
from leadflow.processing.deduplicator import Deduplicator
from leadflow.processing.normalizer import normalize_lead


class TestExactDedup:
    def test_exact_email_phone_match(self, mock_config):
        dedup = Deduplicator(mock_config)
        lead_a = Lead(name="Sarah Chen", email="sarah@example.com", phone="5551234567")
        lead_b = Lead(name="Sarah Chen", email="sarah@example.com", phone="5551234567")
        unique, dups = dedup.deduplicate([lead_a, lead_b])
        assert len(unique) == 1
        assert len(dups) == 1

    def test_no_duplicates(self, mock_config):
        dedup = Deduplicator(mock_config)
        lead_a = Lead(name="Alice", email="alice@example.com", phone="1111111111")
        lead_b = Lead(name="Bob", email="bob@example.com", phone="2222222222")
        unique, dups = dedup.deduplicate([lead_a, lead_b])
        assert len(unique) == 2
        assert len(dups) == 0

    def test_against_existing(self, mock_config):
        dedup = Deduplicator(mock_config)
        existing = [Lead(name="Sarah Chen", email="sarah@example.com", phone="5551234567")]
        incoming = [Lead(name="Sarah Chen", email="sarah@example.com", phone="5551234567")]
        unique, dups = dedup.deduplicate(incoming, existing)
        assert len(unique) == 0
        assert len(dups) == 1

    def test_empty_email_and_phone_skip_exact(self, mock_config):
        dedup = Deduplicator(mock_config)
        lead_a = Lead(name="Unknown Person", email="", phone="")
        lead_b = Lead(name="Another Unknown", email="", phone="")
        unique, dups = dedup.deduplicate([lead_a, lead_b])
        # Both should pass through since we can't hash them
        assert len(unique) == 2
        assert len(dups) == 0


class TestFuzzyDedup:
    def test_name_and_company_overlap(self, mock_config):
        dedup = Deduplicator(mock_config)
        lead_a = normalize_lead(Lead(
            name="Sarah Chen", email="sarah@blueridgedesign.com",
            phone="5551234567", company="Blue Ridge Design Co",
        ))
        lead_b = normalize_lead(Lead(
            name="sarah chen", email="s.chen@blueridge.com",
            phone="5559999999", company="Blue Ridge Mktg",
        ))
        unique, dups = dedup.deduplicate([lead_a, lead_b])
        # These have different email+phone so exact dedup won't catch them,
        # but fuzzy should catch name overlap + company match
        assert len(unique) == 1
        assert len(dups) == 1

    def test_different_people_same_company(self, mock_config):
        dedup = Deduplicator(mock_config)
        lead_a = Lead(
            name="Sarah Chen", email="sarah@example.com",
            phone="1111111111", company="Acme Corp",
        )
        lead_b = Lead(
            name="Mike Torres", email="mike@example.com",
            phone="2222222222", company="Acme Corp",
        )
        unique, dups = dedup.deduplicate([lead_a, lead_b])
        assert len(unique) == 2
        assert len(dups) == 0

    def test_shared_name_tokens_prefilter(self, mock_config):
        dedup = Deduplicator(mock_config)
        assert dedup._has_shared_name_tokens(
            Lead(name="Sarah Chen"), Lead(name="Sarah Johnson")
        )
        assert not dedup._has_shared_name_tokens(
            Lead(name="Alice Smith"), Lead(name="Bob Jones")
        )
