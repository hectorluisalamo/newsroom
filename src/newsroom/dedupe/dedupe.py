# ABOUTME: Deduplication logic for feed items.
# ABOUTME: Removes exact duplicates by ID and fuzzy duplicates by title similarity.
"""Feed item deduplication."""


def dedupe_items(items: list) -> list:
    """Remove duplicate feed items.

    Phase 1: exact dedup by item_id.
    Phase 2: fuzzy dedup by title similarity (Jaccard on word sets,
    threshold 0.8). Keeps the item with the earliest published_at on ties.
    """
    raise NotImplementedError
