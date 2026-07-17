# ABOUTME: TF-IDF based clustering implementation.
# ABOUTME: Uses scikit-learn for vectorization and agglomerative clustering.
"""TF-IDF + agglomerative clustering implementation."""

import hashlib
from collections import defaultdict

from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from newsroom.models import BriefCluster, ClusterConfig, FeedItem


def _cluster_id(items: list[FeedItem]) -> str:
    joined = "".join(sorted(item.item_id for item in items))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _recency_score(items: list[FeedItem], oldest, newest) -> float:
    latest_in_cluster = max(item.published_at for item in items)
    span = (newest - oldest).total_seconds()
    if span <= 0:
        return 1.0
    return (latest_in_cluster - oldest).total_seconds() / span


class TfidfClusterer:
    """Cluster feed items using TF-IDF vectorization and agglomerative clustering.

    All parameters are loaded from config/cluster.yaml. Implements the
    Clusterer protocol.
    """

    def __init__(self, config: ClusterConfig) -> None:
        """Initialize the clusterer with configuration parameters."""
        self._tfidf_config = config.tfidf
        self._clustering_config = config.clustering
        self._keywords_config = config.keywords
        stop_words = set(ENGLISH_STOP_WORDS) | {
            w.lower() for w in self._tfidf_config.extra_stop_words
        }
        self._vectorizer = TfidfVectorizer(
            max_features=self._tfidf_config.max_features,
            ngram_range=tuple(self._tfidf_config.ngram_range),
            stop_words=sorted(stop_words),
            min_df=self._tfidf_config.min_df,
        )

    def _top_keywords(self, row, feature_names) -> list[str]:
        generic = {w.lower() for w in self._keywords_config.generic_filter}
        ranked = sorted(
            ((score, feature_names[idx]) for idx, score in enumerate(row) if score > 0),
            reverse=True,
        )
        keywords: list[str] = []
        for _, term in ranked:
            if term.lower() in generic:
                continue
            keywords.append(term)
            if len(keywords) == self._keywords_config.top_n:
                break
        return keywords

    def cluster(self, items: list[FeedItem]) -> list[BriefCluster]:
        """Group feed items into BriefClusters based on TF-IDF similarity."""
        if not items:
            return []

        oldest = min(item.published_at for item in items)
        newest = max(item.published_at for item in items)

        if len(items) == 1:
            item = items[0]
            return [
                BriefCluster(
                    cluster_id=_cluster_id(items),
                    label=item.title,
                    items=items,
                    centroid_keywords=[],
                    recency_score=1.0,
                    source_diversity=1,
                    size=1,
                )
            ]

        texts = [f"{item.title} {item.summary}" for item in items]
        matrix = self._vectorizer.fit_transform(texts)
        feature_names = self._vectorizer.get_feature_names_out()

        if matrix.shape[1] == 0:
            labels = list(range(len(items)))
        else:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self._clustering_config.distance_threshold,
                linkage=self._clustering_config.linkage,
                metric="cosine",
            )
            labels = clustering.fit_predict(matrix.toarray())

        groups: dict[int, list[int]] = defaultdict(list)
        for row_idx, label in enumerate(labels):
            groups[label].append(row_idx)

        dense = matrix.toarray() if matrix.shape[1] else None

        clusters: list[BriefCluster] = []
        for row_indices in groups.values():
            group_items = [items[i] for i in row_indices]
            if dense is not None:
                centroid = dense[row_indices].mean(axis=0)
                keywords = self._top_keywords(centroid, feature_names)
            else:
                keywords = []
            label = keywords[0] if keywords else group_items[0].title
            clusters.append(
                BriefCluster(
                    cluster_id=_cluster_id(group_items),
                    label=label,
                    items=group_items,
                    centroid_keywords=keywords,
                    recency_score=_recency_score(group_items, oldest, newest),
                    source_diversity=len({item.source_name for item in group_items}),
                    size=len(group_items),
                )
            )
        return clusters
