# ABOUTME: Unit tests for the deterministic time anchor resolution.
# ABOUTME: Validates cli_now, NEWSROOM_NOW env var, and UTC fallback behavior.
"""Tests for newsroom.time_anchor."""

from datetime import datetime, timezone

import pytest

from newsroom.time_anchor import resolve_now

_EXPECTED_UTC = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# cli_now parsing
# ---------------------------------------------------------------------------


class TestCliNow:
    def test_z_suffix(self):
        result = resolve_now("2026-01-15T12:00:00Z")
        assert result == _EXPECTED_UTC
        assert result.tzinfo is not None

    def test_plus_zero_offset(self):
        result = resolve_now("2026-01-15T12:00:00+00:00")
        assert result == _EXPECTED_UTC

    def test_z_and_plus_zero_are_identical(self):
        from_z = resolve_now("2026-01-15T12:00:00Z")
        from_offset = resolve_now("2026-01-15T12:00:00+00:00")
        assert from_z == from_offset

    def test_non_utc_offset_converted(self):
        result = resolve_now("2026-01-15T07:00:00-05:00")
        assert result == _EXPECTED_UTC

    def test_naive_string_treated_as_utc(self):
        result = resolve_now("2026-01-15T12:00:00")
        assert result == _EXPECTED_UTC
        assert result.tzinfo is not None

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_now("not-a-date")

    def test_result_is_always_utc_aware(self):
        result = resolve_now("2026-06-01T08:30:00+03:00")
        assert result.tzinfo is not None
        assert result.utcoffset().total_seconds() == 0


# ---------------------------------------------------------------------------
# NEWSROOM_NOW env var
# ---------------------------------------------------------------------------


class TestEnvVar:
    def test_env_var_used_when_cli_now_is_none(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_NOW", "2026-01-15T12:00:00Z")
        result = resolve_now(None)
        assert result == _EXPECTED_UTC

    def test_env_var_with_offset(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_NOW", "2026-01-15T07:00:00-05:00")
        result = resolve_now(None)
        assert result == _EXPECTED_UTC

    def test_empty_env_var_ignored(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_NOW", "")
        result = resolve_now(None)
        # Falls through to datetime.now(UTC); just verify it's UTC-aware
        assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# Fallback to datetime.now(UTC)
# ---------------------------------------------------------------------------


class TestFallback:
    def test_no_cli_no_env_returns_utc_now(self, monkeypatch):
        monkeypatch.delenv("NEWSROOM_NOW", raising=False)
        result = resolve_now(None)
        assert result.tzinfo is not None
        now = datetime.now(timezone.utc)
        delta = abs((now - result).total_seconds())
        assert delta < 2.0


# ---------------------------------------------------------------------------
# Precedence: cli_now > NEWSROOM_NOW
# ---------------------------------------------------------------------------


class TestPrecedence:
    def test_cli_now_overrides_env_var(self, monkeypatch):
        monkeypatch.setenv("NEWSROOM_NOW", "2025-06-01T00:00:00Z")
        result = resolve_now("2026-01-15T12:00:00Z")
        assert result == _EXPECTED_UTC
