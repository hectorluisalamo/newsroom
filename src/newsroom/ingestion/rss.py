# ABOUTME: RSS feed fetching and parsing using httpx and feedparser.
# ABOUTME: Handles timeouts, retries, and graceful per-feed failure.
"""RSS feed ingestion for the Newsroom pipeline."""

import logging
from pathlib import Path

import feedparser
import httpx

from newsroom.models import FeedSource

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {500, 502, 503, 504}


def fetch_feed(url: str, timeout: int = 30) -> dict:
    """Fetch and parse a single RSS feed.

    Uses sync httpx with explicit timeout and one retry on
    transient failure (timeout, 5xx).
    """
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = httpx.get(url, timeout=timeout)
            if response.status_code in _RETRYABLE_STATUS:
                msg = f"Retryable status {response.status_code} from {url}"
                raise httpx.HTTPStatusError(
                    msg, request=response.request, response=response
                )
            response.raise_for_status()
            return feedparser.parse(response.content)
        except (
            httpx.TimeoutException,
            httpx.HTTPStatusError,
            httpx.TransportError,
        ) as exc:
            last_error = exc
            if attempt == 0:
                continue
    raise RuntimeError(f"Failed to fetch feed {url}: {last_error}") from last_error


def fetch_all_feeds(sources: list[FeedSource]) -> list[tuple[dict, FeedSource]]:
    """Fetch all RSS feeds for a list of sources.

    Handles per-feed failures gracefully: logs a warning and
    continues with remaining feeds. Returns a flat list of
    (raw_entry, source) pairs across all successfully fetched feeds.
    """
    pairs: list[tuple[dict, FeedSource]] = []
    for source in sources:
        try:
            parsed = fetch_feed(str(source.url))
        except RuntimeError as exc:
            logger.warning("Skipping feed %s (%s): %s", source.name, source.url, exc)
            continue
        for entry in parsed.entries:
            pairs.append((entry, source))
    return pairs


def fetch_local_feeds(directory: Path) -> list[tuple[dict, FeedSource]]:
    """Parse local RSS/XML files from a fixture directory.

    Used for `--source-override` test/demo runs so the pipeline never
    touches the network. Each `*.xml` file is treated as one feed; the
    feed's channel title/link become the source name/url.
    """
    pairs: list[tuple[dict, FeedSource]] = []
    for path in sorted(directory.glob("*.xml")):
        parsed = feedparser.parse(str(path))
        feed_title = parsed.feed.get("title") or path.stem
        feed_link = parsed.feed.get("link") or f"https://example.invalid/{path.stem}"
        source = FeedSource(name=feed_title, url=feed_link)
        for entry in parsed.entries:
            pairs.append((entry, source))
    return pairs
