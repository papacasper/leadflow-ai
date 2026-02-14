"""Notion database lead source using notion-client."""

from __future__ import annotations

import logging
import os

from notion_client import Client

from leadflow.models import Lead
from leadflow.registry import register_source
from leadflow.sources.base import LeadSource

logger = logging.getLogger(__name__)


@register_source("notion")
class NotionSource(LeadSource):
    """Fetches leads from a Notion database."""

    def __init__(self, config: dict) -> None:
        self._config = config
        src_cfg = config.get("sources", {}).get("notion", {})
        token_var = src_cfg.get("token_env_var", "NOTION_TOKEN")
        db_var = src_cfg.get("database_id_env_var", "NOTION_SOURCE_DATABASE_ID")
        self._token = os.getenv(token_var, "")
        self._database_id = os.getenv(db_var, "")

    @property
    def name(self) -> str:
        return "notion"

    def fetch(self) -> list[Lead]:
        if not self._token or not self._database_id:
            logger.error("Notion credentials not set (NOTION_TOKEN / NOTION_SOURCE_DATABASE_ID)")
            return []

        try:
            notion = Client(auth=self._token)
            leads = []
            has_more = True
            start_cursor = None

            while has_more:
                kwargs: dict = {"database_id": self._database_id, "page_size": 100}
                if start_cursor:
                    kwargs["start_cursor"] = start_cursor

                response = notion.databases.query(**kwargs)
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

                for page in response.get("results", []):
                    lead = self._page_to_lead(page)
                    leads.append(lead)

            logger.info("Fetched %d leads from Notion", len(leads))
            return leads

        except Exception as e:
            logger.error("Failed to fetch from Notion: %s", e)
            return []

    def _page_to_lead(self, page: dict) -> Lead:
        """Convert a Notion page to a Lead object."""
        props = page.get("properties", {})

        return Lead(
            name=self._get_title(props, "Name"),
            email=self._get_email(props, "Email"),
            phone=self._get_phone(props, "Phone"),
            company=self._get_rich_text(props, "Company"),
            source="notion",
            notes=self._get_rich_text(props, "Notes"),
            raw_data={"notion_page_id": page.get("id", "")},
        )

    @staticmethod
    def _get_title(props: dict, key: str) -> str:
        """Extract text from a Notion title property."""
        prop = props.get(key, {})
        title_list = prop.get("title", [])
        if title_list:
            return title_list[0].get("text", {}).get("content", "")
        return ""

    @staticmethod
    def _get_rich_text(props: dict, key: str) -> str:
        """Extract text from a Notion rich_text property."""
        prop = props.get(key, {})
        rt_list = prop.get("rich_text", [])
        if rt_list:
            return rt_list[0].get("text", {}).get("content", "")
        return ""

    @staticmethod
    def _get_email(props: dict, key: str) -> str:
        """Extract value from a Notion email property."""
        prop = props.get(key, {})
        return prop.get("email", "") or ""

    @staticmethod
    def _get_phone(props: dict, key: str) -> str:
        """Extract value from a Notion phone_number property."""
        prop = props.get(key, {})
        return prop.get("phone_number", "") or ""
