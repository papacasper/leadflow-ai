"""Core data model for leads."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Lead:
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    source: str = ""
    notes: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "new"  # new | duplicate | enriched
    ingested_at: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "source": self.source,
            "notes": self.notes,
            "summary": self.summary,
            "tags": self.tags,
            "status": self.status,
            "ingested_at": self.ingested_at,
            "raw_data": self.raw_data,
        }

    def dedup_key(self) -> str | None:
        """MD5 hash of email + phone for exact dedup. Returns None if both are empty."""
        email = self.email.strip().lower()
        phone = self.phone.strip()
        if not email and not phone:
            return None
        raw = f"{email}|{phone}"
        return hashlib.md5(raw.encode()).hexdigest()

    def stamp_ingested(self) -> None:
        self.ingested_at = datetime.now(timezone.utc).isoformat()
