# ABOUTME: Integration tests for the QA pipeline.
# ABOUTME: Hand-builds draft.json fixtures and exercises qa_cmd end-to-end.
"""Integration tests for the QA pipeline (draft.json -> report.json)."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from newsroom import commands
from newsroom.models import Draft
from newsroom.render.render import render_draft_json

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_EXAMPLE = _REPO_ROOT / "config.example"
_FIXED_GENERATED_AT = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _write_draft(tmp_path: Path, body_md: str, sources: list[str]) -> Path:
    """Hand-build a draft.json under out_dir/2026-01-15/science_tech/."""
    beat_dir = tmp_path / "2026-01-15" / "science_tech"
    beat_dir.mkdir(parents=True, exist_ok=True)

    draft = Draft(
        beat="science_tech",
        date="2026-01-15",
        pitch_id="test-pitch-1",
        title="Test Draft",
        body_md=body_md,
        word_count=len(body_md.split()),
        sources=sources,
        guidance_used="Keep it sharp and cite every claim.",
        model_id="fake-model-v1",
        generated_at=_FIXED_GENERATED_AT,
        token_usage=None,
    )
    (beat_dir / "draft.json").write_text(render_draft_json(draft))
    return beat_dir


class TestQAPipeline:
    """End-to-end: hand-built draft.json -> qa_cmd -> report.json."""

    def test_draft_with_violations_fails_qa(self, tmp_path):
        # Paragraph 1: a stat with no [src:N] marker in the same paragraph.
        # Paragraph 2: a taboo phrase (config.example/voices/science_tech.md
        # lists "Revolutionary" under Taboo Phrases) + an orphaned [src:9]
        # marker (sources has only 3 entries).
        # Paragraph 3: heavily hedged sentences pushing the hedging ratio
        # over the 0.15 max_ratio threshold.
        body_md = (
            "The new chip achieves a 45% improvement in efficiency over "
            "last year's model.\n\n"
            "Revolutionary claims aside, engineers point to incremental "
            "gains rather than a sudden leap [src:9].\n\n"
            "It's unclear whether the approach scales. Some experts say "
            "the results are overstated. Arguably, the gains are real. "
            "Perhaps not. But the field moves forward regardless [src:1]."
        )
        sources = [
            "https://example.com/source-one",
            "https://example.com/source-two",
            "https://example.com/source-three",
        ]
        beat_dir = _write_draft(tmp_path, body_md, sources)

        commands.qa_cmd(
            beat="science_tech",
            date="2026-01-15",
            out_dir=tmp_path,
            config_dir=_CONFIG_EXAMPLE,
        )

        report_path = beat_dir / "report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text())

        assert report["passed"] is False

        error_findings = [f for f in report["findings"] if f["severity"] == "error"]
        assert any(
            f["check_name"] == "voice_drift" and "Revolutionary" in f["message"]
            for f in error_findings
        )
        assert any(
            f["check_name"] == "citation_integrity" and "src:9" in f["message"]
            for f in error_findings
        )

    def test_clean_draft_passes_qa(self, tmp_path):
        body_md = (
            "The lab reported a 12% gain in throughput [src:1].\n\n"
            "Researchers plan additional trials before publishing final "
            "results, and they expect the review to take several weeks "
            "[src:2].\n\n"
            "The team said the equipment cost about $200,000 to build and "
            "the tests will continue for a few more months before "
            "submission [src:3]."
        )
        sources = [
            "https://example.com/source-one",
            "https://example.com/source-two",
            "https://example.com/source-three",
        ]
        beat_dir = _write_draft(tmp_path, body_md, sources)

        commands.qa_cmd(
            beat="science_tech",
            date="2026-01-15",
            out_dir=tmp_path,
            config_dir=_CONFIG_EXAMPLE,
        )

        report_path = beat_dir / "report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text())

        assert report["passed"] is True

    def test_missing_draft_raises_clear_error(self, tmp_path):
        with pytest.raises(ValueError, match="draft.json not found"):
            commands.qa_cmd(
                beat="science_tech",
                date="2026-01-15",
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
            )

    def test_draft_beat_mismatch_raises_clear_error(self, tmp_path):
        body_md = "The lab reported a 12% gain in throughput [src:1]."
        sources = ["https://example.com/source-one"]
        beat_dir = tmp_path / "2026-01-15" / "other_beat"
        beat_dir.mkdir(parents=True, exist_ok=True)
        draft = Draft(
            beat="science_tech",
            date="2026-01-15",
            pitch_id="test-pitch-1",
            title="Test Draft",
            body_md=body_md,
            word_count=len(body_md.split()),
            sources=sources,
            guidance_used="Keep it sharp and cite every claim.",
            model_id="fake-model-v1",
            generated_at=_FIXED_GENERATED_AT,
            token_usage=None,
        )
        (beat_dir / "draft.json").write_text(render_draft_json(draft))

        with pytest.raises(ValueError, match="does not match requested --beat"):
            commands.qa_cmd(
                beat="other_beat",
                date="2026-01-15",
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
            )

    def test_draft_date_mismatch_raises_clear_error(self, tmp_path):
        # draft.json lives under out_dir/2026-01-15/science_tech/ (matching
        # the requested --date via the directory layout) but the draft's own
        # `date` field is a different day, which qa_cmd must still catch.
        body_md = "The lab reported a 12% gain in throughput [src:1]."
        sources = ["https://example.com/source-one"]
        beat_dir = tmp_path / "2026-01-15" / "science_tech"
        beat_dir.mkdir(parents=True, exist_ok=True)
        draft = Draft(
            beat="science_tech",
            date="2026-01-16",
            pitch_id="test-pitch-1",
            title="Test Draft",
            body_md=body_md,
            word_count=len(body_md.split()),
            sources=sources,
            guidance_used="Keep it sharp and cite every claim.",
            model_id="fake-model-v1",
            generated_at=_FIXED_GENERATED_AT,
            token_usage=None,
        )
        (beat_dir / "draft.json").write_text(render_draft_json(draft))

        with pytest.raises(ValueError, match="does not match requested --date"):
            commands.qa_cmd(
                beat="science_tech",
                date="2026-01-15",
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
            )
