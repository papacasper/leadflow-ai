"""Tests for the Notion source module."""

from unittest.mock import MagicMock, patch

from leadflow.models import Lead
from leadflow.sources.notion_source import NotionSource


class TestNotionSource:
    def test_name(self):
        source = NotionSource({"sources": {"notion": {}}})
        assert source.name == "notion"

    def test_missing_credentials_returns_empty(self):
        """Should return empty list if NOTION_TOKEN or database ID not set."""
        with patch.dict("os.environ", {}, clear=True):
            source = NotionSource({"sources": {"notion": {}}})
            leads = source.fetch()
            assert leads == []

    @patch("leadflow.sources.notion_source.os.getenv")
    def test_fetch_single_page(self, mock_getenv):
        """Test fetching a single page from Notion."""
        mock_getenv.side_effect = lambda key, default="": {
            "NOTION_TOKEN": "test-token",
            "NOTION_SOURCE_DATABASE_ID": "test-db-id",
        }.get(key, default)

        source = NotionSource({"sources": {"notion": {}}})

        mock_response = {
            "results": [
                {
                    "id": "page-1",
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Sarah Chen"}}]},
                        "Email": {"email": "sarah@example.com"},
                        "Phone": {"phone_number": "(555) 123-4567"},
                        "Company": {"rich_text": [{"text": {"content": "Acme Corp"}}]},
                        "Notes": {"rich_text": [{"text": {"content": "Needs website"}}]},
                    },
                }
            ],
            "has_more": False,
            "next_cursor": None,
        }

        with patch("leadflow.sources.notion_source.Client") as MockClient:
            mock_notion = MagicMock()
            mock_notion.databases.query.return_value = mock_response
            MockClient.return_value = mock_notion

            leads = source.fetch()

            assert len(leads) == 1
            assert leads[0].name == "Sarah Chen"
            assert leads[0].email == "sarah@example.com"
            assert leads[0].phone == "(555) 123-4567"
            assert leads[0].company == "Acme Corp"
            assert leads[0].notes == "Needs website"
            assert leads[0].source == "notion"

    @patch("leadflow.sources.notion_source.os.getenv")
    def test_fetch_handles_pagination(self, mock_getenv):
        """Test that pagination works correctly."""
        mock_getenv.side_effect = lambda key, default="": {
            "NOTION_TOKEN": "test-token",
            "NOTION_SOURCE_DATABASE_ID": "test-db-id",
        }.get(key, default)

        source = NotionSource({"sources": {"notion": {}}})

        page_1 = {
            "results": [
                {
                    "id": "page-1",
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Lead 1"}}]},
                    },
                }
            ],
            "has_more": True,
            "next_cursor": "cursor-abc",
        }
        page_2 = {
            "results": [
                {
                    "id": "page-2",
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Lead 2"}}]},
                    },
                }
            ],
            "has_more": False,
            "next_cursor": None,
        }

        with patch("leadflow.sources.notion_source.Client") as MockClient:
            mock_notion = MagicMock()
            mock_notion.databases.query.side_effect = [page_1, page_2]
            MockClient.return_value = mock_notion

            leads = source.fetch()

            assert len(leads) == 2
            assert leads[0].name == "Lead 1"
            assert leads[1].name == "Lead 2"
            assert mock_notion.databases.query.call_count == 2

    def test_page_to_lead_empty_properties(self):
        """Test conversion when properties are empty."""
        source = NotionSource({"sources": {"notion": {}}})
        page = {"id": "page-1", "properties": {}}
        lead = source._page_to_lead(page)
        assert lead.name == ""
        assert lead.email == ""
        assert lead.phone == ""
        assert lead.company == ""
        assert lead.source == "notion"
