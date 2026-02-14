"""Tests for the backend registry."""

from leadflow.destinations.base import LeadDestination
from leadflow.models import Lead
from leadflow.registry import (
    _destinations,
    _sources,
    available_destinations,
    available_sources,
    get_destination,
    get_source,
    register_destination,
    register_source,
)
from leadflow.sources.base import LeadSource

import pytest


# Ensure backend modules are imported so decorators run
import leadflow.sources.mock_source  # noqa: F401
import leadflow.sources.google_sheets  # noqa: F401
import leadflow.sources.notion_source  # noqa: F401
import leadflow.destinations.mock_writer  # noqa: F401
import leadflow.destinations.master_sheet  # noqa: F401
import leadflow.destinations.notion_writer  # noqa: F401


class TestRegistration:
    def test_mock_source_registered(self):
        assert "mock" in _sources

    def test_google_sheets_source_registered(self):
        assert "google_sheets" in _sources

    def test_notion_source_registered(self):
        assert "notion" in _sources

    def test_mock_destination_registered(self):
        assert "mock" in _destinations

    def test_google_sheets_destination_registered(self):
        assert "google_sheets" in _destinations

    def test_notion_destination_registered(self):
        assert "notion" in _destinations

    def test_available_sources(self):
        sources = available_sources()
        assert "mock" in sources
        assert "google_sheets" in sources
        assert "notion" in sources

    def test_available_destinations(self):
        dests = available_destinations()
        assert "mock" in dests
        assert "google_sheets" in dests
        assert "notion" in dests


class TestFactory:
    def test_get_mock_source(self):
        source = get_source("mock", {})
        assert isinstance(source, LeadSource)
        assert source.name == "mock"

    def test_get_mock_destination(self):
        dest = get_destination("mock", {})
        assert isinstance(dest, LeadDestination)
        assert dest.name == "mock"

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            get_source("nonexistent", {})

    def test_unknown_destination_raises(self):
        with pytest.raises(ValueError, match="Unknown destination"):
            get_destination("nonexistent", {})

    def test_mock_source_returns_leads(self):
        source = get_source("mock", {})
        leads = source.fetch()
        assert len(leads) == 12
        assert all(isinstance(lead, Lead) for lead in leads)
