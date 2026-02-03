# ABOUTME: RSS feed fetching and parsing using httpx and feedparser.
# ABOUTME: Handles timeouts, retries, and graceful per-feed failure.
"""RSS feed ingestion for the Newsroom pipeline."""


def fetch_feed(url: str, timeout: int = 30) -> dict:
    """Fetch and parse a single RSS feed.

    Uses sync httpx with explicit timeout and one retry on
    transient failure (timeout, 5xx).
    """
    raise NotImplementedError


def fetch_all_feeds(sources: list) -> list:
    """Fetch all RSS feeds for a list of sources.

    Handles per-feed failures gracefully: logs a warning and
    continues with remaining feeds.
    """
    raise NotImplementedError
