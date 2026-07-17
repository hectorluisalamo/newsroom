# ABOUTME: Unit tests for cluster ranking.
# ABOUTME: Validates composite scoring and stable sort behavior.
"""Tests for newsroom.rank."""

from datetime import datetime, timezone

from newsroom.models import BriefCluster, FeedItem
from newsroom.rank.rank import rank_clusters

_BASE_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_feed_item(item_id: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=f"Story {item_id}",
        url=f"https://example.com/{item_id}",
        source_name="Example Source",
        source_feed_url="https://example.com/feed.xml",
        published_at=_BASE_TIME,
        summary="A short summary.",
        raw_tags=[],
        beat="science_tech",
    )


def _make_cluster(
    cluster_id: str, *, recency_score: float, source_diversity: int, size: int
) -> BriefCluster:
    return BriefCluster(
        cluster_id=cluster_id,
        label=f"Cluster {cluster_id}",
        items=[_make_feed_item(f"{cluster_id}-{i}") for i in range(size)],
        centroid_keywords=[],
        recency_score=recency_score,
        source_diversity=source_diversity,
        size=size,
    )


class TestRankClusters:
    def test_empty_list_returns_empty(self):
        assert rank_clusters([]) == []

    def test_composite_order_not_just_recency(self):
        """Pin the 0.4/0.3/0.3 weighting: cluster B's diversity+size lead
        outweighs cluster A's recency lead, so recency-only order (A, C, B)
        must NOT match the actual composite order.

        Normalized scores (min-max across this list):
          A: recency=1.0, diversity_norm=0.0,   size_norm=0.0    -> 0.4
          B: recency=0.0, diversity_norm=1.0,   size_norm=1.0    -> 0.6
          C: recency=0.5, diversity_norm=0.5,   size_norm=0.444  -> 0.4833
        Composite order (descending): B, C, A.
        """
        cluster_a = _make_cluster("A", recency_score=1.0, source_diversity=1, size=1)
        cluster_b = _make_cluster("B", recency_score=0.0, source_diversity=5, size=10)
        cluster_c = _make_cluster("C", recency_score=0.5, source_diversity=3, size=5)

        result = rank_clusters([cluster_a, cluster_b, cluster_c])

        assert [c.cluster_id for c in result] == ["B", "C", "A"]

        recency_only_order = sorted(
            [cluster_a, cluster_b, cluster_c],
            key=lambda c: c.recency_score,
            reverse=True,
        )
        assert [c.cluster_id for c in result] != [
            c.cluster_id for c in recency_only_order
        ]

    def test_strictly_dominant_cluster_ranks_first(self):
        weaker = _make_cluster("weak", recency_score=0.2, source_diversity=1, size=1)
        stronger = _make_cluster(
            "strong", recency_score=0.9, source_diversity=4, size=8
        )

        result = rank_clusters([weaker, stronger])

        assert [c.cluster_id for c in result] == ["strong", "weak"]
