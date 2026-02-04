# ABOUTME: Deterministic time resolution for the Newsroom CLI.
# ABOUTME: Resolves --now flag, NEWSROOM_NOW env var, or real UTC time.
"""Deterministic time anchor resolution.

Provides a single canonical 'now' value used by all date-dependent
operations, ensuring reproducibility in tests and fixtures.
"""

import os
from datetime import datetime, timezone


def _parse_iso_utc(value: str) -> datetime:
    """Parse an ISO 8601 string and return a UTC-aware datetime.

    Normalizes trailing 'Z' to '+00:00' for fromisoformat compatibility.
    Naive results are treated as UTC. Aware results are converted to UTC.
    """
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def resolve_now(cli_now: str | None = None) -> datetime:
    """Resolve the canonical 'now' timestamp.

    Priority: cli_now arg > NEWSROOM_NOW env var > datetime.now(UTC).
    Always returns a UTC-aware datetime.
    """
    if cli_now is not None:
        return _parse_iso_utc(cli_now)
    env_now = os.environ.get("NEWSROOM_NOW")
    if env_now:
        return _parse_iso_utc(env_now)
    return datetime.now(timezone.utc)
