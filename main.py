"""LeadFlow AI — CLI entry point."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from leadflow.config import load_config
from leadflow.destinations.master_sheet import MasterSheetWriter
from leadflow.destinations.slack_notifier import SlackNotifier
from leadflow.pipeline import Pipeline
from leadflow.processing.deduplicator import Deduplicator
from leadflow.processing.enricher import Enricher


def build_pipeline(config: dict) -> Pipeline:
    """Construct all pipeline components based on configuration."""
    mock_mode = config.get("mock_mode", True)

    # Source selection
    if mock_mode:
        from leadflow.sources.mock_source import MockSource
        source = MockSource()
    else:
        from leadflow.sources.google_sheets import GoogleSheetsSource
        source = GoogleSheetsSource(config)

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
    writer = MasterSheetWriter(config)
    notifier = SlackNotifier(config)

    return Pipeline(
        source=source,
        deduplicator=deduplicator,
        enricher=enricher,
        writer=writer,
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
    args = parser.parse_args()

    config = load_config(
        config_path=args.config,
        mock=args.mock,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    pipeline = build_pipeline(config)
    stats = pipeline.run()
    print_summary(stats, config)

    # Exit with error if nothing was processed
    if stats.fetched == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
