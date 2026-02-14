"""Integration tests for the full pipeline (all mock mode)."""

import json
from pathlib import Path

import pytest

from leadflow.destinations.mock_writer import MockWriter
from leadflow.destinations.slack_notifier import SlackNotifier
from leadflow.models import Lead
from leadflow.pipeline import Pipeline
from leadflow.processing.deduplicator import Deduplicator
from leadflow.processing.enricher import Enricher
from leadflow.sources.mock_source import MockSource


@pytest.fixture
def mock_pipeline(mock_config, tmp_path, monkeypatch):
    """Build a full mock pipeline that writes to a temp directory."""
    monkeypatch.chdir(tmp_path)
    return Pipeline(
        source=MockSource(),
        deduplicator=Deduplicator(mock_config),
        enricher=Enricher(mock_config),
        writer=MockWriter(mock_config),
        notifier=SlackNotifier(mock_config),
        config=mock_config,
    )


class TestFullPipeline:
    def test_processes_all_mock_leads(self, mock_pipeline, tmp_path):
        stats = mock_pipeline.run()
        assert stats.fetched == 12
        assert stats.normalized == 12
        assert stats.unique + stats.duplicates == 12
        assert stats.duplicates >= 1  # at least the exact dup pair
        assert stats.enriched >= 1
        assert stats.written >= 1
        assert stats.duration_seconds > 0

        # Check output file was created
        output_file = tmp_path / "output" / "leads.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert len(data) == stats.written

    def test_no_leads(self, mock_config, tmp_path, monkeypatch):
        """Pipeline with an empty source should complete without error."""
        monkeypatch.chdir(tmp_path)

        class EmptySource:
            name = "empty"
            def fetch(self):
                return []

        pipeline = Pipeline(
            source=EmptySource(),
            deduplicator=Deduplicator(mock_config),
            enricher=Enricher(mock_config),
            writer=MockWriter(mock_config),
            notifier=SlackNotifier(mock_config),
            config=mock_config,
        )
        stats = pipeline.run()
        assert stats.fetched == 0
        assert stats.written == 0

    def test_dry_run(self, mock_config, tmp_path, monkeypatch):
        """Dry run should skip write and notify."""
        monkeypatch.chdir(tmp_path)
        mock_config["dry_run"] = True
        pipeline = Pipeline(
            source=MockSource(),
            deduplicator=Deduplicator(mock_config),
            enricher=Enricher(mock_config),
            writer=MockWriter(mock_config),
            notifier=SlackNotifier(mock_config),
            config=mock_config,
        )
        stats = pipeline.run()
        assert stats.fetched == 12
        assert stats.written == 0
        assert stats.notified is False

        # No output file should be created
        output_file = tmp_path / "output" / "leads.json"
        assert not output_file.exists()

    def test_all_duplicates(self, mock_config, tmp_path, monkeypatch):
        """If all incoming leads are duplicates, pipeline should handle gracefully."""
        monkeypatch.chdir(tmp_path)
        existing = [
            Lead(name="Sarah Chen", email="sarah@blueridgedesign.com", phone="5551234567"),
            Lead(name="Marcus Johnson", email="marcus.j@freshbyte.io", phone="+15559876543"),
        ]

        class DuplicateSource:
            name = "dup_source"
            def fetch(self):
                return [
                    Lead(name="Sarah Chen", email="sarah@blueridgedesign.com", phone="5551234567"),
                    Lead(name="Marcus Johnson", email="marcus.j@freshbyte.io", phone="+15559876543"),
                ]

        pipeline = Pipeline(
            source=DuplicateSource(),
            deduplicator=Deduplicator(mock_config),
            enricher=Enricher(mock_config),
            writer=MockWriter(mock_config),
            notifier=SlackNotifier(mock_config),
            config=mock_config,
        )
        stats = pipeline.run(existing_leads=existing)
        assert stats.fetched == 2
        assert stats.duplicates == 2
        assert stats.unique == 0
        assert stats.written == 0
