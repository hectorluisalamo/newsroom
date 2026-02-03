# ABOUTME: Time-related utility functions for the Newsroom pipeline.
# ABOUTME: Parses duration strings like "48h" and normalizes timestamps to UTC.
"""Time parsing and normalization utilities."""

from datetime import datetime, timedelta


def parse_since(since: str) -> timedelta:
    """Parse a duration string like '48h' into a timedelta."""
    raise NotImplementedError


def normalize_timestamp(raw: str, fallback: datetime) -> datetime:
    """Parse a timestamp string into a UTC-aware datetime.

    Tries multiple common date formats. Falls back to the provided
    datetime if parsing fails.
    """
    raise NotImplementedError
