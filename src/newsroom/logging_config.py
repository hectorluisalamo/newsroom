# ABOUTME: Logging configuration for the Newsroom CLI.
# ABOUTME: Sets up stdlib logging with configurable verbosity.
"""Logging setup for the Newsroom CLI."""

import logging


def setup_logging(verbose: bool = False) -> None:
    """Configure stdlib logging for the newsroom package."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
