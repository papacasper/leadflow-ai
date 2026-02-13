"""Two-stage deduplication: exact hash + Claude fuzzy (or mock heuristic)."""

from __future__ import annotations

import logging
import time

from leadflow.models import Lead

logger = logging.getLogger(__name__)


class Deduplicator:
    def __init__(self, config: dict, claude_client=None) -> None:
        self._config = config
        self._mock_mode = config.get("mock_mode", True)
        dedup_cfg = config.get("processing", {}).get("dedup", {})
        self._fuzzy_threshold = dedup_cfg.get("fuzzy_threshold", 0.7)
        self._claude_model = dedup_cfg.get("claude_model", "claude-haiku-4-5-20251001")
        self._max_tokens = dedup_cfg.get("max_tokens", 10)
        self._client = claude_client

    def deduplicate(
        self, incoming: list[Lead], existing: list[Lead] | None = None
    ) -> tuple[list[Lead], list[Lead]]:
        """Returns (unique_leads, duplicate_leads)."""
        if existing is None:
            existing = []

        # Build set of known dedup keys from existing leads
        known_keys: set[str] = set()
        for lead in existing:
            key = lead.dedup_key()
            if key:
                known_keys.add(key)

        unique: list[Lead] = []
        duplicates: list[Lead] = []

        for lead in incoming:
            # Stage 1: exact hash dedup
            key = lead.dedup_key()
            if key and key in known_keys:
                lead.status = "duplicate"
                duplicates.append(lead)
                logger.debug("Exact duplicate: %s (%s)", lead.name, lead.email)
                continue

            # Stage 2: fuzzy dedup against existing + already-accepted unique leads
            is_dup = False
            candidates = existing + unique
            for candidate in candidates:
                if not self._has_shared_name_tokens(lead, candidate):
                    continue
                # Potential match — use fuzzy check
                if self._fuzzy_check(lead, candidate):
                    lead.status = "duplicate"
                    duplicates.append(lead)
                    is_dup = True
                    logger.debug(
                        "Fuzzy duplicate: %s ~ %s", lead.name, candidate.name
                    )
                    break

            if not is_dup:
                if key:
                    known_keys.add(key)
                unique.append(lead)

        logger.info(
            "Dedup: %d incoming → %d unique, %d duplicates",
            len(incoming),
            len(unique),
            len(duplicates),
        )
        return unique, duplicates

    def _has_shared_name_tokens(self, a: Lead, b: Lead) -> bool:
        """Pre-filter: do the two leads share at least one name token?"""
        tokens_a = set(a.name.lower().split())
        tokens_b = set(b.name.lower().split())
        # Remove common titles/prefixes
        stop = {"dr.", "mr.", "ms.", "mrs.", "jr.", "sr.", "dr", "mr", "ms", "mrs"}
        tokens_a -= stop
        tokens_b -= stop
        return bool(tokens_a & tokens_b)

    def _fuzzy_check(self, a: Lead, b: Lead) -> bool:
        """Dispatch to real or mock fuzzy matching."""
        if self._mock_mode:
            return self._mock_fuzzy_check(a, b)
        return self._claude_fuzzy_check(a, b)

    def _mock_fuzzy_check(self, a: Lead, b: Lead) -> bool:
        """Heuristic fuzzy matching without API calls."""
        # Name token overlap ratio
        tokens_a = set(a.name.lower().split())
        tokens_b = set(b.name.lower().split())
        stop = {"dr.", "mr.", "ms.", "mrs.", "jr.", "sr.", "dr", "mr", "ms", "mrs"}
        tokens_a -= stop
        tokens_b -= stop
        if not tokens_a or not tokens_b:
            return False
        overlap = len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))

        # Company substring matching
        comp_a = a.company.lower().replace(".", "").strip()
        comp_b = b.company.lower().replace(".", "").strip()
        company_match = False
        if comp_a and comp_b:
            # Check if one is a substring/abbreviation of the other
            shorter, longer = sorted([comp_a, comp_b], key=len)
            # Extract first word as base comparison
            company_match = shorter.split()[0] == longer.split()[0]

        # Email domain match
        domain_a = a.email.split("@")[-1] if "@" in a.email else ""
        domain_b = b.email.split("@")[-1] if "@" in b.email else ""
        domain_match = domain_a and domain_b and domain_a == domain_b

        # Decision: high name overlap + (company OR domain match)
        if overlap >= self._fuzzy_threshold and (company_match or domain_match):
            return True

        return False

    def _claude_fuzzy_check(self, a: Lead, b: Lead) -> bool:
        """Use Claude to determine if two leads are the same person."""
        if not self._client:
            logger.warning("No Claude client, defaulting to DIFFERENT")
            return False

        prompt = (
            f"Are these two leads the same person? Reply ONLY 'SAME' or 'DIFFERENT'.\n\n"
            f"Lead A: {a.name}, {a.email}, {a.phone}, {a.company}\n"
            f"Lead B: {b.name}, {b.email}, {b.phone}, {b.company}"
        )

        for attempt in range(3):
            try:
                response = self._client.messages.create(
                    model=self._claude_model,
                    max_tokens=self._max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                answer = response.content[0].text.strip().upper()
                return "SAME" in answer
            except Exception as e:
                logger.warning("Claude fuzzy check attempt %d failed: %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)

        # Safe default: keep the lead
        logger.warning("Claude fuzzy check failed after retries, defaulting to DIFFERENT")
        return False
