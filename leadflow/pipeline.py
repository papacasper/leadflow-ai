"""Pipeline orchestrator — fetch → normalize → dedup → enrich → write → notify."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from leadflow.destinations.master_sheet import MasterSheetWriter
from leadflow.destinations.slack_notifier import SlackNotifier
from leadflow.models import Lead
from leadflow.processing.deduplicator import Deduplicator
from leadflow.processing.enricher import Enricher
from leadflow.processing.normalizer import normalize_lead
from leadflow.sources.base import LeadSource

logger = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    fetched: int = 0
    normalized: int = 0
    unique: int = 0
    duplicates: int = 0
    enriched: int = 0
    written: int = 0
    notified: bool = False
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "fetched": self.fetched,
            "normalized": self.normalized,
            "unique": self.unique,
            "duplicates": self.duplicates,
            "enriched": self.enriched,
            "written": self.written,
            "notified": self.notified,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class Pipeline:
    def __init__(
        self,
        source: LeadSource,
        deduplicator: Deduplicator,
        enricher: Enricher,
        writer: MasterSheetWriter,
        notifier: SlackNotifier,
        config: dict,
    ) -> None:
        self._source = source
        self._deduplicator = deduplicator
        self._enricher = enricher
        self._writer = writer
        self._notifier = notifier
        self._config = config
        self._dry_run = config.get("dry_run", False)

    def run(self, existing_leads: list[Lead] | None = None) -> PipelineStats:
        """Execute the full pipeline. Returns stats."""
        stats = PipelineStats()
        start = time.time()

        # Step 1: Fetch
        logger.info("Step 1/6: Fetching leads from %s", self._source.name)
        raw_leads = self._source.fetch()
        stats.fetched = len(raw_leads)
        logger.info("Fetched %d leads", stats.fetched)

        if not raw_leads:
            logger.info("No leads fetched, pipeline complete")
            stats.duration_seconds = time.time() - start
            return stats

        # Step 2: Normalize
        logger.info("Step 2/6: Normalizing leads")
        normalized = [normalize_lead(lead) for lead in raw_leads]
        stats.normalized = len(normalized)
        logger.info("Normalized %d leads", stats.normalized)

        # Step 3: Deduplicate
        logger.info("Step 3/6: Deduplicating leads")
        unique, duplicates = self._deduplicator.deduplicate(normalized, existing_leads)
        stats.unique = len(unique)
        stats.duplicates = len(duplicates)
        logger.info("Dedup: %d unique, %d duplicates", stats.unique, stats.duplicates)

        if not unique:
            logger.info("All leads were duplicates, pipeline complete")
            stats.duration_seconds = time.time() - start
            return stats

        # Step 4: Enrich
        logger.info("Step 4/6: Enriching leads")
        enriched = self._enricher.enrich(unique)
        stats.enriched = len([l for l in enriched if l.status == "enriched"])
        logger.info("Enriched %d leads", stats.enriched)

        # Step 5: Write
        if self._dry_run:
            logger.info("Step 5/6: SKIPPED (dry run)")
        else:
            logger.info("Step 5/6: Writing to master sheet")
            stats.written = self._writer.write(enriched)
            logger.info("Wrote %d leads", stats.written)

        # Step 6: Notify
        if self._dry_run:
            logger.info("Step 6/6: SKIPPED (dry run)")
        else:
            logger.info("Step 6/6: Sending notifications")
            stats.notified = self._notifier.notify(enriched, stats.to_dict())

        stats.duration_seconds = time.time() - start
        logger.info("Pipeline complete in %.2fs", stats.duration_seconds)
        return stats
