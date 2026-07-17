# ABOUTME: Cluster ranking for the Newsroom pipeline.
# ABOUTME: Scores and sorts clusters by recency, source diversity, and size.
"""Cluster ranking by composite score."""

from newsroom.models import BriefCluster

_RECENCY_WEIGHT = 0.4
_DIVERSITY_WEIGHT = 0.3
_SIZE_WEIGHT = 0.3


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 1.0
    return (value - minimum) / (maximum - minimum)


def rank_clusters(clusters: list[BriefCluster]) -> list[BriefCluster]:
    """Rank clusters by a composite score.

    Score = recency(0.4) + source_diversity(0.3) + size(0.3), with
    source_diversity and size min-max normalized across the given
    clusters. Returns clusters sorted by score descending (stable sort).
    """
    if not clusters:
        return []

    diversities = [c.source_diversity for c in clusters]
    sizes = [c.size for c in clusters]
    min_diversity, max_diversity = min(diversities), max(diversities)
    min_size, max_size = min(sizes), max(sizes)

    def score(cluster: BriefCluster) -> float:
        diversity_norm = _normalize(
            cluster.source_diversity, min_diversity, max_diversity
        )
        size_norm = _normalize(cluster.size, min_size, max_size)
        return (
            _RECENCY_WEIGHT * cluster.recency_score
            + _DIVERSITY_WEIGHT * diversity_norm
            + _SIZE_WEIGHT * size_norm
        )

    return sorted(clusters, key=score, reverse=True)
