# ABOUTME: Feed item normalization for the Newsroom pipeline.
# ABOUTME: Cleans raw RSS entries into structured FeedItem models.
"""Feed item normalization and filtering."""

import hashlib
from datetime import datetime
from urllib.parse import urldefrag

from pydantic import ValidationError

from newsroom.models import FeedItem, FeedSource
from newsroom.utils.text import normalize_whitespace, strip_html, truncate
from newsroom.utils.time_utils import normalize_timestamp, parse_since


def _canonicalize_url(url: str) -> str:
    """Strip the fragment and any trailing slash from a URL."""
    without_fragment, _ = urldefrag(url)
    return without_fragment.rstrip("/")


def normalize_entry(
    entry: dict,
    source: FeedSource,
    beat: str,
    now: datetime,
) -> FeedItem | None:
    """Normalize a single raw feed entry into a FeedItem.

    Strips HTML, normalizes whitespace, truncates summary to 500 chars,
    and generates a deterministic item_id from the canonical URL.
    Returns None if the entry cannot be normalized.
    """
    raw_link = entry.get("link")
    raw_title = entry.get("title")
    if not raw_link or not raw_title:
        return None

    canonical_url = _canonicalize_url(raw_link)
    item_id = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()

    title = normalize_whitespace(strip_html(raw_title))
    raw_summary = entry.get("summary") or entry.get("description") or ""
    summary = truncate(normalize_whitespace(strip_html(raw_summary)), max_chars=500)

    raw_published = entry.get("published") or entry.get("updated") or ""
    published_at = normalize_timestamp(raw_published, fallback=now)

    raw_tags = [
        tag["term"]
        for tag in entry.get("tags", [])
        if isinstance(tag, dict) and tag.get("term")
    ]

    try:
        return FeedItem(
            item_id=item_id,
            title=title,
            url=canonical_url,
            source_name=source.name,
            source_feed_url=str(source.url),
            published_at=published_at,
            summary=summary,
            raw_tags=raw_tags,
            beat=beat,
        )
    except ValidationError:
        return None


def normalize_all(
    entries: list[dict],
    sources: list[FeedSource],
    beat: str,
    since: str,
    now: datetime,
) -> list[FeedItem]:
    """Normalize and filter a batch of raw feed entries.

    `entries` and `sources` are parallel lists (each entry paired with
    the source it came from). Filters by the 'since' time window
    relative to 'now'. Returns a list of FeedItems sorted by
    published_at (stable).
    """
    cutoff = now - parse_since(since)
    items: list[FeedItem] = []
    for entry, source in zip(entries, sources, strict=True):
        item = normalize_entry(entry, source, beat=beat, now=now)
        if item is None:
            continue
        if item.published_at < cutoff:
            continue
        items.append(item)
    return sorted(items, key=lambda item: item.published_at)
