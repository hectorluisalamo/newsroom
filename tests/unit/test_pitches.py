# ABOUTME: Unit tests for algorithmic pitch generation.
# ABOUTME: Validates pitch differentiation, source minimums, and risk flags.
"""Tests for newsroom.pitches."""

from datetime import date, datetime, timezone

import pytest

from newsroom.models import BriefCluster, BriefPack, FeedItem
from newsroom.pitches.pitches import generate_pitches

_NOW_UTC = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_feed_item(item_id: str, url: str, title: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=title,
        url=url,
        source_name="Example",
        source_feed_url="https://example.com/feed.xml",
        published_at=_NOW_UTC,
        summary="A short summary.",
        raw_tags=["science"],
        beat="science_tech",
    )


def _make_cluster(cluster_id: str, label: str, urls: list[str]) -> BriefCluster:
    """Build a BriefCluster with one FeedItem per URL given (URLs may repeat)."""
    items = [
        _make_feed_item(f"{cluster_id}-item-{i}", url, f"{label} #{i}")
        for i, url in enumerate(urls)
    ]
    return BriefCluster(
        cluster_id=cluster_id,
        label=label,
        items=items,
        centroid_keywords=["k1", "k2", "k3", "k4", "k5"],
        recency_score=0.9,
        source_diversity=len(set(urls)),
        size=len(items),
    )


def _make_brief_pack(clusters: list[BriefCluster]) -> BriefPack:
    return BriefPack(
        beat="science_tech",
        date=date(2025, 1, 15),
        since="48h",
        total_items_ingested=sum(c.size for c in clusters),
        total_items_after_dedupe=sum(c.size for c in clusters),
        clusters=clusters,
        generated_at=_NOW_UTC,
    )


class TestThinClusterHandling:
    """A cluster with fewer than 3 distinct source URLs cannot back a Pitch
    (Pitch.source_urls requires >=3), so generate_pitches must skip it rather
    than crash or fabricate sources."""

    def test_top_ranked_thin_cluster_is_skipped_not_crashed(self):
        """A top-ranked cluster with only 2 distinct URLs must not raise; the
        next qualifying clusters should be used to fill out the 3 pitches."""
        thin_top = _make_cluster(
            "thin-top",
            "Thin story",
            ["https://a.example.com/1", "https://a.example.com/2"],
        )
        healthy_1 = _make_cluster(
            "healthy-1",
            "Healthy story one",
            [
                "https://b.example.com/1",
                "https://b.example.com/2",
                "https://b.example.com/3",
            ],
        )
        healthy_2 = _make_cluster(
            "healthy-2",
            "Healthy story two",
            [
                "https://c.example.com/1",
                "https://c.example.com/2",
                "https://c.example.com/3",
            ],
        )
        healthy_3 = _make_cluster(
            "healthy-3",
            "Healthy story three",
            [
                "https://d.example.com/1",
                "https://d.example.com/2",
                "https://d.example.com/3",
            ],
        )
        brief = _make_brief_pack([thin_top, healthy_1, healthy_2, healthy_3])

        pitch_set = generate_pitches(brief, n=3)

        assert len(pitch_set.pitches) == 3
        used_cluster_ids = {p.cluster_id for p in pitch_set.pitches}
        assert "thin-top" not in used_cluster_ids
        assert used_cluster_ids == {"healthy-1", "healthy-2", "healthy-3"}
        for pitch in pitch_set.pitches:
            assert len(pitch.source_urls) >= 3

    def test_cluster_with_duplicate_urls_counts_as_thin(self):
        """Distinct URL count matters, not item count: a 3-item cluster that
        shares URLs across items still has fewer than 3 distinct sources."""
        thin_duplicate = _make_cluster(
            "thin-dupe",
            "Duplicated coverage",
            [
                "https://a.example.com/1",
                "https://a.example.com/1",
                "https://a.example.com/1",
            ],
        )
        healthy_1 = _make_cluster(
            "healthy-1",
            "Healthy story one",
            [
                "https://b.example.com/1",
                "https://b.example.com/2",
                "https://b.example.com/3",
            ],
        )
        healthy_2 = _make_cluster(
            "healthy-2",
            "Healthy story two",
            [
                "https://c.example.com/1",
                "https://c.example.com/2",
                "https://c.example.com/3",
            ],
        )
        healthy_3 = _make_cluster(
            "healthy-3",
            "Healthy story three",
            [
                "https://d.example.com/1",
                "https://d.example.com/2",
                "https://d.example.com/3",
            ],
        )
        brief = _make_brief_pack([thin_duplicate, healthy_1, healthy_2, healthy_3])

        pitch_set = generate_pitches(brief, n=3)

        used_cluster_ids = {p.cluster_id for p in pitch_set.pitches}
        assert "thin-dupe" not in used_cluster_ids

    def test_all_clusters_thin_raises_clear_domain_error(self):
        """When no cluster can back a valid pitch, raise a clear ValueError
        (mirroring the existing zero-clusters case) instead of letting a
        pydantic ValidationError propagate."""
        thin_only = _make_cluster(
            "thin-only",
            "Thin story",
            ["https://a.example.com/1", "https://a.example.com/2"],
        )
        brief = _make_brief_pack([thin_only])

        with pytest.raises(ValueError, match="source"):
            generate_pitches(brief, n=3)

    def test_thin_cluster_among_two_falls_back_to_healthy_only(self):
        """With one thin and one healthy cluster (2 total), the fallback
        logic must not attempt to build a pitch from the thin cluster."""
        thin = _make_cluster(
            "thin",
            "Thin story",
            ["https://a.example.com/1"],
        )
        healthy = _make_cluster(
            "healthy",
            "Healthy story",
            [
                "https://b.example.com/1",
                "https://b.example.com/2",
                "https://b.example.com/3",
            ],
        )
        brief = _make_brief_pack([thin, healthy])

        pitch_set = generate_pitches(brief, n=3)

        assert len(pitch_set.pitches) == 3
        assert all(p.cluster_id == "healthy" for p in pitch_set.pitches)
