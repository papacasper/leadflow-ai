"""Tests for the Notion destination writer."""

from unittest.mock import MagicMock, patch, call

from leadflow.destinations.notion_writer import NotionWriter
from leadflow.models import Lead


class TestNotionWriter:
    def test_name(self):
        writer = NotionWriter({"destinations": {"notion": {}}})
        assert writer.name == "notion"

    def test_empty_leads_returns_zero(self):
        writer = NotionWriter({"destinations": {"notion": {}}})
        assert writer.write([]) == 0

    def test_missing_credentials_returns_zero(self):
        """Should return 0 if credentials not set."""
        with patch.dict("os.environ", {}, clear=True):
            writer = NotionWriter({"destinations": {"notion": {}}})
            leads = [Lead(name="Test", email="test@example.com")]
            assert writer.write(leads) == 0

    @patch("leadflow.destinations.notion_writer.time.sleep")
    @patch("leadflow.destinations.notion_writer.os.getenv")
    def test_write_single_lead(self, mock_getenv, mock_sleep):
        """Test writing a single lead to Notion."""
        mock_getenv.side_effect = lambda key, default="": {
            "NOTION_TOKEN": "test-token",
            "NOTION_DEST_DATABASE_ID": "test-db-id",
        }.get(key, default)

        writer = NotionWriter({"destinations": {"notion": {"rate_limit_delay": 0}}})

        lead = Lead(
            name="Sarah Chen",
            email="sarah@example.com",
            phone="5551234567",
            company="Acme Corp",
            notes="Needs website",
            summary="Web design prospect",
            tags=["web-design", "seo"],
            status="enriched",
            source="mock",
        )

        with patch("leadflow.destinations.notion_writer.Client") as MockClient:
            mock_notion = MagicMock()
            MockClient.return_value = mock_notion

            result = writer.write([lead])

            assert result == 1
            mock_notion.pages.create.assert_called_once()
            call_kwargs = mock_notion.pages.create.call_args
            props = call_kwargs.kwargs.get("properties") or call_kwargs[1].get("properties")

            assert props["Name"]["title"][0]["text"]["content"] == "Sarah Chen"
            assert props["Email"]["email"] == "sarah@example.com"
            assert props["Tags"]["multi_select"] == [{"name": "web-design"}, {"name": "seo"}]

    def test_lead_to_properties_minimal(self):
        """Test property conversion with minimal data."""
        lead = Lead(name="Test Lead")
        props = NotionWriter._lead_to_properties(lead)
        assert "Name" in props
        assert props["Name"]["title"][0]["text"]["content"] == "Test Lead"
        # Optional fields with empty values should not be present
        assert "Email" not in props
        assert "Phone" not in props

    def test_lead_to_properties_full(self):
        """Test property conversion with all fields populated."""
        lead = Lead(
            name="Sarah Chen",
            email="sarah@example.com",
            phone="5551234567",
            company="Acme Corp",
            notes="Needs website",
            summary="Web design prospect",
            tags=["web-design", "seo"],
            status="enriched",
            source="notion",
            ingested_at="2026-01-01T00:00:00+00:00",
        )
        props = NotionWriter._lead_to_properties(lead)

        assert props["Name"]["title"][0]["text"]["content"] == "Sarah Chen"
        assert props["Email"]["email"] == "sarah@example.com"
        assert props["Phone"]["phone_number"] == "5551234567"
        assert props["Company"]["rich_text"][0]["text"]["content"] == "Acme Corp"
        assert props["Notes"]["rich_text"][0]["text"]["content"] == "Needs website"
        assert props["Summary"]["rich_text"][0]["text"]["content"] == "Web design prospect"
        assert len(props["Tags"]["multi_select"]) == 2
        assert props["Status"]["select"]["name"] == "enriched"
        assert props["Source"]["select"]["name"] == "notion"
        assert props["Ingested At"]["date"]["start"] == "2026-01-01T00:00:00+00:00"
