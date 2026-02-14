"""Google Sheets destination writer."""

from __future__ import annotations

import logging

from leadflow.destinations.base import LeadDestination
from leadflow.models import Lead
from leadflow.registry import register_destination

logger = logging.getLogger(__name__)


@register_destination("google_sheets")
class GoogleSheetsWriter(LeadDestination):
    """Writes enriched leads to a Google Sheets spreadsheet."""

    def __init__(self, config: dict) -> None:
        self._config = config
        dest_cfg = config.get("destinations", {}).get("google_sheets", {})
        self._spreadsheet_name = dest_cfg.get("spreadsheet_name", "LeadFlow Master")
        self._worksheet_index = dest_cfg.get("worksheet_index", 0)

    @property
    def name(self) -> str:
        return "google_sheets"

    def write(self, leads: list[Lead]) -> int:
        """Write leads to Google Sheets. Returns number of leads written."""
        if not leads:
            logger.info("No leads to write")
            return 0

        for lead in leads:
            lead.stamp_ingested()

        try:
            import gspread

            gc = gspread.service_account()
            spreadsheet = gc.open(self._spreadsheet_name)
            worksheet = spreadsheet.get_worksheet(self._worksheet_index)

            headers = ["name", "email", "phone", "company", "source", "notes",
                       "summary", "tags", "status", "ingested_at"]

            existing = worksheet.get_all_values()
            if not existing:
                worksheet.append_row(headers)

            for lead in leads:
                row = [
                    lead.name, lead.email, lead.phone, lead.company,
                    lead.source, lead.notes, lead.summary,
                    ", ".join(lead.tags), lead.status, lead.ingested_at,
                ]
                worksheet.append_row(row)

            logger.info("Wrote %d leads to Google Sheets", len(leads))
            return len(leads)

        except Exception as e:
            logger.error("Failed to write to Google Sheets: %s", e)
            return 0
