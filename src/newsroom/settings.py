# ABOUTME: Configuration loader for sources, QA thresholds, cluster params, and voices.
# ABOUTME: Reads YAML and Markdown configs from the config/ directory.
"""Configuration loading for the Newsroom CLI."""

from pathlib import Path


def load_sources(beat: str, config_dir: Path) -> list:
    """Load RSS feed sources for a given beat from config/sources.yaml."""
    raise NotImplementedError


def load_qa_config(config_dir: Path) -> dict:
    """Load QA check thresholds and phrase lists from config/qa.yaml."""
    raise NotImplementedError


def load_cluster_config(config_dir: Path) -> dict:
    """Load TF-IDF and clustering parameters from config/cluster.yaml."""
    raise NotImplementedError


def load_voice(beat: str, config_dir: Path) -> str:
    """Load and parse the voice constitution markdown for a given beat."""
    raise NotImplementedError
