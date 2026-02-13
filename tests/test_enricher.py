"""Tests for the enrichment module."""

from leadflow.models import Lead
from leadflow.processing.enricher import Enricher


class TestMockEnrichment:
    def test_seo_keyword(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Alice", company="Acme", notes="needs seo audit")
        result = enricher.enrich([lead])[0]
        assert "seo" in result.tags
        assert result.status == "enriched"

    def test_healthcare_keywords(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Dr. Smith", company="Valley Health", notes="medical practice, HIPAA compliant website")
        result = enricher.enrich([lead])[0]
        assert "healthcare" in result.tags
        assert result.status == "enriched"

    def test_multiple_tags(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Bob", company="TechCo", notes="SaaS startup, needs landing page and mobile app")
        result = enricher.enrich([lead])[0]
        assert len(result.tags) >= 2
        assert result.status == "enriched"

    def test_no_matching_keywords(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Eve", company="Unknown", notes="general inquiry")
        result = enricher.enrich([lead])[0]
        # Should get default tag
        assert len(result.tags) >= 1
        assert result.status == "enriched"

    def test_empty_list(self, mock_config):
        enricher = Enricher(mock_config)
        result = enricher.enrich([])
        assert result == []

    def test_summary_includes_company(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Alice", company="Acme Corp", notes="needs website redesign")
        result = enricher.enrich([lead])[0]
        assert "Acme Corp" in result.summary

    def test_tags_filtered_to_valid(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(name="Test", company="Test Co", notes="seo website mobile ecommerce")
        result = enricher.enrich([lead])[0]
        valid = set(mock_config["processing"]["enrichment"]["valid_tags"])
        for tag in result.tags:
            assert tag in valid

    def test_max_five_tags(self, mock_config):
        enricher = Enricher(mock_config)
        lead = Lead(
            name="Test", company="Test Co",
            notes="seo website mobile ecommerce saas startup agency ai enterprise education fintech",
        )
        result = enricher.enrich([lead])[0]
        assert len(result.tags) <= 5
