"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from leadflow.models import Lead

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_config() -> dict:
    """Minimal mock-mode configuration."""
    return {
        "mock_mode": True,
        "dry_run": False,
        "processing": {
            "dedup": {
                "fuzzy_threshold": 0.7,
                "claude_model": "claude-haiku-4-5-20251001",
                "max_tokens": 10,
            },
            "enrichment": {
                "claude_model": "claude-sonnet-4-5-20250929",
                "batch_size": 5,
                "max_tokens": 1024,
                "valid_tags": [
                    "saas", "ecommerce", "agency", "startup", "enterprise",
                    "local-business", "marketing", "seo", "web-design",
                    "mobile", "ai-ml", "healthcare", "fintech", "education",
                ],
            },
        },
        "destinations": {
            "master_sheet": {
                "spreadsheet_name": "LeadFlow Master",
                "worksheet_index": 0,
            },
            "slack": {
                "webhook_env_var": "SLACK_WEBHOOK_URL",
                "channel": "#leads",
            },
        },
    }


@pytest.fixture
def sample_leads() -> list[Lead]:
    """Load sample leads from fixture file."""
    with open(FIXTURES_DIR / "sample_leads.json") as f:
        raw = json.load(f)
    return [
        Lead(
            name=r.get("name", ""),
            email=r.get("email", ""),
            phone=r.get("phone", ""),
            company=r.get("company", ""),
            source="test",
            notes=r.get("notes", ""),
            raw_data=r,
        )
        for r in raw
    ]


@pytest.fixture
def duplicate_pairs() -> list[dict]:
    """Load known duplicate pairs from fixture file."""
    with open(FIXTURES_DIR / "duplicate_pairs.json") as f:
        return json.load(f)
