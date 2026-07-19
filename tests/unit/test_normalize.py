# ABOUTME: Unit tests for feed item normalization.
# ABOUTME: Validates HTML stripping, date parsing, and filtering logic.
"""Tests for newsroom.normalize."""

from datetime import datetime, timezone

import pytest

from newsroom.models import FeedSource
from newsroom.normalize.normalize import (
    _canonicalize_url,
    normalize_all,
    normalize_entry,
)

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_SOURCE = FeedSource(name="Example Source", url="https://example.com/feed.xml")


class TestCanonicalizeUrl:
    def test_strips_fragment(self):
        assert (
            _canonicalize_url("https://example.com/article#section-2")
            == "https://example.com/article"
        )

    def test_strips_single_trailing_slash(self):
        assert (
            _canonicalize_url("https://example.com/article/")
            == "https://example.com/article"
        )

    def test_strips_both_fragment_and_trailing_slash(self):
        assert (
            _canonicalize_url("https://example.com/article/#top")
            == "https://example.com/article"
        )


class TestNormalizeEntryRequiredFields:
    def test_missing_link_returns_none(self):
        entry = {"title": "Headline"}

        assert normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW) is None

    def test_missing_title_returns_none(self):
        entry = {"link": "https://example.com/article"}

        assert normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW) is None

    def test_empty_link_returns_none(self):
        entry = {"link": "", "title": "Headline"}

        assert normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW) is None

    def test_link_that_fails_model_validation_returns_none(self):
        """A present, non-empty link that is not a valid HttpUrl passes the
        early truthiness check but fails FeedItem construction, exercising
        the ValidationError -> None branch rather than the missing-field
        branch above."""
        entry = {"link": "not-a-valid-url", "title": "Headline"}

        assert normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW) is None


class TestNormalizeEntryTextCleaning:
    def test_html_stripped_and_whitespace_normalized_in_title(self):
        entry = {
            "link": "https://example.com/article",
            "title": "<b>Big   News</b>\n\nToday",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.title == "Big News Today"

    def test_html_stripped_and_whitespace_normalized_in_summary(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "summary": "<p>Some   summary\ntext</p>",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.summary == "Some summary text"

    def test_summary_truncated_to_500_chars(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "summary": "x" * 600,
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert len(item.summary) == 500

    def test_summary_falls_back_to_description(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "description": "Only a description here.",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.summary == "Only a description here."

    def test_empty_summary_falls_back_to_description(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "summary": "",
            "description": "Fallback description.",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.summary == "Fallback description."


class TestNormalizeEntryItemId:
    def test_item_id_is_sha256_of_canonical_url(self):
        entry = {"link": "https://example.com/article", "title": "Headline"}

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        # Hardcoded digest for "https://example.com/article", computed once,
        # so this test can't drift into re-deriving the implementation.
        expected = "632538290468e7a39c06323c9e3ae98f31072d641cbb37ea37917f56bbeb5539"
        assert item.item_id == expected

    def test_url_with_and_without_fragment_yield_same_id(self):
        plain_entry = {"link": "https://example.com/article", "title": "Headline"}
        fragment_entry = {
            "link": "https://example.com/article#discussion",
            "title": "Headline",
        }

        plain_item = normalize_entry(
            plain_entry, _SOURCE, beat="science_tech", now=_NOW
        )
        fragment_item = normalize_entry(
            fragment_entry, _SOURCE, beat="science_tech", now=_NOW
        )

        assert plain_item.item_id == fragment_item.item_id


class TestNormalizeEntryPublishedDate:
    def test_missing_published_falls_back_to_now(self):
        entry = {"link": "https://example.com/article", "title": "Headline"}

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.published_at == _NOW

    def test_present_published_is_parsed(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "published": "2025-06-01T09:00:00Z",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.published_at == datetime(2025, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

    def test_missing_published_falls_back_to_updated(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "updated": "2025-06-01T09:00:00Z",
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.published_at == datetime(2025, 6, 1, 9, 0, 0, tzinfo=timezone.utc)


class TestNormalizeEntryTags:
    def test_tags_extracted_from_dicts_with_truthy_term(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "tags": [{"term": "ai"}, {"term": "space"}],
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.raw_tags == ["ai", "space"]

    def test_tags_without_truthy_term_are_skipped(self):
        entry = {
            "link": "https://example.com/article",
            "title": "Headline",
            "tags": [{"term": ""}, {"no_term": "x"}, "not-a-dict", {"term": "science"}],
        }

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.raw_tags == ["science"]

    def test_missing_tags_key_yields_empty_list(self):
        entry = {"link": "https://example.com/article", "title": "Headline"}

        item = normalize_entry(entry, _SOURCE, beat="science_tech", now=_NOW)

        assert item.raw_tags == []


def _entry(url: str, published: str, title: str = "Headline") -> dict:
    return {"link": url, "title": title, "published": published}


class TestNormalizeAll:
    def test_mismatched_lengths_raise_value_error(self):
        entries = [_entry("https://example.com/1", "2026-01-15T00:00:00Z")]
        sources = [_SOURCE, _SOURCE]

        with pytest.raises(ValueError):
            normalize_all(entries, sources, beat="science_tech", since="48h", now=_NOW)

    def test_items_older_than_since_window_are_filtered_out(self):
        recent = _entry("https://example.com/recent", "2026-01-15T00:00:00Z")
        stale = _entry("https://example.com/stale", "2026-01-10T00:00:00Z")
        entries = [recent, stale]
        sources = [_SOURCE, _SOURCE]

        result = normalize_all(
            entries, sources, beat="science_tech", since="48h", now=_NOW
        )

        urls = [str(item.url) for item in result]
        assert urls == ["https://example.com/recent"]

    def test_item_exactly_at_cutoff_is_kept(self):
        """The filter is `published_at < cutoff`, so an item published at
        exactly the cutoff instant must survive, not be dropped."""
        at_cutoff = _entry("https://example.com/at-cutoff", "2026-01-13T12:00:00Z")
        entries = [at_cutoff]
        sources = [_SOURCE]

        result = normalize_all(
            entries, sources, beat="science_tech", since="48h", now=_NOW
        )

        urls = [str(item.url) for item in result]
        assert urls == ["https://example.com/at-cutoff"]

    def test_result_sorted_ascending_by_published_at(self):
        later = _entry("https://example.com/later", "2026-01-15T10:00:00Z")
        earlier = _entry("https://example.com/earlier", "2026-01-14T10:00:00Z")
        entries = [later, earlier]
        sources = [_SOURCE, _SOURCE]

        result = normalize_all(
            entries, sources, beat="science_tech", since="7d", now=_NOW
        )

        assert [str(item.url) for item in result] == [
            "https://example.com/earlier",
            "https://example.com/later",
        ]

    def test_none_normalized_entries_are_skipped(self):
        valid = _entry("https://example.com/valid", "2026-01-15T00:00:00Z")
        invalid = {"title": "No link here"}
        entries = [valid, invalid]
        sources = [_SOURCE, _SOURCE]

        result = normalize_all(
            entries, sources, beat="science_tech", since="48h", now=_NOW
        )

        assert len(result) == 1
        assert str(result[0].url) == "https://example.com/valid"
