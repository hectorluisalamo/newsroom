# ABOUTME: Clusterer protocol defining the clustering interface.
# ABOUTME: Allows swapping clustering implementations without changing callers.
"""Clustering protocol for the Newsroom pipeline."""

from typing import Protocol


class Clusterer(Protocol):
    """Interface for clustering feed items into story threads."""

    def cluster(self, items: list) -> list:
        """Group feed items into clusters of related stories."""
        ...
