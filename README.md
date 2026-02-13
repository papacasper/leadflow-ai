# LeadFlow AI

AI-powered lead automation suite that ingests, normalizes, deduplicates, enriches, and routes leads using Claude.

## Quick Start

```bash
uv run main.py --mock
```

No API keys needed — mock mode uses synthetic data to demonstrate the full pipeline.

## Features

LeadFlow AI processes leads through a six-stage pipeline:

1. **Source** — Pull raw leads from Google Sheets (or mock data)
2. **Normalize** — Standardize names, emails, phone numbers, and company fields
3. **Deduplicate** — Fuzzy matching + Claude-powered semantic dedup
4. **Enrich** — Claude analyzes leads to add tags, scores, and summaries
5. **Write** — Push enriched leads to a master Google Sheet (or local JSON)
6. **Notify** — Send new-lead alerts to Slack

## CLI Usage

```bash
uv run main.py [OPTIONS]
```

| Flag | Description |
|---|---|
| `--mock` | Run with synthetic data, no external services |
| `--dry-run` | Execute pipeline but skip write and notify |
| `--verbose`, `-v` | Enable debug-level logging |
| `--config PATH` | Config file path (default: `config.yaml`) |

## Project Structure

```
leadflow-ai/
├── main.py                     # CLI entry point
├── config.yaml                 # Runtime configuration
├── pyproject.toml
├── leadflow/
│   ├── config.py               # Config loading
│   ├── models.py               # Data models
│   ├── pipeline.py             # Pipeline orchestration
│   ├── sources/
│   │   ├── base.py             # Base source class
│   │   ├── mock_source.py      # Mock data source
│   │   └── google_sheets.py    # Google Sheets source
│   ├── processing/
│   │   ├── normalizer.py       # Lead normalization
│   │   ├── deduplicator.py     # Claude-powered dedup
│   │   └── enricher.py         # Claude-powered enrichment
│   └── destinations/
│       ├── master_sheet.py     # Google Sheets output
│       └── slack_notifier.py   # Slack notifications
├── tests/
│   ├── conftest.py
│   ├── test_normalizer.py
│   ├── test_deduplicator.py
│   ├── test_enricher.py
│   ├── test_pipeline.py
│   └── fixtures/
└── demo/
    ├── run_demo.sh
    └── seed_data.py
```

## Configuration

**`config.yaml`** — Controls pipeline behavior: source/destination settings, Claude model selection, dedup thresholds, enrichment tags, and logging.

**`.env`** — Store API credentials (not committed):

```
ANTHROPIC_API_KEY=sk-ant-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## Testing

```bash
uv run --group dev pytest tests/ -v
```

## License

[MIT](LICENSE)
