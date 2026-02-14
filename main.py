"""LeadFlow AI — CLI entry point."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from leadflow.config import load_config
from leadflow.destinations.slack_notifier import SlackNotifier
from leadflow.pipeline import Pipeline
from leadflow.processing.deduplicator import Deduplicator
from leadflow.processing.enricher import Enricher
from leadflow.registry import get_source, get_destination, available_sources, available_destinations

# Import backend modules to trigger registration decorators
import leadflow.sources.mock_source  # noqa: F401
import leadflow.sources.google_sheets  # noqa: F401
import leadflow.sources.notion_source  # noqa: F401
import leadflow.destinations.mock_writer  # noqa: F401
import leadflow.destinations.master_sheet  # noqa: F401
import leadflow.destinations.notion_writer  # noqa: F401


def build_pipeline(config: dict) -> Pipeline:
    """Construct all pipeline components based on configuration."""
    mock_mode = config.get("mock_mode", True)

    # Determine backends from config or CLI, defaulting based on mock_mode
    source_key = config.get("source_backend", "mock" if mock_mode else "google_sheets")
    dest_key = config.get("destination_backend", "mock" if mock_mode else "google_sheets")

    source = get_source(source_key, config)
    destination = get_destination(dest_key, config)

    # Claude client (only if not mock)
    claude_client = None
    if not mock_mode:
        try:
            import anthropic
            claude_client = anthropic.Anthropic()
        except Exception as e:
            print(f"Warning: Could not initialize Anthropic client: {e}")
            print("Falling back to mock mode")
            config["mock_mode"] = True

    deduplicator = Deduplicator(config, claude_client)
    enricher = Enricher(config, claude_client)
    notifier = SlackNotifier(config)

    return Pipeline(
        source=source,
        deduplicator=deduplicator,
        enricher=enricher,
        writer=destination,
        notifier=notifier,
        config=config,
    )


def print_summary(stats, config: dict) -> None:
    """Print a rich summary table."""
    console = Console()
    console.print()

    mode = "[bold yellow]MOCK[/bold yellow]" if config.get("mock_mode") else "[bold green]LIVE[/bold green]"
    dry_run = " [dim](dry run)[/dim]" if config.get("dry_run") else ""
    console.print(f"  LeadFlow AI — Pipeline Complete {mode}{dry_run}")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")

    table.add_row("Source", config.get("source_backend", "—"))
    table.add_row("Destination", config.get("destination_backend", "—"))
    table.add_row("Leads fetched", str(stats.fetched))
    table.add_row("Normalized", str(stats.normalized))
    table.add_row("Unique", str(stats.unique))
    table.add_row("Duplicates", str(stats.duplicates))
    table.add_row("Enriched", str(stats.enriched))
    table.add_row("Written", str(stats.written))
    table.add_row("Notified", "Yes" if stats.notified else "No")
    table.add_row("Duration", f"{stats.duration_seconds:.2f}s")

    console.print(table)
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LeadFlow AI — AI-powered lead automation suite",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Run in mock mode (no API keys or external services needed)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run pipeline but skip write and notify steps",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--source", default=None,
        help=f"Source backend (available: mock, google_sheets, notion)",
    )
    parser.add_argument(
        "--dest", default=None,
        help=f"Destination backend (available: mock, google_sheets, notion)",
    )
    args = parser.parse_args()

    config = load_config(
        config_path=args.config,
        mock=args.mock,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # CLI overrides for backends
    if args.source:
        config["source_backend"] = args.source
    if args.dest:
        config["destination_backend"] = args.dest

    pipeline = build_pipeline(config)
    stats = pipeline.run()
    print_summary(stats, config)

    # Exit with error if nothing was processed
    if stats.fetched == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
