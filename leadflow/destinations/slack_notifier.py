"""Slack notifications — webhook or mock (console log)."""

from __future__ import annotations

import logging
import os

from leadflow.models import Lead

logger = logging.getLogger(__name__)


class SlackNotifier:
    def __init__(self, config: dict) -> None:
        self._config = config
        self._mock_mode = config.get("mock_mode", True)
        slack_cfg = config.get("destinations", {}).get("slack", {})
        self._webhook_env_var = slack_cfg.get("webhook_env_var", "SLACK_WEBHOOK_URL")
        self._channel = slack_cfg.get("channel", "#leads")

    def notify(self, leads: list[Lead], stats: dict | None = None) -> bool:
        """Send notification about new leads. Returns True on success."""
        if not leads:
            logger.info("No leads to notify about")
            return True

        if self._mock_mode:
            return self._mock_notify(leads, stats)
        return self._slack_notify(leads, stats)

    def _mock_notify(self, leads: list[Lead], stats: dict | None = None) -> bool:
        """Print notification to console."""
        logger.info("--- Slack Notification (mock) ---")
        logger.info("Channel: %s", self._channel)
        logger.info("New leads: %d", len(leads))
        for lead in leads[:5]:  # show first 5
            tags_str = ", ".join(lead.tags) if lead.tags else "no tags"
            logger.info("  • %s (%s) [%s]", lead.name, lead.company, tags_str)
        if len(leads) > 5:
            logger.info("  ... and %d more", len(leads) - 5)
        if stats:
            logger.info("Pipeline stats: %s", stats)
        logger.info("--- End Notification ---")
        return True

    def _slack_notify(self, leads: list[Lead], stats: dict | None = None) -> bool:
        """Send Block Kit message via Slack webhook."""
        webhook_url = os.getenv(self._webhook_env_var)
        if not webhook_url:
            logger.warning("Slack webhook URL not set (%s), skipping notification", self._webhook_env_var)
            return False

        try:
            import requests

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎯 {len(leads)} New Leads Processed",
                    },
                },
            ]

            for lead in leads[:10]:
                tags_str = ", ".join(lead.tags) if lead.tags else "—"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{lead.name}* ({lead.company})\n"
                            f"_{lead.summary}_\n"
                            f"Tags: `{tags_str}`"
                        ),
                    },
                })

            if stats:
                blocks.append({"type": "divider"})
                stats_text = " | ".join(f"{k}: {v}" for k, v in stats.items())
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": stats_text}],
                })

            payload = {"blocks": blocks}
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Slack notification sent successfully")
            return True

        except Exception as e:
            logger.error("Failed to send Slack notification: %s", e)
            return False
