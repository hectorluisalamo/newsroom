# ABOUTME: Time-related utility functions for the Newsroom pipeline.
# ABOUTME: Parses duration strings like "48h" and normalizes timestamps to UTC.
"""Time parsing and normalization utilities."""

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

_SINCE_RE = re.compile(r"^(\d+)(h|d|m)$")

_UNIT_TO_KWARG = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


def parse_since(since: str) -> timedelta:
    """Parse a duration string like '48h' into a timedelta.

    Supports minute ('m'), hour ('h'), and day ('d') suffixes.
    """
    match = _SINCE_RE.match(since.strip())
    if not match:
        msg = f"Invalid since window: {since!r} (expected e.g. '48h', '2d', '90m')"
        raise ValueError(msg)
    amount, unit = match.groups()
    kwarg = _UNIT_TO_KWARG[unit]
    return timedelta(**{kwarg: int(amount)})


def normalize_timestamp(raw: str, fallback: datetime) -> datetime:
    """Parse a timestamp string into a UTC-aware datetime.

    Tries RFC 822 (RSS pubDate) format first, then ISO 8601. Falls back
    to the provided datetime if parsing fails. The fallback itself is
    normalized to UTC if naive.
    """
    for parser in (parsedate_to_datetime, datetime.fromisoformat):
        try:
            parsed = parser(raw)
        except (TypeError, ValueError):
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if fallback.tzinfo is None:
        return fallback.replace(tzinfo=timezone.utc)
    return fallback.astimezone(timezone.utc)
