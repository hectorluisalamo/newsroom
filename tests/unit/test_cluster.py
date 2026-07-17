# ABOUTME: Unit tests for TF-IDF clustering.
# ABOUTME: Validates cluster formation, keyword extraction, and deterministic IDs.
"""Tests for newsroom.cluster."""

from datetime import datetime, timezone

from newsroom.cluster.tfidf import TfidfClusterer
from newsroom.models import ClusterConfig, FeedItem

_BASE_TIME = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_cluster_config(**overrides) -> ClusterConfig:
    defaults = {
        "tfidf": {
            "max_features": 5000,
            "ngram_range": [1, 2],
            "stop_words": "english",
            "min_df": 2,
            "extra_stop_words": [],
        },
        "clustering": {
            "method": "agglomerative",
            "distance_threshold": 0.7,
            "linkage": "average",
        },
        "keywords": {
            "top_n": 5,
            "generic_filter": [],
        },
    }
    defaults.update(overrides)
    return ClusterConfig(**defaults)


def _make_item(item_id: str, title: str, summary: str) -> FeedItem:
    return FeedItem(
        item_id=item_id,
        title=title,
        url=f"https://example.com/{item_id}",
        source_name="Example Source",
        source_feed_url="https://example.com/feed.xml",
        published_at=_BASE_TIME,
        summary=summary,
        raw_tags=[],
        beat="science_tech",
    )


class TestEmptyVocabularyFallback:
    """With min_df=2, a corpus where no term repeats across documents
    leaves TfidfVectorizer.fit_transform with nothing to vectorize.
    sklearn raises ValueError("After pruning, no terms remain...") in
    that case rather than returning a zero-column matrix, so this path
    must be caught explicitly and routed to the same singleton-cluster
    fallback used when the matrix comes back with zero columns.
    """

    def test_disjoint_tiny_input_falls_back_to_singletons(self):
        clusterer = TfidfClusterer(_make_cluster_config())
        items = [
            _make_item("a", "Zzyxq Wobblesnort", ""),
            _make_item("b", "Blivet Trentworth", ""),
        ]

        clusters = clusterer.cluster(items)

        assert len(clusters) == 2
        assert {c.size for c in clusters} == {1}
        assert {item.item_id for c in clusters for item in c.items} == {"a", "b"}

    def test_similar_input_still_clusters_together(self):
        """Sanity check that the fix didn't disable real clustering: two
        near-identical items with repeated vocabulary should still merge
        into a single cluster rather than falling back to singletons."""
        clusterer = TfidfClusterer(_make_cluster_config())
        items = [
            _make_item(
                "a",
                "Quantum Computing Breakthrough Announced",
                "Researchers announce quantum computing breakthrough today.",
            ),
            _make_item(
                "b",
                "Quantum Computing Breakthrough Confirmed",
                "Independent team confirms quantum computing breakthrough.",
            ),
        ]

        clusters = clusterer.cluster(items)

        assert len(clusters) == 1
        assert clusters[0].size == 2
