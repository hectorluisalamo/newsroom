# ABOUTME: Deterministic time resolution for the Newsroom CLI.
# ABOUTME: Resolves --now flag, NEWSROOM_NOW env var, or real UTC time.
"""Deterministic time anchor resolution.

Provides a single canonical 'now' value used by all date-dependent
operations, ensuring reproducibility in tests and fixtures.
"""

from datetime import datetime


def resolve_now(cli_now: str | None = None) -> datetime:
    """Resolve the canonical 'now' timestamp.

    Priority: cli_now arg > NEWSROOM_NOW env var > datetime.now(UTC).
    Always returns a UTC-aware datetime.
    """
    raise NotImplementedError
