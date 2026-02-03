# ABOUTME: Feed item normalization for the Newsroom pipeline.
# ABOUTME: Cleans raw RSS entries into structured FeedItem models.
"""Feed item normalization and filtering."""

from datetime import datetime


def normalize_entry(
    entry: dict,
    source: dict,
    beat: str,
    now: datetime,
) -> object | None:
    """Normalize a single raw feed entry into a FeedItem.

    Strips HTML, normalizes whitespace, truncates summary to 500 chars,
    and generates a deterministic item_id from the canonical URL.
    Returns None if the entry cannot be normalized.
    """
    raise NotImplementedError


def normalize_all(
    entries: list,
    sources: list,
    since: str,
    now: datetime,
) -> list:
    """Normalize and filter a batch of raw feed entries.

    Filters by the 'since' time window relative to 'now'.
    Returns a list of FeedItems sorted by published_at (stable).
    """
    raise NotImplementedError
