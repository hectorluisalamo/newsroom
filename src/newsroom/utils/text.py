# ABOUTME: Text processing utilities for the Newsroom pipeline.
# ABOUTME: Provides HTML stripping, whitespace normalization, and shared helpers.
"""Text cleaning and normalization utilities."""


def strip_html(raw: str) -> str:
    """Remove HTML tags from a string."""
    raise NotImplementedError


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and newlines into single spaces."""
    raise NotImplementedError


def truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to a maximum character count."""
    raise NotImplementedError
