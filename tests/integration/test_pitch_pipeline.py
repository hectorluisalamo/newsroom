# ABOUTME: Integration tests for the pitch pipeline.
# ABOUTME: Validates ingestion through pitch generation using fixture data.
"""Integration tests for the pitch pipeline (ingestion -> pitches)."""

import json
from pathlib import Path

import pytest

from newsroom import commands

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXTURE_DIR = _REPO_ROOT / "fixtures" / "science_tech"
_CONFIG_EXAMPLE = _REPO_ROOT / "config.example"
_FIXED_NOW = "2026-01-15T12:00:00Z"


def _run_pitch_cmd(tmp_path: Path) -> Path:
    """Run pitch_cmd against the fixture feeds and return the beat's output dir."""
    commands.pitch_cmd(
        beat="science_tech",
        since="48h",
        now=_FIXED_NOW,
        out_dir=tmp_path,
        source_override=str(_FIXTURE_DIR),
        verbose=False,
        config_dir=_CONFIG_EXAMPLE,
    )
    return tmp_path / "2026-01-15" / "science_tech"


class TestPitchPipeline:
    """End-to-end: ingest -> normalize -> dedupe -> cluster -> rank -> pitch."""

    def test_writes_brief_and_pitches_files(self, tmp_path):
        beat_dir = _run_pitch_cmd(tmp_path)
        assert (beat_dir / "brief.json").exists()
        assert (beat_dir / "brief.md").exists()
        assert (beat_dir / "pitches.json").exists()
        assert (beat_dir / "pitches.md").exists()

    def test_brief_pack_has_ingested_and_clustered_items(self, tmp_path):
        beat_dir = _run_pitch_cmd(tmp_path)
        brief = json.loads((beat_dir / "brief.json").read_text())

        assert brief["beat"] == "science_tech"
        assert brief["date"] == "2026-01-15"
        assert brief["total_items_ingested"] > 0
        # No fuzzy/exact dupes across the fixture feeds, so dedupe preserves count.
        assert brief["total_items_after_dedupe"] > 0
        assert brief["total_items_after_dedupe"] <= brief["total_items_ingested"]
        assert len(brief["clusters"]) >= 3

        for cluster in brief["clusters"]:
            assert cluster["size"] == len(cluster["items"])
            assert 0.0 <= cluster["recency_score"] <= 1.0

    def test_pitch_set_has_exactly_three_valid_pitches(self, tmp_path):
        beat_dir = _run_pitch_cmd(tmp_path)
        pitch_set = json.loads((beat_dir / "pitches.json").read_text())

        assert pitch_set["beat"] == "science_tech"
        assert pitch_set["date"] == "2026-01-15"
        assert len(pitch_set["pitches"]) == 3

        pitch_ids = {p["pitch_id"] for p in pitch_set["pitches"]}
        assert len(pitch_ids) == 3

        for pitch in pitch_set["pitches"]:
            assert len(pitch["source_urls"]) >= 3
            assert pitch["title"]
            assert pitch["thesis_angle"]
            assert pitch["cluster_id"]
            assert pitch["angle"]

    def test_deterministic_across_repeated_runs(self, tmp_path):
        """Same --now and same fixtures must produce byte-identical pitch output."""
        beat_dir_a = _run_pitch_cmd(tmp_path / "run_a")
        beat_dir_b = _run_pitch_cmd(tmp_path / "run_b")

        pitches_a = (beat_dir_a / "pitches.json").read_text()
        pitches_b = (beat_dir_b / "pitches.json").read_text()
        assert pitches_a == pitches_b

    def test_source_override_never_touches_network(self, tmp_path, monkeypatch):
        """Guard against silently falling back to a live network fetch."""
        import httpx

        def _fail(*args, **kwargs):
            raise AssertionError(
                "pitch_cmd must not make network calls with --source-override"
            )

        monkeypatch.setattr(httpx, "get", _fail)
        beat_dir = _run_pitch_cmd(tmp_path)
        assert (beat_dir / "pitches.json").exists()

    def test_zero_items_after_since_window_raises(self, tmp_path):
        """An unreachable --since window yields no items, which cannot form pitches."""
        with pytest.raises(ValueError, match="zero clusters"):
            commands.pitch_cmd(
                beat="science_tech",
                since="1m",
                now=_FIXED_NOW,
                out_dir=tmp_path,
                source_override=str(_FIXTURE_DIR),
                verbose=False,
                config_dir=_CONFIG_EXAMPLE,
            )
