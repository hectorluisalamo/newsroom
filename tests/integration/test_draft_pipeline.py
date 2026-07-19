# ABOUTME: Integration tests for the draft pipeline.
# ABOUTME: Validates pitch through draft using a fake, network-free LLM provider.
"""Integration tests for the draft pipeline (pitch → draft)."""

import json
from pathlib import Path

import pytest

from conftest import FakeLLMProvider
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


def _write_guidance(tmp_path: Path) -> Path:
    guidance_file = tmp_path / "guidance.md"
    guidance_file.write_text("Keep it sharp and cite every claim.")
    return guidance_file


class TestDraftPipeline:
    """End-to-end: pitch -> draft, using a fake LLM provider (no network, no spend)."""

    def test_writes_draft_files_with_expected_content(self, tmp_path):
        beat_dir = _run_pitch_cmd(tmp_path)
        pitches = json.loads((beat_dir / "pitches.json").read_text())
        pitch_id = pitches["pitches"][0]["pitch_id"]
        guidance_file = _write_guidance(tmp_path)

        commands.draft_cmd(
            beat="science_tech",
            date="2026-01-15",
            pitch_id=pitch_id,
            guidance_file=guidance_file,
            now=_FIXED_NOW,
            out_dir=tmp_path,
            config_dir=_CONFIG_EXAMPLE,
            provider=FakeLLMProvider(word_count=700),
        )

        assert (beat_dir / "draft.json").exists()
        assert (beat_dir / "draft.md").exists()

        draft = json.loads((beat_dir / "draft.json").read_text())
        assert draft["word_count"] > 0
        assert len(draft["sources"]) > 0
        assert draft["model_id"] == "fake-model-v1"
        assert draft["pitch_id"] == pitch_id
        assert "[src:" in draft["body_md"]

        draft_md = (beat_dir / "draft.md").read_text()
        assert "## Sources" in draft_md

    def test_unknown_pitch_id_raises(self, tmp_path):
        beat_dir = _run_pitch_cmd(tmp_path)
        assert beat_dir.exists()
        guidance_file = _write_guidance(tmp_path)

        with pytest.raises(ValueError, match="pitch_id"):
            commands.draft_cmd(
                beat="science_tech",
                date="2026-01-15",
                pitch_id="does-not-exist",
                guidance_file=guidance_file,
                now=_FIXED_NOW,
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
                provider=FakeLLMProvider(word_count=700),
            )

    def test_non_iso_date_raises_and_does_not_escape_out_dir(self, tmp_path):
        # `date` is caller-controlled; a path-traversal payload must be
        # rejected by strict ISO parsing before it's ever joined into a path.
        escaped_root = tmp_path.parent / "evil"
        assert not escaped_root.exists()

        beat_dir = _run_pitch_cmd(tmp_path)
        assert beat_dir.exists()
        guidance_file = _write_guidance(tmp_path)

        with pytest.raises(ValueError, match="invalid --date"):
            commands.draft_cmd(
                beat="science_tech",
                date="../evil",
                pitch_id="does-not-matter",
                guidance_file=guidance_file,
                now=_FIXED_NOW,
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
                provider=FakeLLMProvider(word_count=700),
            )

        # Belt-and-suspenders: validation must fail before any escaped path
        # is created outside out_dir.
        assert not escaped_root.exists()

    def test_date_mismatch_against_pitch_set_only_raises(self, tmp_path):
        # pitches.json for 2026-01-15 lives under out_dir/2026-01-15/<beat>/.
        # Pointing draft_cmd at a *different* but still well-formed ISO date
        # that happens to resolve to the same directory tree (via a manually
        # relocated pitches.json) must be rejected rather than silently
        # drafted against a mismatched pitch set. brief.json is patched to
        # match the requested --date so the brief guard cannot also fire —
        # isolating the pitch_set guard from its sibling.
        beat_dir = _run_pitch_cmd(tmp_path)
        pitches = json.loads((beat_dir / "pitches.json").read_text())
        pitch_id = pitches["pitches"][0]["pitch_id"]
        guidance_file = _write_guidance(tmp_path)

        mismatched_dir = tmp_path / "2026-01-16" / "science_tech"
        mismatched_dir.mkdir(parents=True)
        (mismatched_dir / "pitches.json").write_text(
            (beat_dir / "pitches.json").read_text()
        )
        brief = json.loads((beat_dir / "brief.json").read_text())
        brief["date"] = "2026-01-16"
        (mismatched_dir / "brief.json").write_text(json.dumps(brief))

        with pytest.raises(ValueError, match="pitch_set date .* does not match"):
            commands.draft_cmd(
                beat="science_tech",
                date="2026-01-16",
                pitch_id=pitch_id,
                guidance_file=guidance_file,
                now=_FIXED_NOW,
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
                provider=FakeLLMProvider(word_count=700),
            )

    def test_date_mismatch_against_brief_only_raises(self, tmp_path):
        # Mirror of the pitch_set-only case above, but with the mismatch
        # confined to brief.json: pitches.json is patched to match the
        # requested --date so the pitch_set guard cannot also fire —
        # isolating the brief guard from its sibling.
        beat_dir = _run_pitch_cmd(tmp_path)
        pitches = json.loads((beat_dir / "pitches.json").read_text())
        pitch_id = pitches["pitches"][0]["pitch_id"]
        guidance_file = _write_guidance(tmp_path)

        mismatched_dir = tmp_path / "2026-01-16" / "science_tech"
        mismatched_dir.mkdir(parents=True)
        (mismatched_dir / "brief.json").write_text(
            (beat_dir / "brief.json").read_text()
        )
        pitches["date"] = "2026-01-16"
        (mismatched_dir / "pitches.json").write_text(json.dumps(pitches))

        with pytest.raises(ValueError, match="brief_pack date .* does not match"):
            commands.draft_cmd(
                beat="science_tech",
                date="2026-01-16",
                pitch_id=pitch_id,
                guidance_file=guidance_file,
                now=_FIXED_NOW,
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
                provider=FakeLLMProvider(word_count=700),
            )

    def test_missing_guidance_file_raises_clear_error(self, tmp_path):
        # guidance_file is a caller-controlled CLI flag; a typo'd or missing
        # path must raise a clear ValueError before the bare read_text()
        # would otherwise surface a raw FileNotFoundError.
        beat_dir = _run_pitch_cmd(tmp_path)
        pitches = json.loads((beat_dir / "pitches.json").read_text())
        pitch_id = pitches["pitches"][0]["pitch_id"]
        missing_guidance_file = tmp_path / "does-not-exist.md"

        with pytest.raises(ValueError, match="guidance file"):
            commands.draft_cmd(
                beat="science_tech",
                date="2026-01-15",
                pitch_id=pitch_id,
                guidance_file=missing_guidance_file,
                now=_FIXED_NOW,
                out_dir=tmp_path,
                config_dir=_CONFIG_EXAMPLE,
                provider=FakeLLMProvider(word_count=700),
            )
