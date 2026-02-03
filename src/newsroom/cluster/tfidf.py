# ABOUTME: TF-IDF based clustering implementation.
# ABOUTME: Uses scikit-learn for vectorization and agglomerative clustering.
"""TF-IDF + agglomerative clustering implementation."""


class TfidfClusterer:
    """Cluster feed items using TF-IDF vectorization and agglomerative clustering.

    All parameters are loaded from config/cluster.yaml. Implements the
    Clusterer protocol.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the clusterer with configuration parameters."""
        raise NotImplementedError

    def cluster(self, items: list) -> list:
        """Group feed items into BriefClusters based on TF-IDF similarity."""
        raise NotImplementedError
