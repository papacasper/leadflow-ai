"""Configuration loader — merges config.yaml + .env + CLI flags."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(
    config_path: str = "config.yaml",
    mock: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Load configuration from YAML file, environment variables, and CLI flags."""
    load_dotenv()

    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # CLI flags override file config
    if mock:
        config["mock_mode"] = True

    # Auto-detect mock mode if API key is missing
    if not config.get("mock_mode"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            config["mock_mode"] = True

    config["dry_run"] = dry_run

    # Logging setup
    log_level = logging.DEBUG if verbose else logging.INFO
    log_cfg = config.get("logging", {})
    log_format = log_cfg.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.basicConfig(level=log_level, format=log_format, force=True)

    return config
