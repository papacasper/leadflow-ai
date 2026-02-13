"""Mock lead source with 12 hardcoded messy leads including duplicate pairs."""

from __future__ import annotations

from leadflow.models import Lead
from leadflow.sources.base import LeadSource


class MockSource(LeadSource):
    """Provides 12 realistic messy leads for demo/testing without external deps."""

    @property
    def name(self) -> str:
        return "mock"

    def fetch(self) -> list[Lead]:
        raw_leads = [
            # Lead 1 — clean
            {
                "name": "Sarah Chen",
                "email": "sarah@blueridgedesign.com",
                "phone": "(555) 123-4567",
                "company": "Blue Ridge Design Co",
                "notes": "Needs new website, SEO audit, complete rebrand",
            },
            # Lead 2 — duplicate of #1 (name variation + company abbreviation)
            {
                "name": "sarah chen",
                "email": "sarah@blueridgedesign.com",
                "phone": "5551234567",
                "company": "Blue Ridge Mktg",
                "notes": "Referred by Jake, wants seo help",
            },
            # Lead 3 — messy phone
            {
                "name": "  marcus JOHNSON  ",
                "email": "MARCUS.J@FRESHBYTE.IO",
                "phone": "+1-555-987-6543",
                "company": "FreshByte Technologies",
                "notes": "SaaS startup, Series A, needs landing pages and conversion optimization",
            },
            # Lead 4 — duplicate of #3 (different email format)
            {
                "name": "Marcus Johnson",
                "email": "m.johnson@freshbyte.io",
                "phone": "+15559876543",
                "company": "Freshbyte Tech",
                "notes": "met at SaaStr conference, interested in website redesign",
            },
            # Lead 5 — clean, no phone
            {
                "name": "Aisha Patel",
                "email": "aisha.p@greenleaf.org",
                "phone": "",
                "company": "GreenLeaf Foundation",
                "notes": "Non-profit, needs donation page and email campaign setup",
            },
            # Lead 6 — messy everything
            {
                "name": "robert  o'brien",
                "email": "ROB@OBRIEN-LAW.COM  ",
                "phone": "555.222.3333",
                "company": "O'Brien & Associates Law",
                "notes": "law firm, wants new website, mobile friendly, appointment booking",
            },
            # Lead 7 — minimal info
            {
                "name": "Li Wei",
                "email": "liwei88@gmail.com",
                "phone": "",
                "company": "",
                "notes": "ecommerce store, Shopify migration, product photography needs",
            },
            # Lead 8 — healthcare lead
            {
                "name": "Dr. Emily Nakamura",
                "email": "enakamura@valleyhealth.com",
                "phone": "(555) 444-5555",
                "company": "Valley Health Partners",
                "notes": "Medical practice, HIPAA compliant website, patient portal integration",
            },
            # Lead 9 — fintech
            {
                "name": "JAMES WRIGHT",
                "email": "jwright@paystream.co",
                "phone": "555-333-4444",
                "company": "PayStream Financial",
                "notes": "fintech startup, mobile app landing page, investor deck design",
            },
            # Lead 10 — education
            {
                "name": "priya sharma  ",
                "email": "  PRIYA@LEARNHUB.EDU",
                "phone": "+1 (555) 666-7777",
                "company": "LearnHub Academy",
                "notes": "online education platform, needs LMS integration and course landing pages",
            },
            # Lead 11 — agency lead
            {
                "name": "Tom Baker",
                "email": "tom@bakerdigital.agency",
                "phone": "5558889999",
                "company": "Baker Digital Agency",
                "notes": "white-label partnership, overflow web design and development work",
            },
            # Lead 12 — AI/ML startup
            {
                "name": "Yuki Tanaka",
                "email": "yuki@neuralpath.ai",
                "phone": "(555) 111-0000",
                "company": "NeuralPath AI",
                "notes": "AI startup, needs product demo website, API docs site, technical blog",
            },
        ]

        leads = []
        for raw in raw_leads:
            lead = Lead(
                name=raw.get("name", ""),
                email=raw.get("email", ""),
                phone=raw.get("phone", ""),
                company=raw.get("company", ""),
                source="mock",
                notes=raw.get("notes", ""),
                raw_data=raw,
            )
            leads.append(lead)

        return leads
