#!/usr/bin/env bash
# LeadFlow AI — One-command demo
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================="
echo "  LeadFlow AI — Demo"
echo "========================================="
echo

# Show seed data
echo "--- Seed Data ---"
uv run demo/seed_data.py
echo

# Run pipeline in mock mode
echo
echo "--- Running Pipeline (Mock Mode) ---"
echo
uv run main.py --mock --verbose

# Show output
echo
echo "--- Output File ---"
if [ -f output/leads.json ]; then
    echo "Leads written to output/leads.json"
    echo "Total leads: $(uv run python -c "import json; print(len(json.load(open('output/leads.json'))))")"
else
    echo "No output file created (this shouldn't happen in mock mode)"
fi

# Run tests
echo
echo "--- Running Tests ---"
echo
uv run --group dev pytest tests/ -v

echo
echo "========================================="
echo "  Demo complete!"
echo "========================================="
