"""Pure normalization functions for lead fields."""

from __future__ import annotations

import re
from dataclasses import replace

from leadflow.models import Lead


def normalize_email(email: str) -> str:
    """Lowercase, strip whitespace."""
    return email.strip().lower()


def normalize_name(name: str) -> str:
    """Title case, collapse whitespace, strip."""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    # Title-case but preserve particles like O'Brien
    parts = []
    for part in name.split(" "):
        if "'" in part and len(part) > 2:
            # Handle O'Brien, D'Angelo etc.
            idx = part.index("'")
            prefix = part[:idx].capitalize()
            suffix = part[idx + 1:].capitalize()
            parts.append(f"{prefix}'{suffix}")
        else:
            parts.append(part.capitalize())
    return " ".join(parts)


def normalize_phone(phone: str) -> str:
    """Strip to digits, preserve leading +. Returns empty string for empty input."""
    phone = phone.strip()
    if not phone:
        return ""
    has_plus = phone.startswith("+")
    digits = re.sub(r"[^\d]", "", phone)
    if not digits:
        return ""
    if has_plus:
        return f"+{digits}"
    return digits


def normalize_company(company: str) -> str:
    """Strip whitespace, collapse internal spaces."""
    company = company.strip()
    company = re.sub(r"\s+", " ", company)
    return company


def normalize_lead(lead: Lead) -> Lead:
    """Apply all normalizations, returning a new Lead instance."""
    return replace(
        lead,
        name=normalize_name(lead.name),
        email=normalize_email(lead.email),
        phone=normalize_phone(lead.phone),
        company=normalize_company(lead.company),
        notes=lead.notes.strip(),
    )
