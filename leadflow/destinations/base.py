"""Abstract base class for lead destinations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from leadflow.models import Lead


class LeadDestination(ABC):
    """Interface for all lead destinations."""

    @abstractmethod
    def write(self, leads: list[Lead]) -> int:
        """Write leads to the destination. Returns the number of leads written."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable destination name."""
        ...
