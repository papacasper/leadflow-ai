"""Mock destination writer — writes to console and output/leads.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from leadflow.destinations.base import LeadDestination
from leadflow.models import Lead
from leadflow.registry import register_destination

logger = logging.getLogger(__name__)


@register_destination("mock")
class MockWriter(LeadDestination):
    """Writes leads to a local JSON file for demo/testing."""

    def __init__(self, config: dict | None = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "mock"

    def write(self, leads: list[Lead]) -> int:
        """Write leads to output/leads.json."""
        if not leads:
            logger.info("No leads to write")
            return 0

        for lead in leads:
            lead.stamp_ingested()

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "leads.json"

        existing = []
        if output_path.exists():
            try:
                with open(output_path) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []

        new_records = [lead.to_dict() for lead in leads]
        all_records = existing + new_records

        with open(output_path, "w") as f:
            json.dump(all_records, f, indent=2, default=str)

        logger.info("Wrote %d leads to %s (total: %d)", len(leads), output_path, len(all_records))
        return len(leads)
