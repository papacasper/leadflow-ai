"""AI enrichment: generates summaries and tags for leads."""

from __future__ import annotations

import json
import logging
import re
import time

from leadflow.models import Lead

logger = logging.getLogger(__name__)


class Enricher:
    def __init__(self, config: dict, claude_client=None) -> None:
        self._config = config
        self._mock_mode = config.get("mock_mode", True)
        enrich_cfg = config.get("processing", {}).get("enrichment", {})
        self._claude_model = enrich_cfg.get("claude_model", "claude-sonnet-4-5-20250929")
        self._batch_size = enrich_cfg.get("batch_size", 5)
        self._max_tokens = enrich_cfg.get("max_tokens", 1024)
        self._valid_tags = set(enrich_cfg.get("valid_tags", []))
        self._client = claude_client

    def enrich(self, leads: list[Lead]) -> list[Lead]:
        """Enrich all leads, processing in batches."""
        if not leads:
            return leads

        if self._mock_mode:
            return [self._mock_enrich_single(lead) for lead in leads]

        enriched = []
        for i in range(0, len(leads), self._batch_size):
            batch = leads[i : i + self._batch_size]
            enriched.extend(self._enrich_batch(batch))

        return enriched

    def _mock_enrich_single(self, lead: Lead) -> Lead:
        """Keyword-based mock enrichment."""
        notes_lower = lead.notes.lower()
        tags: list[str] = []
        summary_parts: list[str] = []

        # Keyword → tag mapping
        tag_rules = {
            "seo": ("seo", "Needs SEO services"),
            "website": ("web-design", "Looking for web design"),
            "rebrand": ("marketing", "Interested in rebranding"),
            "landing page": ("marketing", "Needs landing pages"),
            "mobile": ("mobile", "Mobile-focused project"),
            "app": ("mobile", "App-related needs"),
            "saas": ("saas", "SaaS company"),
            "startup": ("startup", "Startup venture"),
            "ecommerce": ("ecommerce", "E-commerce business"),
            "shopify": ("ecommerce", "Shopify-related needs"),
            "non-profit": ("local-business", "Non-profit organization"),
            "donation": ("local-business", "Needs donation functionality"),
            "law": ("local-business", "Legal services business"),
            "medical": ("healthcare", "Healthcare/medical practice"),
            "hipaa": ("healthcare", "Requires HIPAA compliance"),
            "patient": ("healthcare", "Patient-facing needs"),
            "fintech": ("fintech", "Financial technology company"),
            "investor": ("fintech", "Investor-related needs"),
            "education": ("education", "Education sector"),
            "course": ("education", "Course/learning platform"),
            "lms": ("education", "LMS integration needed"),
            "agency": ("agency", "Agency partnership"),
            "white-label": ("agency", "White-label opportunity"),
            "ai": ("ai-ml", "AI/ML focused"),
            "api": ("ai-ml", "API/technical project"),
            "enterprise": ("enterprise", "Enterprise client"),
            "conversion": ("marketing", "Conversion optimization"),
        }

        for keyword, (tag, desc) in tag_rules.items():
            if keyword in notes_lower:
                if tag not in tags:
                    tags.append(tag)
                if desc not in summary_parts:
                    summary_parts.append(desc)

        # Default if nothing matched
        if not tags:
            tags = ["web-design"]
            summary_parts = ["General web project inquiry"]

        # Filter to valid tags
        if self._valid_tags:
            tags = [t for t in tags if t in self._valid_tags]

        lead.tags = tags[:5]  # cap at 5 tags
        lead.summary = f"{lead.company or 'Prospect'}: {'. '.join(summary_parts[:3])}."
        lead.status = "enriched"
        return lead

    def _enrich_batch(self, batch: list[Lead]) -> list[Lead]:
        """Enrich a batch of leads using Claude."""
        if not self._client:
            logger.warning("No Claude client available, skipping enrichment")
            return batch

        leads_text = "\n\n".join(
            f"Lead {i+1}:\n"
            f"  Name: {lead.name}\n"
            f"  Company: {lead.company}\n"
            f"  Notes: {lead.notes}"
            for i, lead in enumerate(batch)
        )

        valid_tags_str = ", ".join(sorted(self._valid_tags)) if self._valid_tags else "any relevant tags"

        prompt = (
            f"Analyze these {len(batch)} leads and provide a JSON array with one object per lead.\n"
            f"Each object must have:\n"
            f"  - \"summary\": a 1-2 sentence business summary\n"
            f"  - \"tags\": array of 1-5 tags from ONLY these options: {valid_tags_str}\n\n"
            f"Respond with ONLY the JSON array, no other text.\n\n"
            f"{leads_text}"
        )

        for attempt in range(3):
            try:
                response = self._client.messages.create(
                    model=self._claude_model,
                    max_tokens=self._max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text.strip()
                results = self._parse_enrichment_response(text)

                if len(results) == len(batch):
                    for lead, result in zip(batch, results):
                        lead.summary = result.get("summary", "")
                        raw_tags = result.get("tags", [])
                        if self._valid_tags:
                            lead.tags = [t for t in raw_tags if t in self._valid_tags]
                        else:
                            lead.tags = raw_tags
                        lead.status = "enriched"
                    return batch
                else:
                    logger.warning(
                        "Enrichment returned %d results for %d leads",
                        len(results),
                        len(batch),
                    )

            except Exception as e:
                logger.warning("Enrichment attempt %d failed: %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)

        logger.warning("Enrichment failed after retries, returning leads un-enriched")
        return batch

    def _parse_enrichment_response(self, text: str) -> list[dict]:
        """Parse Claude's JSON response, stripping markdown fences if present."""
        # Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        text = text.strip()

        return json.loads(text)
