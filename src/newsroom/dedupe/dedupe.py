# ABOUTME: Deduplication logic for feed items.
# ABOUTME: Removes exact duplicates by ID and fuzzy duplicates by title similarity.
"""Feed item deduplication."""

import re

from newsroom.models import FeedItem

_WORD_RE = re.compile(r"[a-z0-9]+")

_FUZZY_THRESHOLD = 0.8


def _title_words(title: str) -> set[str]:
    return set(_WORD_RE.findall(title.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def dedupe_items(items: list[FeedItem]) -> list[FeedItem]:
    """Remove duplicate feed items.

    Phase 1: exact dedup by item_id (earliest published_at wins on
    collision). Phase 2: fuzzy dedup by title similarity (Jaccard on
    word sets, threshold 0.8). Keeps the item with the earliest
    published_at on ties.
    """
    exact: dict[str, FeedItem] = {}
    for item in items:
        existing = exact.get(item.item_id)
        if existing is None or item.published_at < existing.published_at:
            exact[item.item_id] = item

    remaining = sorted(exact.values(), key=lambda item: item.published_at)

    kept: list[FeedItem] = []
    kept_words: list[set[str]] = []
    for item in remaining:
        words = _title_words(item.title)
        if any(_jaccard(words, other) >= _FUZZY_THRESHOLD for other in kept_words):
            continue
        kept.append(item)
        kept_words.append(words)

    return kept
