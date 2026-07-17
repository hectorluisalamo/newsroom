# ABOUTME: Text processing utilities for the Newsroom pipeline.
# ABOUTME: Provides HTML stripping, whitespace normalization, and shared helpers.
"""Text cleaning and normalization utilities."""

import re

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(raw: str) -> str:
    """Remove HTML tags from a string."""
    return _TAG_RE.sub("", raw)


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and newlines into single spaces."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to a maximum character count."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
