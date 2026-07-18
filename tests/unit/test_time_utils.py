# ABOUTME: Unit tests for time utility functions.
# ABOUTME: Validates duration parsing and timestamp normalization.
"""Tests for newsroom.utils.time_utils."""

from datetime import datetime, timedelta, timezone

import pytest

from newsroom.utils.time_utils import normalize_timestamp, parse_since

_FALLBACK = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


class TestParseSinceValid:
    def test_hours(self):
        assert parse_since("48h") == timedelta(hours=48)

    def test_days(self):
        assert parse_since("2d") == timedelta(days=2)

    def test_minutes(self):
        assert parse_since("90m") == timedelta(minutes=90)

    def test_zero_hours_is_valid(self):
        assert parse_since("0h") == timedelta(0)

    def test_strips_leading_and_trailing_whitespace(self):
        assert parse_since("  48h  ") == timedelta(hours=48)


class TestParseSinceInvalid:
    @pytest.mark.parametrize(
        "since",
        ["48", "48x", "", "h", "1.5h", "-5h"],
    )
    def test_invalid_inputs_raise_value_error(self, since):
        with pytest.raises(ValueError, match="Invalid since window"):
            parse_since(since)

    def test_uppercase_unit_is_rejected(self):
        with pytest.raises(ValueError, match="Invalid since window"):
            parse_since("48H")


class TestNormalizeTimestampRfc822:
    def test_rfc822_pubdate_is_utc_aware(self):
        result = normalize_timestamp(
            "Wed, 15 Jan 2025 12:00:00 GMT", fallback=_FALLBACK
        )

        assert result.tzinfo is not None
        assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_rfc822_with_non_utc_offset_is_converted(self):
        result = normalize_timestamp(
            "Wed, 15 Jan 2025 12:00:00 +0500", fallback=_FALLBACK
        )

        assert result.tzinfo is not None
        assert result == datetime(2025, 1, 15, 7, 0, 0, tzinfo=timezone.utc)


class TestNormalizeTimestampIso8601:
    def test_iso8601_with_z_suffix_is_utc_aware(self):
        result = normalize_timestamp("2025-01-15T12:00:00Z", fallback=_FALLBACK)

        assert result.tzinfo is not None
        assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_iso8601_with_non_utc_offset_is_converted(self):
        """A tz-aware but non-UTC input must be converted, not merely
        re-labeled — assert the actual instant, not just the offset."""
        result = normalize_timestamp("2025-01-15T12:00:00+05:00", fallback=_FALLBACK)

        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)
        assert result == datetime(2025, 1, 15, 7, 0, 0, tzinfo=timezone.utc)

    def test_iso8601_naive_gets_utc_attached(self):
        result = normalize_timestamp("2025-01-15T12:00:00", fallback=_FALLBACK)

        assert result.tzinfo is not None
        assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


class TestNormalizeTimestampFallback:
    def test_unparseable_raw_falls_back(self):
        result = normalize_timestamp("not a real timestamp", fallback=_FALLBACK)

        assert result == _FALLBACK

    def test_naive_fallback_is_normalized_to_utc(self):
        naive_fallback = datetime(2026, 3, 1, 8, 30, 0)

        result = normalize_timestamp("garbage", fallback=naive_fallback)

        assert result.tzinfo is not None
        assert result == datetime(2026, 3, 1, 8, 30, 0, tzinfo=timezone.utc)

    def test_tz_aware_non_utc_fallback_is_converted(self):
        aware_fallback = datetime(
            2026, 3, 1, 8, 30, 0, tzinfo=timezone(timedelta(hours=-4))
        )

        result = normalize_timestamp("garbage", fallback=aware_fallback)

        assert result.tzinfo is not None
        assert result.utcoffset() == timedelta(0)
        assert result == datetime(2026, 3, 1, 12, 30, 0, tzinfo=timezone.utc)

    def test_empty_raw_falls_back(self):
        result = normalize_timestamp("", fallback=_FALLBACK)

        assert result == _FALLBACK
