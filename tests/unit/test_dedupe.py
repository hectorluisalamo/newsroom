# ABOUTME: Unit tests for feed item deduplication.
# ABOUTME: Validates exact and fuzzy dedup with deterministic tie-breaking.
"""Tests for newsroom.dedupe."""

from datetime import datetime, timedelta, timezone

from newsroom.dedupe.dedupe import dedupe_items
from newsroom.models import FeedItem

_BASE_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_item(
    item_id: str,
    title: str,
    published_at: datetime,
    *,
    url: str = "https://example.com/article",
    source_name: str = "Example Source",
) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=title,
        url=url,
        source_name=source_name,
        source_feed_url="https://example.com/feed.xml",
        published_at=published_at,
        summary="A short summary.",
        raw_tags=[],
        beat="science_tech",
    )


class TestExactDedupe:
    """item_id is derived from the canonical URL upstream in normalize.py,
    so two items sharing an item_id represent the same URL surfaced by
    two different feeds/fetches."""

    def test_exact_duplicate_removed_keeping_earliest(self):
        earlier = _make_item(
            "dup-1", "Exact Duplicate Story", _BASE_TIME, url="https://a.example/x"
        )
        later = _make_item(
            "dup-1",
            "Exact Duplicate Story",
            _BASE_TIME + timedelta(hours=2),
            url="https://a.example/x",
        )
        distinct = _make_item(
            "other-1", "Completely Unrelated Headline", _BASE_TIME + timedelta(hours=1)
        )

        result = dedupe_items([later, distinct, earlier])

        ids = [item.item_id for item in result]
        assert ids.count("dup-1") == 1
        assert "other-1" in ids

        kept = next(item for item in result if item.item_id == "dup-1")
        assert kept.published_at == earlier.published_at

    def test_distinct_item_ids_all_kept(self):
        items = [
            _make_item("id-1", "First Unrelated Headline", _BASE_TIME),
            _make_item(
                "id-2",
                "Second Totally Different Headline",
                _BASE_TIME + timedelta(hours=1),
            ),
            _make_item(
                "id-3",
                "Third Unconnected Topic Headline",
                _BASE_TIME + timedelta(hours=2),
            ),
        ]

        result = dedupe_items(items)

        assert {item.item_id for item in result} == {"id-1", "id-2", "id-3"}


class TestFuzzyDedupe:
    def test_fuzzy_duplicate_at_threshold_removed(self):
        # "scientists discover new exoplanet" -> 4 words.
        # Adding one word gives Jaccard = 4/5 = 0.8, exactly at threshold.
        original = _make_item(
            "fz-1",
            "Scientists Discover New Exoplanet",
            _BASE_TIME,
            url="https://a.example/1",
        )
        near_duplicate = _make_item(
            "fz-2",
            "Scientists Discover New Exoplanet Today",
            _BASE_TIME + timedelta(hours=1),
            url="https://b.example/2",
        )

        result = dedupe_items([near_duplicate, original])

        assert len(result) == 1
        assert result[0].item_id == "fz-1"
        assert result[0].published_at == original.published_at

    def test_near_miss_below_threshold_kept(self):
        # Same 4-word base, but two extra words pull Jaccard to 4/6 = 0.667,
        # below the 0.8 threshold, so both must be kept.
        original = _make_item(
            "nm-1",
            "Scientists Discover New Exoplanet",
            _BASE_TIME,
            url="https://a.example/1",
        )
        below_threshold = _make_item(
            "nm-2",
            "Scientists Discover New Exoplanet Today Somewhere",
            _BASE_TIME + timedelta(hours=1),
            url="https://b.example/2",
        )

        result = dedupe_items([original, below_threshold])

        assert {item.item_id for item in result} == {"nm-1", "nm-2"}
