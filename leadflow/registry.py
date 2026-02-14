"""Backend registry for lead sources and destinations."""

from __future__ import annotations

from typing import Callable, Type

from leadflow.destinations.base import LeadDestination
from leadflow.sources.base import LeadSource

_sources: dict[str, Type[LeadSource]] = {}
_destinations: dict[str, Type[LeadDestination]] = {}


# ---------------------------------------------------------------------------
# Registration decorators
# ---------------------------------------------------------------------------

def register_source(key: str) -> Callable[[Type[LeadSource]], Type[LeadSource]]:
    """Decorator that registers a LeadSource subclass under *key*."""

    def decorator(cls: Type[LeadSource]) -> Type[LeadSource]:
        _sources[key] = cls
        return cls

    return decorator


def register_destination(key: str) -> Callable[[Type[LeadDestination]], Type[LeadDestination]]:
    """Decorator that registers a LeadDestination subclass under *key*."""

    def decorator(cls: Type[LeadDestination]) -> Type[LeadDestination]:
        _destinations[key] = cls
        return cls

    return decorator


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def get_source(key: str, config: dict) -> LeadSource:
    """Instantiate and return the source registered under *key*.

    Raises ``ValueError`` if *key* is not registered.
    """
    if key not in _sources:
        available = ", ".join(sorted(_sources)) or "(none)"
        raise ValueError(
            f"Unknown source {key!r}. Available sources: {available}"
        )
    return _sources[key](config)


def get_destination(key: str, config: dict) -> LeadDestination:
    """Instantiate and return the destination registered under *key*.

    Raises ``ValueError`` if *key* is not registered.
    """
    if key not in _destinations:
        available = ", ".join(sorted(_destinations)) or "(none)"
        raise ValueError(
            f"Unknown destination {key!r}. Available destinations: {available}"
        )
    return _destinations[key](config)


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

def available_sources() -> list[str]:
    """Return a sorted list of registered source keys."""
    return sorted(_sources)


def available_destinations() -> list[str]:
    """Return a sorted list of registered destination keys."""
    return sorted(_destinations)
