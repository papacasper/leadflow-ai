"""Seed data script — populates mock source or prints Google Sheets instructions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from leadflow.sources.mock_source import MockSource


def main():
    print("LeadFlow AI — Seed Data\n")
    print("=" * 50)

    # Show mock leads
    source = MockSource()
    leads = source.fetch()

    print(f"\nMock source contains {len(leads)} leads:\n")
    for i, lead in enumerate(leads, 1):
        print(f"  {i:2d}. {lead.name:<25s} {lead.email:<35s} {lead.company}")

    print("\n" + "=" * 50)
    print("\nTo run the pipeline with mock data:")
    print("  python main.py --mock")
    print("\nTo run with verbose output:")
    print("  python main.py --mock --verbose")
    print("\n" + "=" * 50)

    print("\nTo set up real Google Sheets integration:")
    print("  1. Create a Google Cloud project")
    print("  2. Enable Google Sheets API and Drive API")
    print("  3. Create a service account and download JSON key")
    print("  4. Save key as ~/.config/gspread/service_account.json")
    print("  5. Create 'LeadFlow Raw Leads' spreadsheet")
    print("  6. Share it with the service account email (Editor)")
    print("  7. Add these columns: name, email, phone, company, notes")
    print("  8. Run: python main.py")

    # Also dump leads as JSON for manual import
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    seed_path = output_dir / "seed_leads.json"
    with open(seed_path, "w") as f:
        json.dump([lead.to_dict() for lead in leads], f, indent=2, default=str)
    print(f"\nSeed data exported to: {seed_path}")


if __name__ == "__main__":
    main()
