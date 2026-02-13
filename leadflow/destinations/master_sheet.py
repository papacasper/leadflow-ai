"""Master sheet writer — Google Sheets or mock (console + JSON file)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from leadflow.models import Lead

logger = logging.getLogger(__name__)


class MasterSheetWriter:
    def __init__(self, config: dict) -> None:
        self._config = config
        self._mock_mode = config.get("mock_mode", True)
        dest_cfg = config.get("destinations", {}).get("master_sheet", {})
        self._spreadsheet_name = dest_cfg.get("spreadsheet_name", "LeadFlow Master")
        self._worksheet_index = dest_cfg.get("worksheet_index", 0)

    def write(self, leads: list[Lead]) -> int:
        """Write leads to destination. Returns number of leads written."""
        if not leads:
            logger.info("No leads to write")
            return 0

        # Stamp ingestion time
        for lead in leads:
            lead.stamp_ingested()

        if self._mock_mode:
            return self._mock_write(leads)
        return self._sheets_write(leads)

    def _mock_write(self, leads: list[Lead]) -> int:
        """Write to console and output/leads.json."""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "leads.json"

        # Load existing leads if file exists
        existing = []
        if output_path.exists():
            try:
                with open(output_path) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []

        # Append new leads
        new_records = [lead.to_dict() for lead in leads]
        all_records = existing + new_records

        with open(output_path, "w") as f:
            json.dump(all_records, f, indent=2, default=str)

        logger.info("Wrote %d leads to %s (total: %d)", len(leads), output_path, len(all_records))
        return len(leads)

    def _sheets_write(self, leads: list[Lead]) -> int:
        """Write leads to Google Sheets."""
        try:
            import gspread

            gc = gspread.service_account()
            spreadsheet = gc.open(self._spreadsheet_name)
            worksheet = spreadsheet.get_worksheet(self._worksheet_index)

            headers = ["name", "email", "phone", "company", "source", "notes",
                       "summary", "tags", "status", "ingested_at"]

            # Check if headers exist
            existing = worksheet.get_all_values()
            if not existing:
                worksheet.append_row(headers)

            rows = []
            for lead in leads:
                row = [
                    lead.name, lead.email, lead.phone, lead.company,
                    lead.source, lead.notes, lead.summary,
                    ", ".join(lead.tags), lead.status, lead.ingested_at,
                ]
                rows.append(row)

            for row in rows:
                worksheet.append_row(row)

            logger.info("Wrote %d leads to Google Sheets", len(leads))
            return len(leads)

        except Exception as e:
            logger.error("Failed to write to Google Sheets: %s", e)
            return 0
