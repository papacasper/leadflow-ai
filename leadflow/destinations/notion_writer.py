"""Notion database destination writer using notion-client."""

from __future__ import annotations

import logging
import os
import time

from notion_client import Client

from leadflow.destinations.base import LeadDestination
from leadflow.models import Lead
from leadflow.registry import register_destination

logger = logging.getLogger(__name__)


@register_destination("notion")
class NotionWriter(LeadDestination):
    """Writes enriched leads to a Notion database."""

    def __init__(self, config: dict) -> None:
        self._config = config
        dest_cfg = config.get("destinations", {}).get("notion", {})
        token_var = dest_cfg.get("token_env_var", "NOTION_TOKEN")
        db_var = dest_cfg.get("database_id_env_var", "NOTION_DEST_DATABASE_ID")
        self._token = os.getenv(token_var, "")
        self._database_id = os.getenv(db_var, "")
        self._rate_limit_delay = dest_cfg.get("rate_limit_delay", 0.35)

    @property
    def name(self) -> str:
        return "notion"

    def write(self, leads: list[Lead]) -> int:
        """Write leads to a Notion database. Returns number of leads written."""
        if not leads:
            logger.info("No leads to write")
            return 0

        if not self._token or not self._database_id:
            logger.error("Notion credentials not set (NOTION_TOKEN / NOTION_DEST_DATABASE_ID)")
            return 0

        try:
            notion = Client(auth=self._token)
            written = 0

            for lead in leads:
                lead.stamp_ingested()
                properties = self._lead_to_properties(lead)

                try:
                    notion.pages.create(
                        parent={"database_id": self._database_id},
                        properties=properties,
                    )
                    written += 1
                except Exception as e:
                    logger.warning("Failed to write lead %s: %s", lead.name, e)

                # Respect Notion API rate limit (~3 requests/sec)
                time.sleep(self._rate_limit_delay)

            logger.info("Wrote %d/%d leads to Notion", written, len(leads))
            return written

        except Exception as e:
            logger.error("Failed to connect to Notion: %s", e)
            return 0

    @staticmethod
    def _lead_to_properties(lead: Lead) -> dict:
        """Convert a Lead to Notion page properties."""
        properties: dict = {
            "Name": {
                "title": [{"text": {"content": lead.name}}],
            },
        }

        if lead.email:
            properties["Email"] = {"email": lead.email}

        if lead.phone:
            properties["Phone"] = {"phone_number": lead.phone}

        if lead.company:
            properties["Company"] = {
                "rich_text": [{"text": {"content": lead.company}}],
            }

        if lead.notes:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": lead.notes}}],
            }

        if lead.summary:
            properties["Summary"] = {
                "rich_text": [{"text": {"content": lead.summary}}],
            }

        if lead.tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in lead.tags],
            }

        if lead.status:
            properties["Status"] = {
                "select": {"name": lead.status},
            }

        if lead.source:
            properties["Source"] = {
                "select": {"name": lead.source},
            }

        if lead.ingested_at:
            properties["Ingested At"] = {
                "date": {"start": lead.ingested_at},
            }

        return properties
