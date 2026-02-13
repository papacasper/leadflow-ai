"""Abstract base class for lead sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from leadflow.models import Lead


class LeadSource(ABC):
    """Interface for all lead sources."""

    @abstractmethod
    def fetch(self) -> list[Lead]:
        """Fetch leads from the source. Returns a list of raw Lead objects."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable source name."""
        ...
