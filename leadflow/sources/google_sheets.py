"""Google Sheets lead source using gspread."""

from __future__ import annotations

import logging

from leadflow.models import Lead
from leadflow.registry import register_source
from leadflow.sources.base import LeadSource

logger = logging.getLogger(__name__)


@register_source("google_sheets")
class GoogleSheetsSource(LeadSource):
    """Fetches leads from a Google Sheets spreadsheet."""

    def __init__(self, config: dict) -> None:
        self._config = config.get("sources", {}).get("google_sheets", {})
        self._spreadsheet_name = self._config.get("spreadsheet_name", "LeadFlow Raw Leads")
        self._worksheet_index = self._config.get("worksheet_index", 0)

    @property
    def name(self) -> str:
        return "google_sheets"

    def fetch(self) -> list[Lead]:
        try:
            import gspread

            gc = gspread.service_account()
            spreadsheet = gc.open(self._spreadsheet_name)
            worksheet = spreadsheet.get_worksheet(self._worksheet_index)
            records = worksheet.get_all_records()
        except Exception as e:
            logger.error("Failed to fetch from Google Sheets: %s", e)
            return []

        leads = []
        for row in records:
            lead = Lead(
                name=str(row.get("name", "") or ""),
                email=str(row.get("email", "") or ""),
                phone=str(row.get("phone", "") or ""),
                company=str(row.get("company", "") or ""),
                source="google_sheets",
                notes=str(row.get("notes", "") or ""),
                raw_data=dict(row),
            )
            leads.append(lead)

        logger.info("Fetched %d leads from Google Sheets", len(leads))
        return leads
